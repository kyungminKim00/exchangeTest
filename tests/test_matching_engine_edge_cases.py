"""Edge case tests for matching/engine.py to improve coverage."""

from decimal import Decimal
from unittest.mock import AsyncMock, Mock, patch

import pytest

from alt_exchange.core.enums import (Asset, OrderStatus, OrderType, Side,
                                     TimeInForce)
from alt_exchange.core.models import Order, Trade
from alt_exchange.services.matching.engine import MatchingEngine


class TestMatchingEngineEdgeCases:
    """Edge case tests for MatchingEngine."""

    @pytest.fixture
    def mock_db(self):
        """Mock database."""
        db = Mock()
        db.orders = {}
        db.trades = {}
        db.update_order = Mock()
        db.insert_trade = Mock()
        return db

    @pytest.fixture
    def mock_event_bus(self):
        """Mock event bus."""
        return AsyncMock()

    @pytest.fixture
    def matching_engine(self, mock_db, mock_event_bus):
        """MatchingEngine instance."""
        return MatchingEngine(db=mock_db, event_bus=mock_event_bus, market="ALT/USDT")

    def test_submit_limit_order_with_zero_amount(self, matching_engine):
        """Test submit limit order with zero amount."""
        order = Order(
            id=1,
            user_id=1,
            account_id=1,
            market="ALT/USDT",
            side=Side.BUY,
            type=OrderType.LIMIT,
            time_in_force=TimeInForce.GTC,
            price=Decimal("100.0"),
            amount=Decimal("0.0"),
            filled=Decimal("0.0"),
            status=OrderStatus.OPEN,
        )

        result = matching_engine.submit(order)
        assert result == []

    def test_submit_limit_order_with_negative_amount(self, matching_engine):
        """Test submit limit order with negative amount."""
        order = Order(
            id=1,
            user_id=1,
            account_id=1,
            market="ALT/USDT",
            side=Side.BUY,
            type=OrderType.LIMIT,
            time_in_force=TimeInForce.GTC,
            price=Decimal("100.0"),
            amount=Decimal("-1.0"),
            filled=Decimal("0.0"),
            status=OrderStatus.OPEN,
        )

        result = matching_engine.submit(order)
        assert result == []

    def test_submit_limit_order_with_zero_price(self, matching_engine):
        """Test submit limit order with zero price."""
        order = Order(
            id=1,
            user_id=1,
            account_id=1,
            market="ALT/USDT",
            side=Side.BUY,
            type=OrderType.LIMIT,
            time_in_force=TimeInForce.GTC,
            price=Decimal("0.0"),
            amount=Decimal("1.0"),
            filled=Decimal("0.0"),
            status=OrderStatus.OPEN,
        )

        result = matching_engine.submit(order)
        assert result == []

    def test_submit_limit_order_with_negative_price(self, matching_engine):
        """Test submit limit order with negative price."""
        order = Order(
            id=1,
            user_id=1,
            account_id=1,
            market="ALT/USDT",
            side=Side.BUY,
            type=OrderType.LIMIT,
            time_in_force=TimeInForce.GTC,
            price=Decimal("-100.0"),
            amount=Decimal("1.0"),
            filled=Decimal("0.0"),
            status=OrderStatus.OPEN,
        )

        result = matching_engine.submit(order)
        assert result == []

    def test_submit_stop_order_with_zero_stop_price(self, matching_engine):
        """Test submit stop order with zero stop price."""
        order = Order(
            id=1,
            user_id=1,
            account_id=1,
            market="ALT/USDT",
            side=Side.BUY,
            type=OrderType.STOP,
            time_in_force=TimeInForce.GTC,
            price=Decimal("100.0"),
            amount=Decimal("1.0"),
            filled=Decimal("0.0"),
            status=OrderStatus.OPEN,
            stop_price=Decimal("0.0"),
        )

        result = matching_engine.submit(order)
        assert result == []

    def test_submit_stop_order_with_negative_stop_price(self, matching_engine):
        """Test submit stop order with negative stop price."""
        order = Order(
            id=1,
            user_id=1,
            account_id=1,
            market="ALT/USDT",
            side=Side.BUY,
            type=OrderType.STOP,
            time_in_force=TimeInForce.GTC,
            price=Decimal("100.0"),
            amount=Decimal("1.0"),
            filled=Decimal("0.0"),
            status=OrderStatus.OPEN,
            stop_price=Decimal("-50.0"),
        )

        result = matching_engine.submit(order)
        assert result == []

    def test_submit_oco_order_with_zero_stop_price(self, matching_engine):
        """Test submit OCO order with zero stop price."""
        order = Order(
            id=1,
            user_id=1,
            account_id=1,
            market="ALT/USDT",
            side=Side.BUY,
            type=OrderType.OCO,
            time_in_force=TimeInForce.GTC,
            price=Decimal("100.0"),
            amount=Decimal("1.0"),
            filled=Decimal("0.0"),
            status=OrderStatus.OPEN,
            stop_price=Decimal("0.0"),
            link_order_id=2,
        )

        result = matching_engine.submit(order)
        assert result == []

    def test_submit_oco_order_with_negative_stop_price(self, matching_engine):
        """Test submit OCO order with negative stop price."""
        order = Order(
            id=1,
            user_id=1,
            account_id=1,
            market="ALT/USDT",
            side=Side.BUY,
            type=OrderType.OCO,
            time_in_force=TimeInForce.GTC,
            price=Decimal("100.0"),
            amount=Decimal("1.0"),
            filled=Decimal("0.0"),
            status=OrderStatus.OPEN,
            stop_price=Decimal("-50.0"),
            link_order_id=2,
        )

        result = matching_engine.submit(order)
        assert result == []

    def test_cancel_order_with_nonexistent_order(self, matching_engine):
        """Test cancel order with nonexistent order."""
        result = matching_engine.cancel_order(999)
        assert result is False

    def test_cancel_order_with_already_cancelled_order(self, matching_engine, mock_db):
        """Test cancel order with already cancelled order."""
        order = Order(
            id=1,
            user_id=1,
            account_id=1,
            market="ALT/USDT",
            side=Side.BUY,
            type=OrderType.LIMIT,
            time_in_force=TimeInForce.GTC,
            price=Decimal("100.0"),
            amount=Decimal("1.0"),
            filled=Decimal("0.0"),
            status=OrderStatus.CANCELED,
        )
        mock_db.orders = {1: order}

        result = matching_engine.cancel_order(1)
        assert result is False

    def test_cancel_order_with_already_filled_order(self, matching_engine, mock_db):
        """Test cancel order with already filled order."""
        order = Order(
            id=1,
            user_id=1,
            account_id=1,
            market="ALT/USDT",
            side=Side.BUY,
            type=OrderType.LIMIT,
            time_in_force=TimeInForce.GTC,
            price=Decimal("100.0"),
            amount=Decimal("1.0"),
            filled=Decimal("1.0"),
            status=OrderStatus.FILLED,
        )
        mock_db.orders = {1: order}

        result = matching_engine.cancel_order(1)
        assert result is False

    def test_order_book_snapshot_empty(self, matching_engine):
        """Test order book snapshot when empty."""
        bids, asks = matching_engine.order_book_snapshot()
        assert bids == []
        assert asks == []

    def test_process_stop_orders_empty(self, matching_engine):
        """Test process stop orders when empty."""
        result = matching_engine.process_stop_orders(Decimal("100.0"))
        assert result == []

    def test_process_stop_orders_with_none_price(self, matching_engine):
        """Test process stop orders with None price."""
        result = matching_engine.process_stop_orders(None)
        assert result == []

    def test_process_stop_orders_with_zero_price(self, matching_engine):
        """Test process stop orders with zero price."""
        result = matching_engine.process_stop_orders(Decimal("0.0"))
        assert result == []

    def test_process_stop_orders_with_negative_price(self, matching_engine):
        """Test process stop orders with negative price."""
        result = matching_engine.process_stop_orders(Decimal("-100.0"))
        assert result == []

    def test_price_crossed_buy_order_with_none_resting_price(self, matching_engine):
        """Test price crossed for buy order with None resting price."""
        order = Order(
            id=1,
            user_id=1,
            account_id=1,
            market="ALT/USDT",
            side=Side.BUY,
            type=OrderType.LIMIT,
            time_in_force=TimeInForce.GTC,
            price=Decimal("100.0"),
            amount=Decimal("1.0"),
            filled=Decimal("0.0"),
            status=OrderStatus.OPEN,
        )

        result = matching_engine._price_crossed(order, None)
        assert result is True

    def test_price_crossed_sell_order_with_none_resting_price(self, matching_engine):
        """Test price crossed for sell order with None resting price."""
        order = Order(
            id=1,
            user_id=1,
            account_id=1,
            market="ALT/USDT",
            side=Side.SELL,
            type=OrderType.LIMIT,
            time_in_force=TimeInForce.GTC,
            price=Decimal("100.0"),
            amount=Decimal("1.0"),
            filled=Decimal("0.0"),
            status=OrderStatus.OPEN,
        )

        result = matching_engine._price_crossed(order, None)
        assert result is True

    def test_calculate_fillable_buy_order_empty_orderbook(self, matching_engine):
        """Test calculate fillable for buy order with empty orderbook."""
        order = Order(
            id=1,
            user_id=1,
            account_id=1,
            market="ALT/USDT",
            side=Side.BUY,
            type=OrderType.LIMIT,
            time_in_force=TimeInForce.GTC,
            price=Decimal("100.0"),
            amount=Decimal("1.0"),
            filled=Decimal("0.0"),
            status=OrderStatus.OPEN,
        )

        result = matching_engine._calculate_fillable(order)
        assert result == Decimal("0")

    def test_calculate_fillable_sell_order_empty_orderbook(self, matching_engine):
        """Test calculate fillable for sell order with empty orderbook."""
        order = Order(
            id=1,
            user_id=1,
            account_id=1,
            market="ALT/USDT",
            side=Side.SELL,
            type=OrderType.LIMIT,
            time_in_force=TimeInForce.GTC,
            price=Decimal("100.0"),
            amount=Decimal("1.0"),
            filled=Decimal("0.0"),
            status=OrderStatus.OPEN,
        )

        result = matching_engine._calculate_fillable(order)
        assert result == Decimal("0")

    def test_check_oco_cancellation_with_nonexistent_linked_order(
        self, matching_engine, mock_db
    ):
        """Test check OCO cancellation with nonexistent linked order."""
        matching_engine.oco_pairs = {1: 2}
        mock_db.orders = {}  # No orders in database

        # Should not raise an exception
        matching_engine._check_oco_cancellation(1)

    def test_check_oco_cancellation_with_empty_oco_pairs(self, matching_engine):
        """Test check OCO cancellation with empty OCO pairs."""
        matching_engine.oco_pairs = {}

        # Should not raise an exception
        matching_engine._check_oco_cancellation(1)
