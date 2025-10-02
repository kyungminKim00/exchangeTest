"""
Tests for WebSocketManager basic functionality
"""

import asyncio
import json
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from alt_exchange.api.websocket import WebSocketManager
from alt_exchange.core.enums import Side
from alt_exchange.core.models import Trade


class TestWebSocketManager:
    """Tests for WebSocketManager"""

    @pytest.fixture
    def mock_context(self):
        """Mock application context"""
        context = {
            "event_bus": MagicMock(),
            "market_data": MagicMock(),
        }
        return context

    @pytest.fixture
    def ws_manager_with_mock_context(self, mock_context):
        """WebSocketManager with mocked context"""
        with patch(
            "alt_exchange.api.websocket.build_application_context",
            return_value=mock_context,
        ):
            manager = WebSocketManager()
            return manager

    @pytest.fixture
    def mock_websocket(self):
        """Mock WebSocket connection"""
        websocket = AsyncMock()
        websocket.send = AsyncMock()
        websocket.close = AsyncMock()
        websocket.__aiter__ = AsyncMock()
        return websocket

    @pytest.mark.asyncio
    async def test_websocket_manager_initialization(self, ws_manager_with_mock_context):
        """Test WebSocketManager initialization"""
        manager = ws_manager_with_mock_context

        assert manager is not None
        assert hasattr(manager, "connections")
        assert hasattr(manager, "user_connections")
        assert hasattr(manager, "market_subscriptions")
        assert hasattr(manager, "context")
        assert len(manager.connections) == 0
        assert len(manager.user_connections) == 0
        assert len(manager.market_subscriptions) == 0

    @pytest.mark.asyncio
    async def test_register_connection(
        self, ws_manager_with_mock_context, mock_websocket
    ):
        """Test registering a WebSocket connection"""
        manager = ws_manager_with_mock_context

        await manager.register(mock_websocket)

        assert mock_websocket in manager.connections
        assert len(manager.connections) == 1

    @pytest.mark.asyncio
    async def test_unregister_connection(
        self, ws_manager_with_mock_context, mock_websocket
    ):
        """Test unregistering a WebSocket connection"""
        manager = ws_manager_with_mock_context

        # Register first
        await manager.register(mock_websocket)
        assert mock_websocket in manager.connections

        # Unregister
        await manager.unregister(mock_websocket)

        assert mock_websocket not in manager.connections
        assert len(manager.connections) == 0

    @pytest.mark.asyncio
    async def test_subscribe_to_user(
        self, ws_manager_with_mock_context, mock_websocket
    ):
        """Test subscribing to user updates"""
        manager = ws_manager_with_mock_context
        user_id = 123

        await manager.subscribe_to_user(mock_websocket, user_id)

        assert user_id in manager.user_connections
        assert mock_websocket in manager.user_connections[user_id]
        assert len(manager.user_connections[user_id]) == 1

    @pytest.mark.asyncio
    async def test_subscribe_to_market(
        self, ws_manager_with_mock_context, mock_websocket
    ):
        """Test subscribing to market updates"""
        manager = ws_manager_with_mock_context
        market = "ALT/USDT"

        await manager.subscribe_to_market(mock_websocket, market)

        assert market in manager.market_subscriptions
        assert mock_websocket in manager.market_subscriptions[market]
        assert len(manager.market_subscriptions[market]) == 1

    @pytest.mark.asyncio
    async def test_broadcast_trade_success(
        self, ws_manager_with_mock_context, mock_websocket
    ):
        """Test broadcasting trade successfully"""
        manager = ws_manager_with_mock_context
        market = "ALT/USDT"

        # Subscribe to market
        await manager.subscribe_to_market(mock_websocket, market)

        # Create a trade
        trade = Trade(
            id=1,
            buy_order_id=1,
            sell_order_id=2,
            maker_order_id=1,
            taker_order_id=2,
            taker_side=Side.BUY,
            price=Decimal("100.0"),
            amount=Decimal("5.0"),
            fee=Decimal("0.1"),
            created_at=datetime.now(timezone.utc),
        )

        # Broadcast trade
        await manager.broadcast_trade(trade)

        # Verify message was sent
        mock_websocket.send.assert_called_once()
        call_args = mock_websocket.send.call_args[0][0]
        message = json.loads(call_args)
        assert message["type"] == "trade"
        assert message["price"] == "100.0"
        assert message["amount"] == "5.0"

    @pytest.mark.asyncio
    async def test_broadcast_trade_no_subscribers(self, ws_manager_with_mock_context):
        """Test broadcasting trade with no subscribers"""
        manager = ws_manager_with_mock_context

        # Create a trade
        trade = Trade(
            id=1,
            buy_order_id=1,
            sell_order_id=2,
            maker_order_id=1,
            taker_order_id=2,
            taker_side=Side.BUY,
            price=Decimal("100.0"),
            amount=Decimal("5.0"),
            fee=Decimal("0.1"),
            created_at=datetime.now(timezone.utc),
        )

        # Broadcast trade (should not raise exception)
        await manager.broadcast_trade(trade)

        # No assertions needed - just ensure no exception is raised

    @pytest.mark.asyncio
    async def test_broadcast_orderbook_update_success(
        self, ws_manager_with_mock_context, mock_websocket
    ):
        """Test broadcasting orderbook update successfully"""
        manager = ws_manager_with_mock_context
        market = "ALT/USDT"

        # Subscribe to market
        await manager.subscribe_to_market(mock_websocket, market)

        # Mock the orderbook snapshot method
        manager.context["market_data"].order_book_snapshot.return_value = (
            [(Decimal("100"), Decimal("10"))],  # bids
            [(Decimal("101"), Decimal("5"))],  # asks
        )

        # Broadcast orderbook update
        await manager.broadcast_orderbook_update(market)

        # Verify message was sent
        mock_websocket.send.assert_called_once()
        call_args = mock_websocket.send.call_args[0][0]
        message = json.loads(call_args)
        assert message["type"] == "orderbook_update"
        assert message["market"] == market
        assert "bids" in message
        assert "asks" in message

    @pytest.mark.asyncio
    async def test_send_order_update_success(
        self, ws_manager_with_mock_context, mock_websocket
    ):
        """Test sending order update successfully"""
        manager = ws_manager_with_mock_context
        user_id = 123

        # Subscribe to user
        await manager.subscribe_to_user(mock_websocket, user_id)

        order_update = {
            "order_id": 1,
            "status": "filled",
            "filled_amount": "5.0",
        }

        # Send order update
        await manager.send_order_update(user_id, order_update)

        # Verify message was sent
        mock_websocket.send.assert_called_once()
        call_args = mock_websocket.send.call_args[0][0]
        message = json.loads(call_args)
        assert message["type"] == "order_update"
        assert message["data"]["order_id"] == 1
        assert message["data"]["status"] == "filled"

    @pytest.mark.asyncio
    async def test_connection_error_handling(
        self, ws_manager_with_mock_context, mock_websocket
    ):
        """Test handling connection errors during broadcast"""
        manager = ws_manager_with_mock_context
        market = "ALT/USDT"

        # Subscribe to market
        await manager.subscribe_to_market(mock_websocket, market)

        # Mock websocket to raise connection error
        mock_websocket.send.side_effect = Exception("Connection closed")

        # Create a trade
        trade = Trade(
            id=1,
            buy_order_id=1,
            sell_order_id=2,
            maker_order_id=1,
            taker_order_id=2,
            taker_side=Side.BUY,
            price=Decimal("100.0"),
            amount=Decimal("5.0"),
            fee=Decimal("0.1"),
            created_at=datetime.now(timezone.utc),
        )

        # Should not raise exception
        await manager.broadcast_trade(trade)

        # Connection should be cleaned up
        assert market not in manager.market_subscriptions

    @pytest.mark.asyncio
    async def test_websocket_manager_context_usage(self, ws_manager_with_mock_context):
        """Test that WebSocketManager uses context properly"""
        manager = ws_manager_with_mock_context

        # Test that context is available
        assert manager.context is not None
        assert "event_bus" in manager.context
        assert "market_data" in manager.context

    @pytest.mark.asyncio
    async def test_websocket_manager_empty_broadcast(
        self, ws_manager_with_mock_context
    ):
        """Test broadcasting to empty subscription lists"""
        manager = ws_manager_with_mock_context

        # Test broadcasting trade to non-existent market
        trade = Trade(
            id=1,
            buy_order_id=1,
            sell_order_id=2,
            maker_order_id=1,
            taker_order_id=2,
            taker_side=Side.BUY,
            price=Decimal("100.0"),
            amount=Decimal("5.0"),
            fee=Decimal("0.1"),
            created_at=datetime.now(timezone.utc),
        )

        await manager.broadcast_trade(trade)

        # Test broadcasting orderbook to non-existent market
        manager.context["market_data"].order_book_snapshot.return_value = (
            [(Decimal("100"), Decimal("10"))],  # bids
            [(Decimal("101"), Decimal("5"))],  # asks
        )

        await manager.broadcast_orderbook_update("NONEXISTENT")

        # Test sending order update to non-existent user
        order_update = {"order_id": 1, "status": "filled"}
        await manager.send_order_update(999, order_update)

        # Should not raise exceptions
        assert True
