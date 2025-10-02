"""
Additional tests for MatchingEngine to improve coverage.
Focuses on uncovered lines and edge cases.
"""

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, Mock, patch

import pytest

from alt_exchange.core.enums import (Asset, OrderStatus, OrderType, Side,
                                     TimeInForce)
from alt_exchange.core.exceptions import InvalidOrderError, OrderLinkError
from alt_exchange.core.models import Order, Trade
from alt_exchange.services.matching.engine import MatchingEngine


class TestMatchingEngineMoreCoverage:
    """Test MatchingEngine methods for better coverage."""

    @pytest.fixture
    def mock_db(self):
        """Mock database."""
        db = Mock()
        db.next_id = Mock(side_effect=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        db.orders = {}
        db.trades = {}
        db.upsert_order = Mock()
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

    def test_submit_market_order_supported(self, matching_engine):
        """Test submit with market order (now supported)."""
        order = Order(
            id=1,
            user_id=1,
            account_id=1,
            market="ALT/USDT",
            side=Side.BUY,
            type=OrderType.MARKET,
            time_in_force=TimeInForce.GTC,
            price=None,
            amount=Decimal("1"),
        )

        # Market orders are now supported, so this should not raise an error
        result = matching_engine.submit(order)
        assert isinstance(result, list)

    def test_submit_oco_order_missing_link_id(self, matching_engine):
        """Test submit OCO order without link_order_id."""
        order = Order(
            id=1,
            user_id=1,
            account_id=1,
            market="ALT/USDT",
            side=Side.BUY,
            type=OrderType.OCO,
            time_in_force=TimeInForce.GTC,
            price=Decimal("100"),
            amount=Decimal("1"),
            stop_price=Decimal("95"),
        )

        with pytest.raises(OrderLinkError, match="OCO order must have a linked order"):
            matching_engine.submit(order)

    def test_submit_oco_order_with_link_id(self, matching_engine, mock_db):
        """Test submit OCO order with link_order_id."""
        order = Order(
            id=1,
            user_id=1,
            account_id=1,
            market="ALT/USDT",
            side=Side.BUY,
            type=OrderType.OCO,
            time_in_force=TimeInForce.GTC,
            price=Decimal("100"),
            amount=Decimal("1"),
            stop_price=Decimal("95"),
            link_order_id=2,
        )

        # Mock the linked order exists
        linked_order = Order(
            id=2,
            user_id=1,
            account_id=1,
            market="ALT/USDT",
            side=Side.BUY,
            type=OrderType.STOP,
            time_in_force=TimeInForce.GTC,
            price=Decimal("95"),
            amount=Decimal("1"),
            stop_price=Decimal("95"),
        )
        mock_db.orders = {2: linked_order}

        result = matching_engine.submit(order)
        assert result == []

    def test_submit_stop_order_triggered(self, matching_engine, mock_db):
        """Test submit stop order that gets triggered."""
        # Create a buy stop order that should trigger
        order = Order(
            id=1,
            user_id=1,
            account_id=1,
            market="ALT/USDT",
            side=Side.BUY,
            type=OrderType.STOP,
            time_in_force=TimeInForce.GTC,
            price=Decimal("100"),
            amount=Decimal("1"),
            stop_price=Decimal("95"),
        )

        # Mock current market price above stop price (should trigger)
        matching_engine._get_market_price = Mock(return_value=Decimal("96"))

        result = matching_engine.submit(order)
        assert result == []

    def test_submit_stop_order_not_triggered(self, matching_engine, mock_db):
        """Test submit stop order that doesn't trigger."""
        # Create a buy stop order that shouldn't trigger
        order = Order(
            id=1,
            user_id=1,
            account_id=1,
            market="ALT/USDT",
            side=Side.BUY,
            type=OrderType.STOP,
            time_in_force=TimeInForce.GTC,
            price=Decimal("100"),
            amount=Decimal("1"),
            stop_price=Decimal("95"),
        )

        # Mock current market price below stop price (shouldn't trigger)
        matching_engine._get_market_price = Mock(return_value=Decimal("90"))

        result = matching_engine.submit(order)
        assert result == []

    def test_submit_stop_order_sell_side_triggered(self, matching_engine, mock_db):
        """Test submit sell stop order that gets triggered."""
        # Create a sell stop order that should trigger
        order = Order(
            id=1,
            user_id=1,
            account_id=1,
            market="ALT/USDT",
            side=Side.SELL,
            type=OrderType.STOP,
            time_in_force=TimeInForce.GTC,
            price=Decimal("100"),
            amount=Decimal("1"),
            stop_price=Decimal("105"),
        )

        # Mock current market price below stop price (should trigger for sell)
        matching_engine._get_market_price = Mock(return_value=Decimal("104"))

        result = matching_engine.submit(order)
        assert result == []

    def test_submit_stop_order_sell_side_not_triggered(self, matching_engine, mock_db):
        """Test submit sell stop order that doesn't trigger."""
        # Create a sell stop order that shouldn't trigger
        order = Order(
            id=1,
            user_id=1,
            account_id=1,
            market="ALT/USDT",
            side=Side.SELL,
            type=OrderType.STOP,
            time_in_force=TimeInForce.GTC,
            price=Decimal("100"),
            amount=Decimal("1"),
            stop_price=Decimal("105"),
        )

        # Mock current market price above stop price (shouldn't trigger for sell)
        matching_engine._get_market_price = Mock(return_value=Decimal("110"))

        result = matching_engine.submit(order)
        assert result == []

    def test_cancel_order_not_found(self, matching_engine, mock_db):
        """Test cancel_order when order not found."""
        mock_db.orders = {}

        result = matching_engine.cancel_order(999)
        assert result is False

    def test_cancel_order_already_cancelled(self, matching_engine, mock_db):
        """Test cancel_order when order already cancelled."""
        order = Order(
            id=1,
            user_id=1,
            account_id=1,
            market="ALT/USDT",
            side=Side.BUY,
            type=OrderType.LIMIT,
            time_in_force=TimeInForce.GTC,
            price=Decimal("100"),
            amount=Decimal("1"),
            status=OrderStatus.CANCELED,
        )
        mock_db.orders = {1: order}

        result = matching_engine.cancel_order(1)
        assert result is False

    def test_cancel_order_already_filled(self, matching_engine, mock_db):
        """Test cancel_order when order already filled."""
        order = Order(
            id=1,
            user_id=1,
            account_id=1,
            market="ALT/USDT",
            side=Side.BUY,
            type=OrderType.LIMIT,
            time_in_force=TimeInForce.GTC,
            price=Decimal("100"),
            amount=Decimal("1"),
            status=OrderStatus.FILLED,
        )
        mock_db.orders = {1: order}

        result = matching_engine.cancel_order(1)
        assert result is False

    def test_cancel_order_success(self, matching_engine, mock_db):
        """Test successful cancel_order."""
        order = Order(
            id=1,
            user_id=1,
            account_id=1,
            market="ALT/USDT",
            side=Side.BUY,
            type=OrderType.LIMIT,
            time_in_force=TimeInForce.GTC,
            price=Decimal("100"),
            amount=Decimal("1"),
            status=OrderStatus.OPEN,
        )
        mock_db.orders = {1: order}

        result = matching_engine.cancel_order(1)
        assert result is True
        assert order.status == OrderStatus.CANCELED

    def test_cancel_order_oco_type(self, matching_engine, mock_db):
        """Test cancel_order for OCO order type."""
        order = Order(
            id=1,
            user_id=1,
            account_id=1,
            market="ALT/USDT",
            side=Side.BUY,
            type=OrderType.OCO,
            time_in_force=TimeInForce.GTC,
            price=Decimal("100"),
            amount=Decimal("1"),
            status=OrderStatus.OPEN,
            link_order_id=2,
        )
        mock_db.orders = {1: order}

        result = matching_engine.cancel_order(1)
        assert result is True
        assert order.status == OrderStatus.CANCELED

    def test_cancel_order_stop_type(self, matching_engine, mock_db):
        """Test cancel_order for STOP order type."""
        order = Order(
            id=1,
            user_id=1,
            account_id=1,
            market="ALT/USDT",
            side=Side.BUY,
            type=OrderType.STOP,
            time_in_force=TimeInForce.GTC,
            price=Decimal("100"),
            amount=Decimal("1"),
            status=OrderStatus.OPEN,
            stop_price=Decimal("95"),
        )
        mock_db.orders = {1: order}

        result = matching_engine.cancel_order(1)
        assert result is True
        assert order.status == OrderStatus.CANCELED
