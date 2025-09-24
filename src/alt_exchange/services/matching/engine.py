from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Tuple

from alt_exchange.core.enums import OrderStatus, OrderType, Side, TimeInForce
from alt_exchange.core.events import OrderAccepted, OrderStatusChanged, TradeExecuted
from alt_exchange.core.exceptions import InvalidOrderError
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

    def submit(self, order: Order) -> List[Trade]:
        if order.type is not OrderType.LIMIT:
            raise InvalidOrderError("Only limit orders are supported in this prototype")

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
            else:
                best_order.status = OrderStatus.PARTIAL

            # Update incoming order
            order.filled += trade_amount
            order.updated_at = now
            remaining = order.remaining()

            if remaining <= 0:
                order.status = OrderStatus.FILLED
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

    def order_book_snapshot(
        self,
    ) -> Tuple[list[tuple[Decimal, Decimal]], list[tuple[Decimal, Decimal]]]:
        bids = list(self.bids.summary())
        asks = list(self.asks.summary())
        return bids, asks
