"""
Matching Engine 테스트
"""

from decimal import Decimal

import pytest

from alt_exchange.core.enums import OrderStatus, OrderType, Side, TimeInForce
from alt_exchange.core.models import Order
from alt_exchange.infra.database.in_memory import InMemoryDatabase
from alt_exchange.infra.event_bus import InMemoryEventBus
from alt_exchange.services.matching.engine import MatchingEngine


class TestMatchingEngine:
    def setup_method(self):
        self.db = InMemoryDatabase()
        self.event_bus = InMemoryEventBus()
        self.engine = MatchingEngine("ALT/USDT", self.db, self.event_bus)

    def test_engine_creation(self):
        assert self.engine.market == "ALT/USDT"
        assert self.engine.db == self.db
        assert self.engine.event_bus == self.event_bus
        assert self.engine.bids is not None
        assert self.engine.asks is not None

    def test_submit_limit_order_no_match(self):
        order = Order(
            id=1,
            user_id=1,
            account_id=1,
            market="ALT/USDT",
            side=Side.BUY,
            type=OrderType.LIMIT,
            time_in_force=TimeInForce.GTC,
            price=Decimal("100.0"),
            amount=Decimal("10.0"),
        )

        trades = self.engine.submit(order)

        # No trades should be executed
        assert len(trades) == 0
        assert order.status == OrderStatus.OPEN
        assert order.filled == Decimal("0")

    def test_submit_limit_order_with_match(self):
        # Add a sell order to the book
        sell_order = Order(
            id=1,
            user_id=1,
            account_id=1,
            market="ALT/USDT",
            side=Side.SELL,
            type=OrderType.LIMIT,
            time_in_force=TimeInForce.GTC,
            price=Decimal("100.0"),
            amount=Decimal("10.0"),
        )
        self.engine.asks.add_order(sell_order)
        self.db.insert_order(sell_order)

        # Submit a buy order that should match
        buy_order = Order(
            id=2,
            user_id=2,
            account_id=2,
            market="ALT/USDT",
            side=Side.BUY,
            type=OrderType.LIMIT,
            time_in_force=TimeInForce.GTC,
            price=Decimal("100.0"),
            amount=Decimal("5.0"),
        )
        self.db.insert_order(buy_order)

        trades = self.engine.submit(buy_order)

        # One trade should be executed
        assert len(trades) == 1
        trade = trades[0]
        assert trade.price == Decimal("100.0")
        assert trade.amount == Decimal("5.0")
        assert trade.maker_order_id == 1
        assert trade.taker_order_id == 2

    def test_submit_stop_order(self):
        order = Order(
            id=1,
            user_id=1,
            account_id=1,
            market="ALT/USDT",
            side=Side.BUY,
            type=OrderType.STOP,
            time_in_force=TimeInForce.GTC,
            price=Decimal("100.0"),
            amount=Decimal("10.0"),
            stop_price=Decimal("90.0"),
        )
        self.db.insert_order(order)

        trades = self.engine.submit(order)

        # No trades should be executed immediately
        assert len(trades) == 0
        assert order.status == OrderStatus.OPEN
        assert len(self.engine.stop_orders) == 1

    def test_cancel_order(self):
        order = Order(
            id=1,
            user_id=1,
            account_id=1,
            market="ALT/USDT",
            side=Side.BUY,
            type=OrderType.LIMIT,
            time_in_force=TimeInForce.GTC,
            price=Decimal("100.0"),
            amount=Decimal("10.0"),
        )
        self.db.insert_order(order)
        self.engine.bids.add_order(order)

        result = self.engine.cancel_order(1)

        assert result is True
        assert order.status == OrderStatus.CANCELED

    def test_order_book_snapshot(self):
        # Add some orders to both sides
        buy_order = Order(
            id=1,
            user_id=1,
            account_id=1,
            market="ALT/USDT",
            side=Side.BUY,
            type=OrderType.LIMIT,
            time_in_force=TimeInForce.GTC,
            price=Decimal("100.0"),
            amount=Decimal("10.0"),
        )
        sell_order = Order(
            id=2,
            user_id=2,
            account_id=2,
            market="ALT/USDT",
            side=Side.SELL,
            type=OrderType.LIMIT,
            time_in_force=TimeInForce.GTC,
            price=Decimal("110.0"),
            amount=Decimal("10.0"),
        )

        self.engine.bids.add_order(buy_order)
        self.engine.asks.add_order(sell_order)

        bids, asks = self.engine.order_book_snapshot()

        assert len(bids) == 1
        assert len(asks) == 1
        assert bids[0] == (Decimal("100.0"), Decimal("10.0"))
        assert asks[0] == (Decimal("110.0"), Decimal("10.0"))

    def test_process_stop_orders(self):
        # Add a stop order
        stop_order = Order(
            id=1,
            user_id=1,
            account_id=1,
            market="ALT/USDT",
            side=Side.BUY,
            type=OrderType.STOP,
            time_in_force=TimeInForce.GTC,
            price=Decimal("100.0"),
            amount=Decimal("10.0"),
            stop_price=Decimal("90.0"),
        )
        self.engine.stop_orders.append(stop_order)
        self.db.insert_order(stop_order)

        # Process stop orders with price that should trigger
        trades = self.engine.process_stop_orders(Decimal("95.0"))

        # Stop order should be activated and converted to limit order
        assert stop_order.type == OrderType.LIMIT
        assert stop_order.stop_price is None
