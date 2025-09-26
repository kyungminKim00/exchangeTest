from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Tuple

from alt_exchange.core.enums import OrderStatus, OrderType, Side, TimeInForce
from alt_exchange.core.events import (OCOOrderCancelled, OrderAccepted,
                                      OrderStatusChanged, StopOrderActivated,
                                      TradeExecuted)
from alt_exchange.core.exceptions import (InvalidOrderError, OrderLinkError,
                                          StopOrderError)
from alt_exchange.core.models import Order, Trade
from alt_exchange.infra.database.base import Database
from alt_exchange.infra.event_bus import InMemoryEventBus

from .orderbook import OrderBookSide

FEE_RATE = Decimal("0.001")


class MatchingEngine:
    """Price-time priority matching engine for a single market."""

    def __init__(self, market: str, db: Database, event_bus: InMemoryEventBus) -> None:
        self.market = market
        self.db = db
        self.event_bus = event_bus
        self.bids = OrderBookSide(is_buy=True)
        self.asks = OrderBookSide(is_buy=False)
        # Stop orders queue - orders waiting for stop price to be triggered
        self.stop_orders: List[Order] = []
        # OCO order pairs - maps order_id to its linked order_id
        self.oco_pairs: dict[int, int] = {}

    def submit(self, order: Order) -> List[Trade]:
        """Submit an order to the matching engine."""
        if order.type == OrderType.STOP:
            return self._submit_stop_order(order)
        elif order.type == OrderType.OCO:
            return self._submit_oco_order(order)
        elif order.type == OrderType.LIMIT:
            return self._submit_limit_order(order)
        else:
            raise InvalidOrderError(f"Order type {order.type} not supported")

    def _submit_limit_order(self, order: Order) -> List[Trade]:
        """Submit a limit order to the matching engine."""
        if order.time_in_force is TimeInForce.FOK:
            potential = self._calculate_fillable(order)
            if potential < order.remaining():
                order.status = OrderStatus.CANCELED
                order.updated_at = datetime.now(timezone.utc)
                self.db.update_order(order)
                self.event_bus.publish(
                    OrderStatusChanged(
                        order_id=order.id,
                        status=order.status,
                        filled=order.filled,
                        remaining=order.remaining(),
                        reason="FOK insufficient liquidity",
                    )
                )
                return []

        trades: List[Trade] = []
        book_to_match = self.asks if order.side is Side.BUY else self.bids
        counter_side = self.bids if order.side is Side.BUY else self.asks

        remaining = order.remaining()
        while remaining > 0:
            best_order = book_to_match.peek_best_order()
            if best_order is None:
                break
            if not self._price_crossed(order, best_order.price):
                break

            trade_amount = min(remaining, best_order.remaining())
            trade_price = best_order.price or order.price
            if trade_price is None:
                raise InvalidOrderError("Unable to determine trade price")

            now = datetime.now(timezone.utc)
            # Update resting order
            best_order.filled += trade_amount
            best_order.updated_at = now
            if best_order.remaining() <= 0:
                best_order.status = OrderStatus.FILLED
                book_to_match.pop_best_order()
                # Check if this was an OCO order and cancel its linked order
                self._check_oco_cancellation(best_order.id)
            else:
                best_order.status = OrderStatus.PARTIAL

            # Update incoming order
            order.filled += trade_amount
            order.updated_at = now
            remaining = order.remaining()

            if remaining <= 0:
                order.status = OrderStatus.FILLED
                # Check if this was an OCO order and cancel its linked order
                self._check_oco_cancellation(order.id)
            else:
                order.status = OrderStatus.PARTIAL

            fee = trade_amount * FEE_RATE
            trade_id = self.db.next_id("trades")
            trade = Trade(
                id=trade_id,
                buy_order_id=order.id if order.side is Side.BUY else best_order.id,
                sell_order_id=best_order.id if order.side is Side.BUY else order.id,
                maker_order_id=best_order.id,
                taker_order_id=order.id,
                taker_side=order.side,
                price=trade_price,
                amount=trade_amount,
                fee=fee,
            )
            self.db.insert_trade(trade)
            trades.append(trade)

            # Persist updated orders
            self.db.update_order(best_order)
            self.db.update_order(order)

            # Emit events for observers
            self.event_bus.publish(
                TradeExecuted(
                    trade_id=trade.id,
                    market=self.market,
                    price=trade.price,
                    amount=trade.amount,
                    maker_order_id=best_order.id,
                    taker_order_id=order.id,
                    taker_side=order.side,
                )
            )
            self.event_bus.publish(
                OrderStatusChanged(
                    order_id=best_order.id,
                    status=best_order.status,
                    filled=best_order.filled,
                    remaining=best_order.remaining(),
                )
            )

        if order.remaining() > 0:
            if order.time_in_force is TimeInForce.GTC:
                order.status = (
                    OrderStatus.OPEN if order.filled == 0 else OrderStatus.PARTIAL
                )
                counter_side.add_order(order)
                self.db.update_order(order)
                self.event_bus.publish(
                    OrderAccepted(
                        order_id=order.id,
                        market=self.market,
                        side=order.side,
                        remaining=order.remaining(),
                    )
                )
                self.event_bus.publish(
                    OrderStatusChanged(
                        order_id=order.id,
                        status=order.status,
                        filled=order.filled,
                        remaining=order.remaining(),
                    )
                )
            elif order.time_in_force is TimeInForce.IOC:
                # Cancel remaining quantity
                order.status = (
                    OrderStatus.CANCELED if order.filled == 0 else OrderStatus.PARTIAL
                )
                order.updated_at = datetime.now(timezone.utc)
                self.db.update_order(order)
                self.event_bus.publish(
                    OrderStatusChanged(
                        order_id=order.id,
                        status=order.status,
                        filled=order.filled,
                        remaining=order.remaining(),
                        reason="IOC remainder canceled",
                    )
                )
        else:
            order.status = OrderStatus.FILLED
            order.updated_at = datetime.now(timezone.utc)
            self.db.update_order(order)
            self.event_bus.publish(
                OrderStatusChanged(
                    order_id=order.id,
                    status=order.status,
                    filled=order.filled,
                    remaining=order.remaining(),
                )
            )

        return trades

    def _submit_stop_order(self, order: Order) -> List[Trade]:
        """Submit a stop order to the stop orders queue."""
        if order.stop_price is None:
            raise StopOrderError("Stop order must have a stop_price")
        if order.price is None:
            raise StopOrderError("Stop order must have a limit price")

        # Add to stop orders queue
        self.stop_orders.append(order)
        order.status = OrderStatus.OPEN
        order.updated_at = datetime.now(timezone.utc)
        self.db.update_order(order)

        self.event_bus.publish(
            OrderStatusChanged(
                order_id=order.id,
                status=order.status,
                filled=order.filled,
                remaining=order.remaining(),
                reason="stop_order_queued",
            )
        )
        return []

    def _submit_oco_order(self, order: Order) -> List[Trade]:
        """Submit an OCO order - creates two linked orders."""
        if order.stop_price is None or order.price is None:
            raise OrderLinkError("OCO order must have both price and stop_price")
        if order.link_order_id is None:
            raise OrderLinkError("OCO order must have a linked order")

        # Create the stop order part
        stop_order = Order(
            id=order.link_order_id,
            user_id=order.user_id,
            account_id=order.account_id,
            market=order.market,
            side=order.side,
            type=OrderType.STOP,
            time_in_force=order.time_in_force,
            price=order.stop_price,  # Stop order uses stop_price as limit price
            amount=order.amount,
            filled=Decimal("0"),
            status=OrderStatus.OPEN,
            stop_price=order.stop_price,
            link_order_id=order.id,
        )

        # Link the orders
        self.oco_pairs[order.id] = stop_order.id
        self.oco_pairs[stop_order.id] = order.id

        # Submit the main limit order
        trades = self._submit_limit_order(order)

        # Submit the stop order
        self._submit_stop_order(stop_order)

        return trades

    def _check_oco_cancellation(self, filled_order_id: int) -> None:
        """Check if a filled order is part of an OCO pair and cancel the linked order."""
        if filled_order_id in self.oco_pairs:
            linked_order_id = self.oco_pairs[filled_order_id]
            linked_order = self.db.orders.get(linked_order_id)

            if linked_order and linked_order.status in {
                OrderStatus.OPEN,
                OrderStatus.PARTIAL,
            }:
                # Cancel the linked order
                linked_order.status = OrderStatus.CANCELED
                linked_order.updated_at = datetime.now(timezone.utc)
                self.db.update_order(linked_order)

                # Remove from stop orders queue if it's a stop order
                if linked_order.type == OrderType.STOP:
                    self.stop_orders = [
                        o for o in self.stop_orders if o.id != linked_order_id
                    ]

                # Remove from OCO pairs
                del self.oco_pairs[filled_order_id]
                if linked_order_id in self.oco_pairs:
                    del self.oco_pairs[linked_order_id]

                self.event_bus.publish(
                    OCOOrderCancelled(
                        order_id=linked_order_id,
                        linked_order_id=filled_order_id,
                        reason="linked_order_filled",
                    )
                )

                self.event_bus.publish(
                    OrderStatusChanged(
                        order_id=linked_order_id,
                        status=linked_order.status,
                        filled=linked_order.filled,
                        remaining=linked_order.remaining(),
                        reason="oco_cancelled",
                    )
                )

    def process_stop_orders(self, market_price: Decimal) -> List[Trade]:
        """Process stop orders when market price changes."""
        activated_orders = []
        remaining_stop_orders = []
        all_trades = []

        for stop_order in self.stop_orders:
            should_activate = False

            if stop_order.side == Side.BUY:
                # Buy stop order activates when price rises above stop_price
                should_activate = market_price >= stop_order.stop_price
            else:
                # Sell stop order activates when price falls below stop_price
                should_activate = market_price <= stop_order.stop_price

            if should_activate:
                # Convert stop order to limit order
                stop_order.type = OrderType.LIMIT
                stop_order.stop_price = None
                activated_orders.append(stop_order)

                self.event_bus.publish(
                    StopOrderActivated(
                        order_id=stop_order.id,
                        market=self.market,
                        stop_price=stop_order.stop_price or Decimal("0"),
                        activated_price=market_price,
                    )
                )

                # Submit as limit order
                trades = self._submit_limit_order(stop_order)
                all_trades.extend(trades)
            else:
                remaining_stop_orders.append(stop_order)

        self.stop_orders = remaining_stop_orders
        return all_trades

    def _calculate_fillable(self, order: Order) -> Decimal:
        to_fill = order.remaining()
        book = self.asks if order.side is Side.BUY else self.bids
        filled = Decimal("0")
        for level in book.iter_price_levels():
            if not self._price_crossed(order, level.price):
                break
            available = sum(o.remaining() for o in level.orders)
            fill = min(to_fill, available)
            filled += fill
            to_fill -= fill
            if to_fill <= 0:
                break
        return filled

    def _price_crossed(self, order: Order, resting_price: Decimal | None) -> bool:
        if resting_price is None:
            return True
        if order.type is OrderType.MARKET or order.price is None:
            return True
        if order.side is Side.BUY:
            return resting_price <= order.price
        return resting_price >= order.price

    def cancel_order(self, order_id: int) -> bool:
        """Cancel an order from the order book or stop orders queue."""
        order = self.db.orders.get(order_id)
        if not order:
            return False

        if order.status not in {OrderStatus.OPEN, OrderStatus.PARTIAL}:
            return False

        # Remove from order book
        if order.side == Side.BUY:
            self.bids.remove_order(order)
        else:
            self.asks.remove_order(order)

        # Remove from stop orders queue
        self.stop_orders = [o for o in self.stop_orders if o.id != order_id]

        # Handle OCO cancellation
        if order_id in self.oco_pairs:
            linked_order_id = self.oco_pairs[order_id]
            linked_order = self.db.orders.get(linked_order_id)

            if linked_order and linked_order.status in {
                OrderStatus.OPEN,
                OrderStatus.PARTIAL,
            }:
                # Cancel the linked order
                linked_order.status = OrderStatus.CANCELED
                linked_order.updated_at = datetime.now(timezone.utc)
                self.db.update_order(linked_order)

                # Remove from stop orders queue if it's a stop order
                if linked_order.type == OrderType.STOP:
                    self.stop_orders = [
                        o for o in self.stop_orders if o.id != linked_order_id
                    ]

                self.event_bus.publish(
                    OCOOrderCancelled(
                        order_id=linked_order_id,
                        linked_order_id=order_id,
                        reason="user_cancelled",
                    )
                )

                self.event_bus.publish(
                    OrderStatusChanged(
                        order_id=linked_order_id,
                        status=linked_order.status,
                        filled=linked_order.filled,
                        remaining=linked_order.remaining(),
                        reason="oco_cancelled",
                    )
                )

            # Remove from OCO pairs
            del self.oco_pairs[order_id]
            if linked_order_id in self.oco_pairs:
                del self.oco_pairs[linked_order_id]

        # Update order status
        order.status = OrderStatus.CANCELED
        order.updated_at = datetime.now(timezone.utc)
        self.db.update_order(order)

        self.event_bus.publish(
            OrderStatusChanged(
                order_id=order.id,
                status=order.status,
                filled=order.filled,
                remaining=order.remaining(),
                reason="user_canceled",
            )
        )

        return True

    def order_book_snapshot(
        self,
    ) -> Tuple[list[tuple[Decimal, Decimal]], list[tuple[Decimal, Decimal]]]:
        bids = list(self.bids.summary())
        asks = list(self.asks.summary())
        return bids, asks
