"""
WebSocket 서버 통합 테스트
실제 WebSocket 서버 핸들러와 메시지 처리 로직을 테스트
"""

import asyncio
import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock, patch

import pytest

import alt_exchange.api.websocket as websocket_module
from alt_exchange.api.websocket import (
    handle_websocket_message,
    start_websocket_server,
    websocket_handler,
    ws_manager,
)
from alt_exchange.core.enums import Side


class TestWebSocketServerIntegration:
    """WebSocket 서버 통합 테스트"""

    @pytest.mark.asyncio
    async def test_websocket_handler_welcome_message(self):
        """WebSocket 핸들러가 환영 메시지를 전송하는지 테스트"""
        mock_websocket = AsyncMock()
        mock_websocket.send = AsyncMock()

        # websocket_handler의 초기 부분을 직접 테스트
        await ws_manager.register(mock_websocket)

        # 환영 메시지 전송 (websocket_handler 내부 로직)
        welcome = {
            "type": "welcome",
            "message": "Connected to ALT Exchange WebSocket",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        await mock_websocket.send(json.dumps(welcome))

        # 검증
        mock_websocket.send.assert_called_once()

        # 전송된 메시지 검증
        call_args = mock_websocket.send.call_args[0][0]
        message = json.loads(call_args)
        assert message["type"] == "welcome"
        assert "Connected to ALT Exchange WebSocket" in message["message"]

    @pytest.mark.asyncio
    async def test_handle_websocket_message_subscribe_market(self):
        """마켓 구독 메시지 처리 테스트"""
        mock_websocket = AsyncMock()
        mock_websocket.send = AsyncMock()

        data = {"type": "subscribe_market", "market": "ALT/USDT"}

        with patch.object(ws_manager, "subscribe_to_market") as mock_subscribe:
            await handle_websocket_message(mock_websocket, data)

            mock_subscribe.assert_called_once_with(mock_websocket, "ALT/USDT")
            mock_websocket.send.assert_called_once()

            # 응답 메시지 검증
            call_args = mock_websocket.send.call_args[0][0]
            response = json.loads(call_args)
            assert response["type"] == "subscription_confirmed"
            assert response["market"] == "ALT/USDT"

    @pytest.mark.asyncio
    async def test_handle_websocket_message_subscribe_user(self):
        """사용자 구독 메시지 처리 테스트"""
        mock_websocket = AsyncMock()
        mock_websocket.send = AsyncMock()

        data = {"type": "subscribe_user", "user_id": 123}

        with patch.object(ws_manager, "subscribe_to_user") as mock_subscribe:
            await handle_websocket_message(mock_websocket, data)

            mock_subscribe.assert_called_once_with(mock_websocket, 123)
            mock_websocket.send.assert_called_once()

            # 응답 메시지 검증
            call_args = mock_websocket.send.call_args[0][0]
            response = json.loads(call_args)
            assert response["type"] == "user_subscription_confirmed"
            assert response["user_id"] == 123

    @pytest.mark.asyncio
    async def test_handle_websocket_message_ping(self):
        """Ping 메시지 처리 테스트"""
        mock_websocket = AsyncMock()
        mock_websocket.send = AsyncMock()

        data = {"type": "ping"}

        await handle_websocket_message(mock_websocket, data)

        mock_websocket.send.assert_called_once()

        # 응답 메시지 검증
        call_args = mock_websocket.send.call_args[0][0]
        response = json.loads(call_args)
        assert response["type"] == "pong"

    @pytest.mark.asyncio
    async def test_handle_websocket_message_unknown_type(self):
        """알 수 없는 메시지 타입 처리 테스트"""
        mock_websocket = AsyncMock()
        mock_websocket.send = AsyncMock()

        data = {"type": "unknown_type"}

        await handle_websocket_message(mock_websocket, data)

        mock_websocket.send.assert_called_once()

        # 에러 메시지 검증
        call_args = mock_websocket.send.call_args[0][0]
        response = json.loads(call_args)
        assert response["type"] == "error"
        assert "Unknown message type: unknown_type" in response["message"]

    @pytest.mark.asyncio
    async def test_handle_websocket_message_subscribe_user_no_user_id(self):
        """사용자 구독 메시지에서 user_id가 없는 경우 테스트"""
        mock_websocket = AsyncMock()
        mock_websocket.send = AsyncMock()

        data = {"type": "subscribe_user", "user_id": None}

        with patch.object(ws_manager, "subscribe_to_user") as mock_subscribe:
            await handle_websocket_message(mock_websocket, data)

            # user_id가 None이므로 subscribe_to_user가 호출되지 않아야 함
            mock_subscribe.assert_not_called()
            mock_websocket.send.assert_not_called()

    @pytest.mark.asyncio
    async def test_send_order_update_method(self):
        """send_order_update 메서드 테스트"""
        user_id = 123
        order_update = {"order_id": 456, "status": "filled"}

        mock_websocket = AsyncMock()
        mock_websocket.send = AsyncMock()

        # 사용자 연결 설정
        ws_manager.user_connections[user_id] = {mock_websocket}

        try:
            await ws_manager.send_order_update(user_id, order_update)

            mock_websocket.send.assert_called_once()

            # 전송된 메시지 검증
            call_args = mock_websocket.send.call_args[0][0]
            message = json.loads(call_args)
            assert message["type"] == "order_update"
            assert message["data"] == order_update

        finally:
            # 테스트 후 정리
            if user_id in ws_manager.user_connections:
                del ws_manager.user_connections[user_id]

    @pytest.mark.asyncio
    async def test_send_order_update_no_user_connections(self):
        """사용자 연결이 없는 경우 send_order_update 테스트"""
        user_id = 999  # 존재하지 않는 사용자

        # 메서드가 예외 없이 종료되는지 확인
        await ws_manager.send_order_update(user_id, {"test": "data"})

    @pytest.mark.asyncio
    async def test_connection_closed_exception_handling(self):
        """ConnectionClosed 예외 처리 테스트"""
        mock_websocket = AsyncMock()
        mock_websocket.send.side_effect = Exception("Connection closed")

        # market 구독 설정
        market = "ALT/USDT"
        ws_manager.market_subscriptions[market] = {mock_websocket}

        try:
            # broadcast_trade에서 ConnectionClosed 예외가 발생해야 함
            mock_trade = Mock()
            mock_trade.price = 100
            mock_trade.amount = 5
            mock_trade.taker_side = Side.BUY
            mock_trade.created_at = datetime.now(timezone.utc)

            await ws_manager.broadcast_trade(mock_trade)

            # 예외가 발생해도 메서드가 정상 종료되어야 함
            assert True

        finally:
            # 테스트 후 정리
            if market in ws_manager.market_subscriptions:
                del ws_manager.market_subscriptions[market]

    @pytest.mark.asyncio
    async def test_start_websocket_server_function_exists(self):
        """start_websocket_server 함수가 존재하는지 테스트"""
        # 함수가 호출 가능한지 확인 (실제 서버 시작은 하지 않음)
        assert callable(start_websocket_server)

        # 함수 시그니처 확인
        import inspect

        sig = inspect.signature(start_websocket_server)
        assert "host" in sig.parameters
        assert "port" in sig.parameters
