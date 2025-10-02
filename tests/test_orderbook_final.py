"""Tests for orderbook.py to improve coverage to 95%."""

from collections import deque
from decimal import Decimal

import pytest

from alt_exchange.core.enums import OrderStatus, OrderType, Side, TimeInForce
from alt_exchange.core.models import Order
from alt_exchange.services.matching.orderbook import OrderBookSide, PriceLevel


class TestOrderBookFinal:
    """Test class for final coverage of orderbook.py."""

    @pytest.fixture
    def buy_side(self):
        """Buy side order book."""
        return OrderBookSide(is_buy=True)

    @pytest.fixture
    def sell_side(self):
        """Sell side order book."""
        return OrderBookSide(is_buy=False)

    @pytest.fixture
    def sample_order(self):
        """Sample order for testing."""
        return Order(
            id=1,
            user_id=1,
            account_id=1,
            market="ALT/USDT",
            side=Side.BUY,
            type=OrderType.LIMIT,
            time_in_force=TimeInForce.GTC,
            price=Decimal("100.0"),
            amount=Decimal("1.0"),
            status=OrderStatus.OPEN,
        )

    def test_price_level_init(self):
        """Test PriceLevel initialization."""
        price = Decimal("100.0")
        orders = deque()
        level = PriceLevel(price=price, orders=orders)

        assert level.price == price
        assert level.orders == orders

    def test_price_level_with_orders(self):
        """Test PriceLevel with orders."""
        price = Decimal("100.0")
        orders = deque(
            [
                Order(
                    id=1,
                    user_id=1,
                    account_id=1,
                    market="ALT/USDT",
                    side=Side.BUY,
                    type=OrderType.LIMIT,
                    time_in_force=TimeInForce.GTC,
                    price=Decimal("100.0"),
                    amount=Decimal("1.0"),
                    status=OrderStatus.OPEN,
                )
            ]
        )
        level = PriceLevel(price=price, orders=orders)

        assert level.price == price
        assert len(level.orders) == 1

    def test_orderbook_side_init_buy(self):
        """Test OrderBookSide initialization for buy side."""
        side = OrderBookSide(is_buy=True)

        assert side.is_buy is True
        assert side._levels == {}
        assert side._prices == []

    def test_orderbook_side_init_sell(self):
        """Test OrderBookSide initialization for sell side."""
        side = OrderBookSide(is_buy=False)

        assert side.is_buy is False
        assert side._levels == {}
        assert side._prices == []

    def test_add_order_new_price_level(self, buy_side, sample_order):
        """Test adding order to new price level."""
        buy_side.add_order(sample_order)

        assert sample_order.price in buy_side._levels
        assert sample_order.price in buy_side._prices
        assert len(buy_side._levels[sample_order.price].orders) == 1

    def test_add_order_existing_price_level(self, buy_side, sample_order):
        """Test adding order to existing price level."""
        # Add first order
        buy_side.add_order(sample_order)

        # Add second order at same price
        order2 = Order(
            id=2,
            user_id=2,
            account_id=2,
            market="ALT/USDT",
            side=Side.BUY,
            type=OrderType.LIMIT,
            time_in_force=TimeInForce.GTC,
            price=Decimal("100.0"),
            amount=Decimal("2.0"),
            status=OrderStatus.OPEN,
        )
        buy_side.add_order(order2)

        assert len(buy_side._levels[sample_order.price].orders) == 2

    def test_add_order_none_price(self, buy_side):
        """Test adding order with None price."""
        order = Order(
            id=1,
            user_id=1,
            account_id=1,
            market="ALT/USDT",
            side=Side.BUY,
            type=OrderType.LIMIT,
            time_in_force=TimeInForce.GTC,
            price=None,
            amount=Decimal("1.0"),
            status=OrderStatus.OPEN,
        )

        with pytest.raises(
            ValueError, match="Limit price is required for resting orders"
        ):
            buy_side.add_order(order)

    def test_best_price_empty(self, buy_side, sell_side):
        """Test best_price with empty order book."""
        assert buy_side.best_price() is None
        assert sell_side.best_price() is None

    def test_best_price_buy_side(self, buy_side):
        """Test best_price for buy side (highest price)."""
        # Add orders at different prices
        order1 = Order(
            id=1,
            user_id=1,
            account_id=1,
            market="ALT/USDT",
            side=Side.BUY,
            type=OrderType.LIMIT,
            time_in_force=TimeInForce.GTC,
            price=Decimal("100.0"),
            amount=Decimal("1.0"),
            status=OrderStatus.OPEN,
        )
        order2 = Order(
            id=2,
            user_id=2,
            account_id=2,
            market="ALT/USDT",
            side=Side.BUY,
            type=OrderType.LIMIT,
            time_in_force=TimeInForce.GTC,
            price=Decimal("110.0"),
            amount=Decimal("1.0"),
            status=OrderStatus.OPEN,
        )

        buy_side.add_order(order1)
        buy_side.add_order(order2)

        assert buy_side.best_price() == Decimal("110.0")

    def test_best_price_sell_side(self, sell_side):
        """Test best_price for sell side (lowest price)."""
        # Add orders at different prices
        order1 = Order(
            id=1,
            user_id=1,
            account_id=1,
            market="ALT/USDT",
            side=Side.SELL,
            type=OrderType.LIMIT,
            time_in_force=TimeInForce.GTC,
            price=Decimal("110.0"),
            amount=Decimal("1.0"),
            status=OrderStatus.OPEN,
        )
        order2 = Order(
            id=2,
            user_id=2,
            account_id=2,
            market="ALT/USDT",
            side=Side.SELL,
            type=OrderType.LIMIT,
            time_in_force=TimeInForce.GTC,
            price=Decimal("100.0"),
            amount=Decimal("1.0"),
            status=OrderStatus.OPEN,
        )

        sell_side.add_order(order1)
        sell_side.add_order(order2)

        assert sell_side.best_price() == Decimal("100.0")

    def test_iter_price_levels_empty(self, buy_side, sell_side):
        """Test iter_price_levels with empty order book."""
        assert list(buy_side.iter_price_levels()) == []
        assert list(sell_side.iter_price_levels()) == []

    def test_iter_price_levels_buy_side(self, buy_side):
        """Test iter_price_levels for buy side (descending order)."""
        # Add orders at different prices
        order1 = Order(
            id=1,
            user_id=1,
            account_id=1,
            market="ALT/USDT",
            side=Side.BUY,
            type=OrderType.LIMIT,
            time_in_force=TimeInForce.GTC,
            price=Decimal("100.0"),
            amount=Decimal("1.0"),
            status=OrderStatus.OPEN,
        )
        order2 = Order(
            id=2,
            user_id=2,
            account_id=2,
            market="ALT/USDT",
            side=Side.BUY,
            type=OrderType.LIMIT,
            time_in_force=TimeInForce.GTC,
            price=Decimal("110.0"),
            amount=Decimal("1.0"),
            status=OrderStatus.OPEN,
        )

        buy_side.add_order(order1)
        buy_side.add_order(order2)

        levels = list(buy_side.iter_price_levels())
        assert len(levels) == 2
        assert levels[0].price == Decimal("110.0")  # Highest first
        assert levels[1].price == Decimal("100.0")

    def test_iter_price_levels_sell_side(self, sell_side):
        """Test iter_price_levels for sell side (ascending order)."""
        # Add orders at different prices
        order1 = Order(
            id=1,
            user_id=1,
            account_id=1,
            market="ALT/USDT",
            side=Side.SELL,
            type=OrderType.LIMIT,
            time_in_force=TimeInForce.GTC,
            price=Decimal("110.0"),
            amount=Decimal("1.0"),
            status=OrderStatus.OPEN,
        )
        order2 = Order(
            id=2,
            user_id=2,
            account_id=2,
            market="ALT/USDT",
            side=Side.SELL,
            type=OrderType.LIMIT,
            time_in_force=TimeInForce.GTC,
            price=Decimal("100.0"),
            amount=Decimal("1.0"),
            status=OrderStatus.OPEN,
        )

        sell_side.add_order(order1)
        sell_side.add_order(order2)

        levels = list(sell_side.iter_price_levels())
        assert len(levels) == 2
        assert levels[0].price == Decimal("100.0")  # Lowest first
        assert levels[1].price == Decimal("110.0")

    def test_pop_best_order_empty(self, buy_side, sell_side):
        """Test pop_best_order with empty order book."""
        assert buy_side.pop_best_order() is None
        assert sell_side.pop_best_order() is None

    def test_pop_best_order_single_order(self, buy_side, sample_order):
        """Test pop_best_order with single order."""
        buy_side.add_order(sample_order)

        popped_order = buy_side.pop_best_order()
        assert popped_order == sample_order
        assert buy_side.best_price() is None

    def test_pop_best_order_multiple_orders(self, buy_side):
        """Test pop_best_order with multiple orders at same price."""
        order1 = Order(
            id=1,
            user_id=1,
            account_id=1,
            market="ALT/USDT",
            side=Side.BUY,
            type=OrderType.LIMIT,
            time_in_force=TimeInForce.GTC,
            price=Decimal("100.0"),
            amount=Decimal("1.0"),
            status=OrderStatus.OPEN,
        )
        order2 = Order(
            id=2,
            user_id=2,
            account_id=2,
            market="ALT/USDT",
            side=Side.BUY,
            type=OrderType.LIMIT,
            time_in_force=TimeInForce.GTC,
            price=Decimal("100.0"),
            amount=Decimal("2.0"),
            status=OrderStatus.OPEN,
        )

        buy_side.add_order(order1)
        buy_side.add_order(order2)

        popped_order = buy_side.pop_best_order()
        assert popped_order == order1  # First in, first out
        assert buy_side.best_price() == Decimal("100.0")  # Still has order2

        popped_order2 = buy_side.pop_best_order()
        assert popped_order2 == order2
        assert buy_side.best_price() is None

    def test_peek_best_order_empty(self, buy_side, sell_side):
        """Test peek_best_order with empty order book."""
        assert buy_side.peek_best_order() is None
        assert sell_side.peek_best_order() is None

    def test_peek_best_order_single_order(self, buy_side, sample_order):
        """Test peek_best_order with single order."""
        buy_side.add_order(sample_order)

        peeked_order = buy_side.peek_best_order()
        assert peeked_order == sample_order
        assert buy_side.best_price() == Decimal("100.0")  # Order still there

    def test_peek_best_order_multiple_orders(self, buy_side):
        """Test peek_best_order with multiple orders at same price."""
        order1 = Order(
            id=1,
            user_id=1,
            account_id=1,
            market="ALT/USDT",
            side=Side.BUY,
            type=OrderType.LIMIT,
            time_in_force=TimeInForce.GTC,
            price=Decimal("100.0"),
            amount=Decimal("1.0"),
            status=OrderStatus.OPEN,
        )
        order2 = Order(
            id=2,
            user_id=2,
            account_id=2,
            market="ALT/USDT",
            side=Side.BUY,
            type=OrderType.LIMIT,
            time_in_force=TimeInForce.GTC,
            price=Decimal("100.0"),
            amount=Decimal("2.0"),
            status=OrderStatus.OPEN,
        )

        buy_side.add_order(order1)
        buy_side.add_order(order2)

        peeked_order = buy_side.peek_best_order()
        assert peeked_order == order1  # First in, first out
        assert buy_side.best_price() == Decimal("100.0")  # Order still there

    def test_remove_order_existing(self, buy_side, sample_order):
        """Test remove_order with existing order."""
        buy_side.add_order(sample_order)

        result = buy_side.remove_order(sample_order)
        assert result is True
        assert buy_side.best_price() is None

    def test_remove_order_nonexistent(self, buy_side, sample_order):
        """Test remove_order with non-existent order."""
        result = buy_side.remove_order(sample_order)
        assert result is False

    def test_remove_order_none_price(self, buy_side):
        """Test remove_order with None price."""
        order = Order(
            id=1,
            user_id=1,
            account_id=1,
            market="ALT/USDT",
            side=Side.BUY,
            type=OrderType.LIMIT,
            time_in_force=TimeInForce.GTC,
            price=None,
            amount=Decimal("1.0"),
            status=OrderStatus.OPEN,
        )

        result = buy_side.remove_order(order)
        assert result is False

    def test_remove_order_empty_level(self, buy_side, sample_order):
        """Test remove_order that empties a price level."""
        buy_side.add_order(sample_order)

        result = buy_side.remove_order(sample_order)
        assert result is True
        assert sample_order.price not in buy_side._levels
        assert sample_order.price not in buy_side._prices

    def test_remove_order_multiple_orders_same_price(self, buy_side):
        """Test remove_order with multiple orders at same price."""
        order1 = Order(
            id=1,
            user_id=1,
            account_id=1,
            market="ALT/USDT",
            side=Side.BUY,
            type=OrderType.LIMIT,
            time_in_force=TimeInForce.GTC,
            price=Decimal("100.0"),
            amount=Decimal("1.0"),
            status=OrderStatus.OPEN,
        )
        order2 = Order(
            id=2,
            user_id=2,
            account_id=2,
            market="ALT/USDT",
            side=Side.BUY,
            type=OrderType.LIMIT,
            time_in_force=TimeInForce.GTC,
            price=Decimal("100.0"),
            amount=Decimal("2.0"),
            status=OrderStatus.OPEN,
        )

        buy_side.add_order(order1)
        buy_side.add_order(order2)

        result = buy_side.remove_order(order1)
        assert result is True
        assert buy_side.best_price() == Decimal("100.0")  # Still has order2

        result2 = buy_side.remove_order(order2)
        assert result2 is True
        assert buy_side.best_price() is None
