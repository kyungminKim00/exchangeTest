"""
OrderBook 테스트
"""

from decimal import Decimal

import pytest

from alt_exchange.core.enums import OrderType, Side, TimeInForce
from alt_exchange.core.models import Order
from alt_exchange.services.matching.orderbook import OrderBookSide, PriceLevel


class TestPriceLevel:
    def test_price_level_creation(self):
        price = Decimal("100.0")
        orders = []
        level = PriceLevel(price=price, orders=orders)

        assert level.price == price
        assert level.orders == orders


class TestOrderBookSide:
    def test_order_book_side_creation(self):
        bids = OrderBookSide(is_buy=True)
        asks = OrderBookSide(is_buy=False)

        assert bids.is_buy is True
        assert asks.is_buy is False

    def test_add_order(self):
        book = OrderBookSide(is_buy=True)
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

        book.add_order(order)

        # Verify order was added
        assert len(book._levels) == 1
        assert Decimal("100.0") in book._levels
        assert len(book._levels[Decimal("100.0")].orders) == 1

    def test_best_price_buy_side(self):
        book = OrderBookSide(is_buy=True)

        # Add orders with different prices
        order1 = Order(
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
        order2 = Order(
            id=2,
            user_id=1,
            account_id=1,
            market="ALT/USDT",
            side=Side.BUY,
            type=OrderType.LIMIT,
            time_in_force=TimeInForce.GTC,
            price=Decimal("110.0"),
            amount=Decimal("10.0"),
        )

        book.add_order(order1)
        book.add_order(order2)

        # For buy side, best price should be highest
        assert book.best_price() == Decimal("110.0")

    def test_best_price_sell_side(self):
        book = OrderBookSide(is_buy=False)

        # Add orders with different prices
        order1 = Order(
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
        order2 = Order(
            id=2,
            user_id=1,
            account_id=1,
            market="ALT/USDT",
            side=Side.SELL,
            type=OrderType.LIMIT,
            time_in_force=TimeInForce.GTC,
            price=Decimal("110.0"),
            amount=Decimal("10.0"),
        )

        book.add_order(order1)
        book.add_order(order2)

        # For sell side, best price should be lowest
        assert book.best_price() == Decimal("100.0")

    def test_pop_best_order(self):
        book = OrderBookSide(is_buy=True)
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

        book.add_order(order)

        # Pop best order
        popped_order = book.pop_best_order()
        assert popped_order == order

        # Verify order was removed
        assert book.best_price() is None

    def test_peek_best_order(self):
        book = OrderBookSide(is_buy=True)
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

        book.add_order(order)

        # Peek best order (should not remove it)
        peeked_order = book.peek_best_order()
        assert peeked_order == order

        # Verify order is still there
        assert book.best_price() == Decimal("100.0")

    def test_remove_order(self):
        book = OrderBookSide(is_buy=True)
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

        book.add_order(order)

        # Remove order
        result = book.remove_order(order)
        assert result is True

        # Verify order was removed
        assert book.best_price() is None

    def test_summary(self):
        book = OrderBookSide(is_buy=True)

        # Add multiple orders at same price level
        order1 = Order(
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
        order2 = Order(
            id=2,
            user_id=1,
            account_id=1,
            market="ALT/USDT",
            side=Side.BUY,
            type=OrderType.LIMIT,
            time_in_force=TimeInForce.GTC,
            price=Decimal("100.0"),
            amount=Decimal("5.0"),
        )

        book.add_order(order1)
        book.add_order(order2)

        # Get summary
        summary = list(book.summary())
        assert len(summary) == 1
        assert summary[0] == (
            Decimal("100.0"),
            Decimal("15.0"),
        )  # Total amount at price level
