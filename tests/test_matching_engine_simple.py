"""
Simple tests for MatchingEngine to improve coverage
"""

from decimal import Decimal
from unittest.mock import AsyncMock, Mock

import pytest

from alt_exchange.core.enums import (Asset, OrderStatus, OrderType, Side,
                                     TimeInForce)
from alt_exchange.core.models import Order
from alt_exchange.services.matching.engine import MatchingEngine


class TestMatchingEngineSimple:
    """Simple tests for MatchingEngine"""

    @pytest.fixture
    def mock_event_bus(self):
        """Create mock event bus"""
        return AsyncMock()

    @pytest.fixture
    def mock_db(self):
        """Create mock database"""
        return Mock()

    @pytest.fixture
    def matching_engine(self, mock_db, mock_event_bus):
        """Create MatchingEngine instance"""
        return MatchingEngine(db=mock_db, market="ALT/USDT", event_bus=mock_event_bus)

    def test_matching_engine_initialization(self, matching_engine):
        """Test MatchingEngine initialization"""
        assert matching_engine.market == "ALT/USDT"
        assert hasattr(matching_engine, "bids")
        assert hasattr(matching_engine, "asks")
        assert hasattr(matching_engine, "event_bus")

    def test_matching_engine_attributes(self, matching_engine):
        """Test MatchingEngine attributes"""
        assert hasattr(matching_engine, "market")
        assert hasattr(matching_engine, "bids")
        assert hasattr(matching_engine, "asks")
        assert hasattr(matching_engine, "event_bus")

    def test_matching_engine_methods(self, matching_engine):
        """Test MatchingEngine methods exist"""
        assert hasattr(matching_engine, "submit")
        assert hasattr(matching_engine, "cancel_order")

    def test_cancel_order_not_found(self, matching_engine):
        """Test cancel_order when order not found"""
        result = matching_engine.cancel_order(999)
        assert result is False

    def test_submit_zero_amount(self, matching_engine):
        """Test submit with zero amount"""
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

    def test_submit_negative_amount(self, matching_engine):
        """Test submit with negative amount"""
        order = Order(
            id=1,
            user_id=1,
            account_id=1,
            market="ALT/USDT",
            side=Side.BUY,
            type=OrderType.LIMIT,
            time_in_force=TimeInForce.GTC,
            price=Decimal("100.0"),
            amount=Decimal("-10.0"),
            filled=Decimal("0.0"),
            status=OrderStatus.OPEN,
        )

        result = matching_engine.submit(order)
        assert result == []

    def test_submit_zero_price(self, matching_engine):
        """Test submit with zero price"""
        order = Order(
            id=1,
            user_id=1,
            account_id=1,
            market="ALT/USDT",
            side=Side.BUY,
            type=OrderType.LIMIT,
            time_in_force=TimeInForce.GTC,
            price=Decimal("0.0"),
            amount=Decimal("10.0"),
            filled=Decimal("0.0"),
            status=OrderStatus.OPEN,
        )

        result = matching_engine.submit(order)
        assert result == []

    def test_submit_negative_price(self, matching_engine):
        """Test submit with negative price"""
        order = Order(
            id=1,
            user_id=1,
            account_id=1,
            market="ALT/USDT",
            side=Side.BUY,
            type=OrderType.LIMIT,
            time_in_force=TimeInForce.GTC,
            price=Decimal("-100.0"),
            amount=Decimal("10.0"),
            filled=Decimal("0.0"),
            status=OrderStatus.OPEN,
        )

        result = matching_engine.submit(order)
        assert result == []
