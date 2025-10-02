"""Simple tests for api/websocket.py to improve coverage."""

import json
from unittest.mock import AsyncMock, Mock, patch

import pytest

from alt_exchange.api.websocket import WebSocketManager


class TestWebSocketSimple:
    """Simple test class for websocket.py."""

    @pytest.fixture
    def websocket_manager(self):
        """WebSocketManager instance."""
        return WebSocketManager()

    @pytest.fixture
    def mock_websocket(self):
        """Mock WebSocket."""
        websocket = AsyncMock()
        websocket.send = AsyncMock()
        websocket.recv = AsyncMock()
        websocket.close = AsyncMock()
        return websocket

    def test_websocket_manager_init(self, websocket_manager):
        """Test WebSocketManager initialization."""
        assert websocket_manager.connections == set()
        assert websocket_manager.user_connections == {}
        assert websocket_manager.market_subscriptions == {}
        assert websocket_manager.context is not None
        assert websocket_manager.event_bus is not None

    @pytest.mark.asyncio
    async def test_register_connection(self, websocket_manager, mock_websocket):
        """Test register connection."""
        await websocket_manager.register(mock_websocket)

        assert mock_websocket in websocket_manager.connections
        assert len(websocket_manager.connections) == 1

    @pytest.mark.asyncio
    async def test_unregister_connection(self, websocket_manager, mock_websocket):
        """Test unregister connection."""
        await websocket_manager.register(mock_websocket)
        await websocket_manager.unregister(mock_websocket)

        assert mock_websocket not in websocket_manager.connections
        assert len(websocket_manager.connections) == 0

    @pytest.mark.asyncio
    async def test_subscribe_to_user(self, websocket_manager, mock_websocket):
        """Test subscribe to user."""
        await websocket_manager.subscribe_to_user(mock_websocket, 1)

        assert 1 in websocket_manager.user_connections
        assert mock_websocket in websocket_manager.user_connections[1]

    @pytest.mark.asyncio
    async def test_subscribe_to_market(self, websocket_manager, mock_websocket):
        """Test subscribe to market."""
        with patch.object(websocket_manager, "send_orderbook_snapshot") as mock_send:
            await websocket_manager.subscribe_to_market(mock_websocket, "ALT/USDT")

        assert "ALT/USDT" in websocket_manager.market_subscriptions
        assert mock_websocket in websocket_manager.market_subscriptions["ALT/USDT"]
        mock_send.assert_called_once_with(mock_websocket, "ALT/USDT")

    @pytest.mark.asyncio
    async def test_send_orderbook_snapshot(self, websocket_manager, mock_websocket):
        """Test send orderbook snapshot."""
        with patch.object(
            websocket_manager.context["market_data"], "order_book_snapshot"
        ) as mock_snapshot:
            mock_snapshot.return_value = ([], [])  # Empty bids and asks

            await websocket_manager.send_orderbook_snapshot(mock_websocket, "ALT/USDT")

        mock_websocket.send.assert_called_once()
        call_args = mock_websocket.send.call_args[0][0]
        message = json.loads(call_args)
        assert message["type"] == "orderbook_snapshot"
        assert message["market"] == "ALT/USDT"

    @pytest.mark.asyncio
    async def test_broadcast_orderbook_update(self, websocket_manager, mock_websocket):
        """Test broadcast orderbook update."""
        # First subscribe to market
        await websocket_manager.subscribe_to_market(mock_websocket, "ALT/USDT")

        with patch.object(
            websocket_manager.context["market_data"], "order_book_snapshot"
        ) as mock_snapshot:
            mock_snapshot.return_value = ([], [])  # Empty bids and asks

            await websocket_manager.broadcast_orderbook_update("ALT/USDT")

        # Should be called twice: once for initial snapshot, once for update
        assert mock_websocket.send.call_count == 2
        call_args = mock_websocket.send.call_args[0][0]
        message = json.loads(call_args)
        assert message["type"] == "orderbook_update"
        assert message["market"] == "ALT/USDT"

    @pytest.mark.asyncio
    async def test_broadcast_trade(self, websocket_manager, mock_websocket):
        """Test broadcast trade."""
        # First subscribe to market
        await websocket_manager.subscribe_to_market(mock_websocket, "ALT/USDT")

        # Create a mock Trade object
        from decimal import Decimal

        from alt_exchange.core.enums import Side
        from alt_exchange.core.models import Trade

        trade = Trade(
            id=1,
            buy_order_id=1,
            sell_order_id=2,
            maker_order_id=1,
            taker_order_id=2,
            taker_side=Side.BUY,
            price=Decimal("100.0"),
            amount=Decimal("1.0"),
            fee=Decimal("0.1"),
        )

        await websocket_manager.broadcast_trade(trade)

        # Should be called twice: once for initial snapshot, once for trade
        assert mock_websocket.send.call_count == 2
        call_args = mock_websocket.send.call_args[0][0]
        message = json.loads(call_args)
        assert message["type"] == "trade"
        assert message["market"] == "ALT/USDT"
        assert message["price"] == "100.0"
        assert message["amount"] == "1.0"
        assert message["side"] == "buy"

    @pytest.mark.asyncio
    async def test_unregister_removes_from_subscriptions(
        self, websocket_manager, mock_websocket
    ):
        """Test that unregister removes websocket from all subscriptions."""
        # Subscribe to both user and market
        await websocket_manager.subscribe_to_user(mock_websocket, 1)
        await websocket_manager.subscribe_to_market(mock_websocket, "ALT/USDT")

        # Unregister
        await websocket_manager.unregister(mock_websocket)

        # Should be removed from all subscriptions
        assert mock_websocket not in websocket_manager.connections
        assert 1 not in websocket_manager.user_connections
        assert "ALT/USDT" not in websocket_manager.market_subscriptions

    @pytest.mark.asyncio
    async def test_multiple_connections_same_user(self, websocket_manager):
        """Test multiple connections for same user."""
        websocket1 = AsyncMock()
        websocket2 = AsyncMock()

        await websocket_manager.subscribe_to_user(websocket1, 1)
        await websocket_manager.subscribe_to_user(websocket2, 1)

        assert len(websocket_manager.user_connections[1]) == 2
        assert websocket1 in websocket_manager.user_connections[1]
        assert websocket2 in websocket_manager.user_connections[1]

    @pytest.mark.asyncio
    async def test_multiple_connections_same_market(self, websocket_manager):
        """Test multiple connections for same market."""
        websocket1 = AsyncMock()
        websocket2 = AsyncMock()

        with patch.object(websocket_manager, "send_orderbook_snapshot"):
            await websocket_manager.subscribe_to_market(websocket1, "ALT/USDT")
            await websocket_manager.subscribe_to_market(websocket2, "ALT/USDT")

        assert len(websocket_manager.market_subscriptions["ALT/USDT"]) == 2
        assert websocket1 in websocket_manager.market_subscriptions["ALT/USDT"]
        assert websocket2 in websocket_manager.market_subscriptions["ALT/USDT"]
