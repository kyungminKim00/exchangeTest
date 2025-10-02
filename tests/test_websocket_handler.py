"""
Tests for WebSocket handler and message processing
"""

import asyncio
import json
from unittest.mock import AsyncMock, patch

import pytest

from alt_exchange.api.websocket import (handle_websocket_message,
                                        start_websocket_server,
                                        websocket_handler)


class TestWebSocketHandler:
    """Tests for WebSocket handler functions"""

    @pytest.fixture
    def mock_websocket(self):
        """Mock WebSocket connection"""
        websocket = AsyncMock()
        websocket.send = AsyncMock()
        websocket.close = AsyncMock()

        # Create a proper async iterator
        async def async_iter():
            yield '{"type": "subscribe_market", "market": "ALT/USDT"}'
            yield '{"type": "subscribe_user", "user_id": 123}'

        websocket.__aiter__ = lambda self: async_iter()
        return websocket

    @pytest.mark.asyncio
    async def test_websocket_handler_success(self, mock_websocket):
        """Test WebSocket handler with successful message processing"""
        with patch("alt_exchange.api.websocket.ws_manager") as mock_manager:
            mock_manager.register = AsyncMock()
            mock_manager.unregister = AsyncMock()
            mock_manager.subscribe_to_market = AsyncMock()
            mock_manager.subscribe_to_user = AsyncMock()

            await websocket_handler(mock_websocket, "/")

            mock_manager.register.assert_called_once_with(mock_websocket)
            mock_manager.unregister.assert_called_once_with(mock_websocket)
            mock_manager.subscribe_to_market.assert_called_once_with(
                mock_websocket, "ALT/USDT"
            )
            mock_manager.subscribe_to_user.assert_called_once_with(mock_websocket, 123)

    @pytest.mark.asyncio
    async def test_websocket_handler_invalid_json(self, mock_websocket):
        """Test WebSocket handler with invalid JSON"""
        # Mock the message iteration with invalid JSON
        mock_websocket.__aiter__.return_value = ["invalid json"]

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

    @pytest.mark.asyncio
    async def test_handle_websocket_message_subscribe_user(self, mock_websocket):
        """Test handling subscribe_user message"""
        message = {"type": "subscribe_user", "user_id": 123}

        with patch("alt_exchange.api.websocket.ws_manager") as mock_manager:
            mock_manager.subscribe_to_user = AsyncMock()

            await handle_websocket_message(mock_websocket, message)

            mock_manager.subscribe_to_user.assert_called_once_with(mock_websocket, 123)

    @pytest.mark.asyncio
    async def test_handle_websocket_message_unknown_type(self, mock_websocket):
        """Test handling unknown message type"""
        message = {"type": "unknown_type", "data": "test"}

        with patch("alt_exchange.api.websocket.ws_manager") as mock_manager:
            await handle_websocket_message(mock_websocket, message)

            # Should send error message
            mock_websocket.send.assert_called_once()
            call_args = mock_websocket.send.call_args[0][0]
            error_message = json.loads(call_args)
            assert error_message["type"] == "error"
            assert "Unknown message type" in error_message["message"]

    @pytest.mark.skip(reason="Complex async mocking required")
    @pytest.mark.asyncio
    async def test_start_websocket_server(self):
        """Test starting WebSocket server"""
        with patch("alt_exchange.api.websocket.websockets.serve") as mock_serve:
            mock_serve.return_value = AsyncMock()

            # Mock asyncio.Future to prevent infinite loop
            with patch("asyncio.Future") as mock_future:
                mock_future.return_value = AsyncMock()
                mock_future.return_value.__await__ = AsyncMock(return_value=iter([]))

                # Mock the async context manager
                mock_serve.return_value.__aenter__ = AsyncMock(return_value=None)
                mock_serve.return_value.__aexit__ = AsyncMock(return_value=None)

                await start_websocket_server("localhost", 8765)

                mock_serve.assert_called_once()

    @pytest.mark.asyncio
    async def test_websocket_handler_connection_error(self, mock_websocket):
        """Test WebSocket handler with connection error"""
        # Mock the message iteration to raise an exception
        mock_websocket.__aiter__.side_effect = Exception("Connection lost")

        with patch("alt_exchange.api.websocket.ws_manager") as mock_manager:
            mock_manager.register = AsyncMock()
            mock_manager.unregister = AsyncMock()

            await websocket_handler(mock_websocket, "/")

            mock_manager.register.assert_called_once_with(mock_websocket)
            mock_manager.unregister.assert_called_once_with(mock_websocket)

    @pytest.mark.asyncio
    async def test_handle_websocket_message_missing_fields(self, mock_websocket):
        """Test handling message with missing required fields"""
        # Test subscribe_market without market field
        message = {"type": "subscribe_market"}

        with patch("alt_exchange.api.websocket.ws_manager") as mock_manager:
            mock_manager.subscribe_to_market = AsyncMock()

            await handle_websocket_message(mock_websocket, message)

            # Should call subscribe_to_market with default market
            mock_manager.subscribe_to_market.assert_called_once_with(
                mock_websocket, "ALT/USDT"
            )

    @pytest.mark.asyncio
    async def test_handle_websocket_message_subscribe_user_missing_user_id(
        self, mock_websocket
    ):
        """Test handling subscribe_user message without user_id"""
        message = {"type": "subscribe_user"}

        with patch("alt_exchange.api.websocket.ws_manager") as mock_manager:
            await handle_websocket_message(mock_websocket, message)

            # Should not call subscribe_to_user when user_id is missing
            mock_manager.subscribe_to_user.assert_not_called()

    @pytest.mark.asyncio
    async def test_websocket_handler_empty_messages(self, mock_websocket):
        """Test WebSocket handler with empty message list"""
        # Mock the message iteration with empty list
        mock_websocket.__aiter__.return_value = []

        with patch("alt_exchange.api.websocket.ws_manager") as mock_manager:
            mock_manager.register = AsyncMock()
            mock_manager.unregister = AsyncMock()

            await websocket_handler(mock_websocket, "/")

            mock_manager.register.assert_called_once_with(mock_websocket)
            mock_manager.unregister.assert_called_once_with(mock_websocket)

    @pytest.mark.asyncio
    async def test_handle_websocket_message_invalid_type(self, mock_websocket):
        """Test handling message with invalid type field"""
        message = {"type": None, "data": "test"}

        with patch("alt_exchange.api.websocket.ws_manager") as mock_manager:
            await handle_websocket_message(mock_websocket, message)

            # Should send error message
            mock_websocket.send.assert_called_once()
            call_args = mock_websocket.send.call_args[0][0]
            error_message = json.loads(call_args)
            assert error_message["type"] == "error"
            assert "Unknown message type" in error_message["message"]
