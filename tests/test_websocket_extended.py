"""
Extended WebSocket tests for comprehensive coverage
"""

import asyncio
import json
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from alt_exchange.api.websocket import (WebSocketManager,
                                        handle_websocket_message,
                                        start_websocket_server,
                                        websocket_handler, ws_manager)
from alt_exchange.core.enums import Asset, Side
from alt_exchange.core.models import Trade


class TestWebSocketManagerExtended:
    """Extended tests for WebSocketManager"""

    @pytest.fixture
    def mock_websocket(self):
        """Mock WebSocket connection"""
        websocket = AsyncMock()
        websocket.send = AsyncMock()
        return websocket

    @pytest.fixture
    def mock_context(self):
        """Mock application context"""
        context = {"event_bus": MagicMock(), "market_data": MagicMock()}
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

    def test_websocket_manager_initialization(self, ws_manager_with_mock_context):
        """Test WebSocketManager initialization"""
        manager = ws_manager_with_mock_context

        assert len(manager.connections) == 0
        assert len(manager.user_connections) == 0
        assert len(manager.market_subscriptions) == 0
        assert manager.context is not None
        assert manager.event_bus is not None

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
        assert len(manager.connections) == 1

        # Unregister
        await manager.unregister(mock_websocket)
        assert len(manager.connections) == 0

    @pytest.mark.asyncio
    async def test_subscribe_to_market(
        self, ws_manager_with_mock_context, mock_websocket
    ):
        """Test subscribing to market data"""
        manager = ws_manager_with_mock_context
        market = "ALT/USDT"

        # Mock the orderbook snapshot method
        manager.context["market_data"].order_book_snapshot.return_value = (
            [(Decimal("100"), Decimal("10"))],  # bids
            [(Decimal("101"), Decimal("5"))],  # asks
        )

        await manager.subscribe_to_market(mock_websocket, market)

        assert market in manager.market_subscriptions
        assert mock_websocket in manager.market_subscriptions[market]
        mock_websocket.send.assert_called_once()

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

    @pytest.mark.asyncio
    async def test_send_orderbook_snapshot_success(
        self, ws_manager_with_mock_context, mock_websocket
    ):
        """Test sending orderbook snapshot successfully"""
        manager = ws_manager_with_mock_context
        market = "ALT/USDT"

        # Mock the orderbook snapshot method
        manager.context["market_data"].order_book_snapshot.return_value = (
            [(Decimal("100"), Decimal("10"))],  # bids
            [(Decimal("101"), Decimal("5"))],  # asks
        )

        await manager.send_orderbook_snapshot(mock_websocket, market)

        mock_websocket.send.assert_called_once()
        sent_message = json.loads(mock_websocket.send.call_args[0][0])
        assert sent_message["type"] == "orderbook_snapshot"
        assert sent_message["market"] == market
        assert "bids" in sent_message
        assert "asks" in sent_message

    @pytest.mark.asyncio
    async def test_send_orderbook_snapshot_error(
        self, ws_manager_with_mock_context, mock_websocket
    ):
        """Test sending orderbook snapshot with error"""
        manager = ws_manager_with_mock_context
        market = "ALT/USDT"

        # Mock the orderbook snapshot method to raise an exception
        manager.context["market_data"].order_book_snapshot.side_effect = Exception(
            "Database error"
        )

        await manager.send_orderbook_snapshot(mock_websocket, market)

        # Should not raise exception, just print error
        mock_websocket.send.assert_not_called()

    @pytest.mark.asyncio
    async def test_broadcast_orderbook_update(
        self, ws_manager_with_mock_context, mock_websocket
    ):
        """Test broadcasting orderbook update"""
        manager = ws_manager_with_mock_context
        market = "ALT/USDT"

        # Subscribe to market first
        await manager.subscribe_to_market(mock_websocket, market)

        # Mock the orderbook snapshot method
        manager.context["market_data"].order_book_snapshot.return_value = (
            [(Decimal("100"), Decimal("10"))],  # bids
            [(Decimal("101"), Decimal("5"))],  # asks
        )

        await manager.broadcast_orderbook_update(market)

        # Should send to subscribed websocket
        assert mock_websocket.send.call_count >= 1

    @pytest.mark.asyncio
    async def test_broadcast_orderbook_update_no_subscribers(
        self, ws_manager_with_mock_context
    ):
        """Test broadcasting orderbook update with no subscribers"""
        manager = ws_manager_with_mock_context
        market = "ALT/USDT"

        # Don't subscribe anyone
        await manager.broadcast_orderbook_update(market)

        # Should not send anything
        assert len(manager.market_subscriptions) == 0

    @pytest.mark.asyncio
    async def test_broadcast_trade(self, ws_manager_with_mock_context, mock_websocket):
        """Test broadcasting trade"""
        manager = ws_manager_with_mock_context
        market = "ALT/USDT"

        # Subscribe to market first
        await manager.subscribe_to_market(mock_websocket, market)

        # Create a trade
        trade = Trade(
            id=1,
            buy_order_id=1,
            sell_order_id=2,
            maker_order_id=1,
            taker_order_id=2,
            taker_side=Side.BUY,
            price=Decimal("100.50"),
            amount=Decimal("5.0"),
            fee=Decimal("0.1"),
            created_at=datetime.now(timezone.utc),
        )

        await manager.broadcast_trade(trade)

        # Should send to subscribed websocket
        assert mock_websocket.send.call_count >= 1

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
            price=Decimal("100.50"),
            amount=Decimal("5.0"),
            fee=Decimal("0.1"),
            created_at=datetime.now(timezone.utc),
        )

        await manager.broadcast_trade(trade)

        # Should not send anything
        assert len(manager.market_subscriptions) == 0

    @pytest.mark.asyncio
    async def test_send_order_update(
        self, ws_manager_with_mock_context, mock_websocket
    ):
        """Test sending order update to user"""
        manager = ws_manager_with_mock_context
        user_id = 123

        # Subscribe user first
        await manager.subscribe_to_user(mock_websocket, user_id)

        order_update = {"order_id": 1, "status": "filled", "filled_amount": "5.0"}

        await manager.send_order_update(user_id, order_update)

        # Should send to user's websocket
        mock_websocket.send.assert_called_once()
        sent_message = json.loads(mock_websocket.send.call_args[0][0])
        assert sent_message["type"] == "order_update"
        assert sent_message["data"] == order_update

    @pytest.mark.asyncio
    async def test_send_order_update_no_user_connections(
        self, ws_manager_with_mock_context
    ):
        """Test sending order update with no user connections"""
        manager = ws_manager_with_mock_context
        user_id = 123

        order_update = {"order_id": 1, "status": "filled", "filled_amount": "5.0"}

        await manager.send_order_update(user_id, order_update)

        # Should not send anything
        assert len(manager.user_connections) == 0

    @pytest.mark.asyncio
    async def test_unregister_cleans_up_user_connections(
        self, ws_manager_with_mock_context, mock_websocket
    ):
        """Test that unregister cleans up user connections"""
        manager = ws_manager_with_mock_context
        user_id = 123

        # Register and subscribe user
        await manager.register(mock_websocket)
        await manager.subscribe_to_user(mock_websocket, user_id)

        assert user_id in manager.user_connections
        assert mock_websocket in manager.user_connections[user_id]

        # Unregister
        await manager.unregister(mock_websocket)

        # User connections should be cleaned up
        assert user_id not in manager.user_connections

    @pytest.mark.asyncio
    async def test_unregister_cleans_up_market_subscriptions(
        self, ws_manager_with_mock_context, mock_websocket
    ):
        """Test that unregister cleans up market subscriptions"""
        manager = ws_manager_with_mock_context
        market = "ALT/USDT"

        # Register and subscribe to market
        await manager.register(mock_websocket)
        await manager.subscribe_to_market(mock_websocket, market)

        assert market in manager.market_subscriptions
        assert mock_websocket in manager.market_subscriptions[market]

        # Unregister
        await manager.unregister(mock_websocket)

        # Market subscriptions should be cleaned up
        assert market not in manager.market_subscriptions


class TestWebSocketHandlerExtended:
    """Extended tests for WebSocket handler functions"""

    @pytest.fixture
    def mock_websocket(self):
        """Mock WebSocket connection"""
        websocket = AsyncMock()
        websocket.send = AsyncMock()
        return websocket

    @pytest.mark.asyncio
    async def test_websocket_handler_success(self, mock_websocket):
        """Test WebSocket handler with successful connection"""
        # Mock the message iteration
        mock_websocket.__aiter__.return_value = [json.dumps({"type": "ping"})]

        with patch("alt_exchange.api.websocket.ws_manager") as mock_manager:
            mock_manager.register = AsyncMock()
            mock_manager.unregister = AsyncMock()

            await websocket_handler(mock_websocket, "/")

            mock_manager.register.assert_called_once_with(mock_websocket)
            mock_manager.unregister.assert_called_once_with(mock_websocket)

    @pytest.mark.asyncio
    async def test_websocket_handler_connection_closed(self, mock_websocket):
        """Test WebSocket handler with connection closed"""
        # Mock connection closed exception
        import websockets.exceptions

        mock_websocket.__aiter__.side_effect = websockets.exceptions.ConnectionClosed(
            None, None
        )

        with patch("alt_exchange.api.websocket.ws_manager") as mock_manager:
            mock_manager.register = AsyncMock()
            mock_manager.unregister = AsyncMock()

            await websocket_handler(mock_websocket, "/")

            mock_manager.register.assert_called_once_with(mock_websocket)
            mock_manager.unregister.assert_called_once_with(mock_websocket)

    @pytest.mark.asyncio
    async def test_handle_websocket_message_subscribe_market(self, mock_websocket):
        """Test handling subscribe_market message"""
        message = {"type": "subscribe_market", "market": "ALT/USDT"}

        with patch("alt_exchange.api.websocket.ws_manager") as mock_manager:
            mock_manager.subscribe_to_market = AsyncMock()

            await handle_websocket_message(mock_websocket, message)

            mock_manager.subscribe_to_market.assert_called_once_with(
                mock_websocket, "ALT/USDT"
            )
            mock_websocket.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_websocket_message_subscribe_user(self, mock_websocket):
        """Test handling subscribe_user message"""
        message = {"type": "subscribe_user", "user_id": 123}

        with patch("alt_exchange.api.websocket.ws_manager") as mock_manager:
            mock_manager.subscribe_to_user = AsyncMock()

            await handle_websocket_message(mock_websocket, message)

            mock_manager.subscribe_to_user.assert_called_once_with(mock_websocket, 123)
            mock_websocket.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_websocket_message_ping(self, mock_websocket):
        """Test handling ping message"""
        message = {"type": "ping"}

        await handle_websocket_message(mock_websocket, message)

        mock_websocket.send.assert_called_once()
        sent_message = json.loads(mock_websocket.send.call_args[0][0])
        assert sent_message["type"] == "pong"

    @pytest.mark.asyncio
    async def test_handle_websocket_message_unknown_type(self, mock_websocket):
        """Test handling unknown message type"""
        message = {"type": "unknown_type"}

        await handle_websocket_message(mock_websocket, message)

        mock_websocket.send.assert_called_once()
        sent_message = json.loads(mock_websocket.send.call_args[0][0])
        assert sent_message["type"] == "error"
        assert "Unknown message type" in sent_message["message"]

    @pytest.mark.asyncio
    async def test_handle_websocket_message_subscribe_user_no_user_id(
        self, mock_websocket
    ):
        """Test handling subscribe_user message without user_id"""
        message = {"type": "subscribe_user"}

        with patch("alt_exchange.api.websocket.ws_manager") as mock_manager:
            mock_manager.subscribe_to_user = AsyncMock()

            await handle_websocket_message(mock_websocket, message)

            # Should not call subscribe_to_user
            mock_manager.subscribe_to_user.assert_not_called()
            # Should not send response
            mock_websocket.send.assert_not_called()


class TestWebSocketServerExtended:
    """Extended tests for WebSocket server"""

    @pytest.mark.asyncio
    async def test_start_websocket_server(self):
        """Test starting WebSocket server"""
        with patch("alt_exchange.api.websocket.websockets.serve") as mock_serve:
            mock_serve.return_value.__aenter__ = AsyncMock()
            mock_serve.return_value.__aexit__ = AsyncMock()

            # Mock the asyncio.Future() to return immediately
            with patch("alt_exchange.api.websocket.asyncio.Future") as mock_future:
                mock_future.return_value = asyncio.Future()
                mock_future.return_value.set_result(None)

                await start_websocket_server("localhost", 8765)

            mock_serve.assert_called_once()
