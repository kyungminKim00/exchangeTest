"""
Additional tests for MatchingEngine methods to improve coverage.
Focus on _check_oco_cancellation, _match_limit_order, and other low-coverage methods.
"""

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, Mock, patch

import pytest

from alt_exchange.core.events import OCOOrderCancelled
from alt_exchange.core.exceptions import InvalidOrderError
from alt_exchange.core.models import (Asset, Order, OrderStatus, OrderType,
                                      Side, TimeInForce, Trade)
from alt_exchange.services.matching.engine import MatchingEngine


class TestMatchingEngineAdditionalMethods:
    """Test additional MatchingEngine methods for better coverage."""

    @pytest.fixture
    def mock_db(self):
        """Mock database."""
        db = Mock()
        db.next_id = Mock(side_effect=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        db.orders = {}
        db.trades = {}
        db.update_order = Mock()
        return db

    @pytest.fixture
    def mock_event_bus(self):
        """Mock event bus."""
        return AsyncMock()

    @pytest.fixture
    def matching_engine(self, mock_db, mock_event_bus):
        """MatchingEngine instance with mocked dependencies."""
        return MatchingEngine(db=mock_db, event_bus=mock_event_bus, market="ALT/USDT")

    def test_check_oco_cancellation_with_linked_order(
        self, matching_engine, mock_db, mock_event_bus
    ):
        """Test _check_oco_cancellation when linked order exists and is cancellable."""
        # Setup OCO pair
        filled_order_id = 1
        linked_order_id = 2
        matching_engine.oco_pairs = {filled_order_id: linked_order_id}

        # Setup linked order
        linked_order = Order(
            id=linked_order_id,
            user_id=1,
            account_id=1,
            market="ALT/USDT",
            side=Side.BUY,
            type=OrderType.STOP,
            time_in_force=TimeInForce.GTC,
            price=Decimal("100.0"),
            amount=Decimal("10.0"),
            status=OrderStatus.OPEN,
        )
        mock_db.orders = {linked_order_id: linked_order}

        # Call method
        matching_engine._check_oco_cancellation(filled_order_id)

        # Verify linked order was cancelled
        assert linked_order.status == OrderStatus.CANCELED
        mock_db.update_order.assert_called_with(linked_order)

        # Verify OCO pair was removed
        assert filled_order_id not in matching_engine.oco_pairs
        assert linked_order_id not in matching_engine.oco_pairs

        # Verify events were published (OCOOrderCancelled and OrderStatusChanged)
        assert mock_event_bus.publish.call_count == 2
        # Check first event (OCOOrderCancelled)
        first_event = mock_event_bus.publish.call_args_list[0][0][0]
        assert isinstance(first_event, OCOOrderCancelled)

    def test_check_oco_cancellation_with_partial_linked_order(
        self, matching_engine, mock_db, mock_event_bus
    ):
        """Test _check_oco_cancellation when linked order is partially filled."""
        # Setup OCO pair
        filled_order_id = 1
        linked_order_id = 2
        matching_engine.oco_pairs = {filled_order_id: linked_order_id}

        # Setup partially filled linked order
        linked_order = Order(
            id=linked_order_id,
            user_id=1,
            account_id=1,
            market="ALT/USDT",
            side=Side.BUY,
            type=OrderType.STOP,
            time_in_force=TimeInForce.GTC,
            price=Decimal("100.0"),
            amount=Decimal("10.0"),
            filled=Decimal("3.0"),
            status=OrderStatus.PARTIAL,
        )
        mock_db.orders = {linked_order_id: linked_order}

        # Call method
        matching_engine._check_oco_cancellation(filled_order_id)

        # Verify linked order was cancelled
        assert linked_order.status == OrderStatus.CANCELED
        mock_db.update_order.assert_called_with(linked_order)

    def test_check_oco_cancellation_with_non_cancellable_linked_order(
        self, matching_engine, mock_db, mock_event_bus
    ):
        """Test _check_oco_cancellation when linked order is not cancellable."""
        # Setup OCO pair
        filled_order_id = 1
        linked_order_id = 2
        matching_engine.oco_pairs = {filled_order_id: linked_order_id}

        # Setup non-cancellable linked order (already filled)
        linked_order = Order(
            id=linked_order_id,
            user_id=1,
            account_id=1,
            market="ALT/USDT",
            side=Side.BUY,
            type=OrderType.STOP,
            time_in_force=TimeInForce.GTC,
            price=Decimal("100.0"),
            amount=Decimal("10.0"),
            status=OrderStatus.FILLED,
        )
        mock_db.orders = {linked_order_id: linked_order}

        # Call method
        matching_engine._check_oco_cancellation(filled_order_id)

        # Verify linked order was not modified
        assert linked_order.status == OrderStatus.FILLED
        mock_db.update_order.assert_not_called()

    def test_check_oco_cancellation_with_missing_linked_order(
        self, matching_engine, mock_db, mock_event_bus
    ):
        """Test _check_oco_cancellation when linked order doesn't exist."""
        # Setup OCO pair
        filled_order_id = 1
        linked_order_id = 2
        matching_engine.oco_pairs = {filled_order_id: linked_order_id}

        # No linked order in database
        mock_db.orders = {}

        # Call method
        matching_engine._check_oco_cancellation(filled_order_id)

        # Verify no database operations
        mock_db.update_order.assert_not_called()

    def test_check_oco_cancellation_with_limit_order(
        self, matching_engine, mock_db, mock_event_bus
    ):
        """Test _check_oco_cancellation with limit order (not stop order)."""
        # Setup OCO pair
        filled_order_id = 1
        linked_order_id = 2
        matching_engine.oco_pairs = {filled_order_id: linked_order_id}

        # Setup limit order (not stop order)
        linked_order = Order(
            id=linked_order_id,
            user_id=1,
            account_id=1,
            market="ALT/USDT",
            side=Side.BUY,
            type=OrderType.LIMIT,  # Not STOP
            time_in_force=TimeInForce.GTC,
            price=Decimal("100.0"),
            amount=Decimal("10.0"),
            status=OrderStatus.OPEN,
        )
        mock_db.orders = {linked_order_id: linked_order}

        # Call method
        matching_engine._check_oco_cancellation(filled_order_id)

        # Verify linked order was cancelled
        assert linked_order.status == OrderStatus.CANCELED
        mock_db.update_order.assert_called_with(linked_order)

    def test_check_oco_cancellation_with_stop_order_in_queue(
        self, matching_engine, mock_db, mock_event_bus
    ):
        """Test _check_oco_cancellation with stop order in stop_orders queue."""
        # Setup OCO pair
        filled_order_id = 1
        linked_order_id = 2
        matching_engine.oco_pairs = {filled_order_id: linked_order_id}

        # Setup stop order
        linked_order = Order(
            id=linked_order_id,
            user_id=1,
            account_id=1,
            market="ALT/USDT",
            side=Side.BUY,
            type=OrderType.STOP,
            time_in_force=TimeInForce.GTC,
            price=Decimal("100.0"),
            amount=Decimal("10.0"),
            status=OrderStatus.OPEN,
        )
        mock_db.orders = {linked_order_id: linked_order}

        # Add to stop orders queue
        matching_engine.stop_orders = [linked_order]

        # Call method
        matching_engine._check_oco_cancellation(filled_order_id)

        # Verify stop order was removed from queue
        assert linked_order not in matching_engine.stop_orders

    def test_check_oco_cancellation_bidirectional_oco_pairs(
        self, matching_engine, mock_db, mock_event_bus
    ):
        """Test _check_oco_cancellation with bidirectional OCO pairs."""
        # Setup bidirectional OCO pair
        filled_order_id = 1
        linked_order_id = 2
        matching_engine.oco_pairs = {
            filled_order_id: linked_order_id,
            linked_order_id: filled_order_id,
        }

        # Setup linked order
        linked_order = Order(
            id=linked_order_id,
            user_id=1,
            account_id=1,
            market="ALT/USDT",
            side=Side.BUY,
            type=OrderType.STOP,
            time_in_force=TimeInForce.GTC,
            price=Decimal("100.0"),
            amount=Decimal("10.0"),
            status=OrderStatus.OPEN,
        )
        mock_db.orders = {linked_order_id: linked_order}

        # Call method
        matching_engine._check_oco_cancellation(filled_order_id)

        # Verify both OCO pairs were removed
        assert filled_order_id not in matching_engine.oco_pairs
        assert linked_order_id not in matching_engine.oco_pairs

    def test_calculate_fillable_buy_order(self, matching_engine):
        """Test _calculate_fillable for buy order."""
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
            filled=Decimal("3.0"),
            status=OrderStatus.PARTIAL,
        )

        # _calculate_fillable checks the order book for available liquidity
        # Since the order book is empty, it should return 0
        result = matching_engine._calculate_fillable(order)
        assert result == Decimal("0")

    def test_calculate_fillable_sell_order(self, matching_engine):
        """Test _calculate_fillable for sell order."""
        order = Order(
            id=1,
            user_id=1,
            account_id=1,
            market="ALT/USDT",
            side=Side.SELL,
            type=OrderType.LIMIT,
            time_in_force=TimeInForce.GTC,
            price=Decimal("100.0"),
            amount=Decimal("10.0"),
            filled=Decimal("3.0"),
            status=OrderStatus.PARTIAL,
        )

        # _calculate_fillable checks the order book for available liquidity
        # Since the order book is empty, it should return 0
        result = matching_engine._calculate_fillable(order)
        assert result == Decimal("0")

    def test_price_crossed_buy_order(self, matching_engine):
        """Test _price_crossed for buy order."""
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
            status=OrderStatus.OPEN,
        )

        # Buy order crosses when price >= resting price
        assert matching_engine._price_crossed(order, Decimal("99.0")) is True
        assert matching_engine._price_crossed(order, Decimal("100.0")) is True
        assert matching_engine._price_crossed(order, Decimal("101.0")) is False

    def test_price_crossed_sell_order(self, matching_engine):
        """Test _price_crossed for sell order."""
        order = Order(
            id=1,
            user_id=1,
            account_id=1,
            market="ALT/USDT",
            side=Side.SELL,
            type=OrderType.LIMIT,
            time_in_force=TimeInForce.GTC,
            price=Decimal("100.0"),
            amount=Decimal("10.0"),
            status=OrderStatus.OPEN,
        )

        # Sell order crosses when price <= resting price
        assert matching_engine._price_crossed(order, Decimal("99.0")) is False
        assert matching_engine._price_crossed(order, Decimal("100.0")) is True
        assert matching_engine._price_crossed(order, Decimal("101.0")) is True

    def test_price_crossed_with_none_resting_price(self, matching_engine):
        """Test _price_crossed with None resting price."""
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
            status=OrderStatus.OPEN,
        )

        # Should return True when resting price is None
        assert matching_engine._price_crossed(order, None) is True
