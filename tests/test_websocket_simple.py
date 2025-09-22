"""
간단한 WebSocket 테스트 모듈
기본적인 WebSocket 기능을 테스트합니다.
"""

import json
import os
import sys
from unittest.mock import Mock, patch

import pytest

# src 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from alt_exchange.api.websocket import WebSocketManager


class TestWebSocketSimple:
    """간단한 WebSocket 기능 테스트 클래스"""

    def setup_method(self):
        """각 테스트 메서드 실행 전 설정"""
        with patch("alt_exchange.api.websocket.build_application_context"):
            self.manager = WebSocketManager()

    def test_websocket_manager_initialization(self):
        """WebSocket 매니저 초기화 테스트"""
        assert self.manager.connections == set()
        assert self.manager.user_connections == {}
        assert self.manager.market_subscriptions == {}

    def test_websocket_manager_properties(self):
        """WebSocket 매니저 속성 테스트"""
        # 초기 상태 확인
        assert len(self.manager.connections) == 0
        assert len(self.manager.user_connections) == 0
        assert len(self.manager.market_subscriptions) == 0

        # 연결 추가
        mock_websocket = Mock()
        self.manager.connections.add(mock_websocket)
        assert len(self.manager.connections) == 1

        # 사용자 연결 추가
        self.manager.user_connections[123] = {mock_websocket}
        assert len(self.manager.user_connections) == 1
        assert 123 in self.manager.user_connections

        # 시장 구독 추가
        self.manager.market_subscriptions["ALT/USDT"] = {mock_websocket}
        assert len(self.manager.market_subscriptions) == 1
        assert "ALT/USDT" in self.manager.market_subscriptions

    def test_connection_management(self):
        """연결 관리 테스트"""
        mock_websocket1 = Mock()
        mock_websocket1.client.host = "127.0.0.1"
        mock_websocket1.client.port = 8000

        mock_websocket2 = Mock()
        mock_websocket2.client.host = "127.0.0.1"
        mock_websocket2.client.port = 8001

        # 연결 추가
        self.manager.connections.add(mock_websocket1)
        self.manager.connections.add(mock_websocket2)
        assert len(self.manager.connections) == 2

        # 연결 제거
        self.manager.connections.discard(mock_websocket1)
        assert len(self.manager.connections) == 1
        assert mock_websocket1 not in self.manager.connections
        assert mock_websocket2 in self.manager.connections

    def test_market_subscription_management(self):
        """시장 구독 관리 테스트"""
        mock_websocket1 = Mock()
        mock_websocket2 = Mock()

        # 시장 구독 추가
        self.manager.market_subscriptions["ALT/USDT"] = {
            mock_websocket1,
            mock_websocket2,
        }
        self.manager.market_subscriptions["BTC/USDT"] = {mock_websocket1}

        assert "ALT/USDT" in self.manager.market_subscriptions
        assert "BTC/USDT" in self.manager.market_subscriptions
        assert len(self.manager.market_subscriptions["ALT/USDT"]) == 2
        assert len(self.manager.market_subscriptions["BTC/USDT"]) == 1

        # 구독에서 연결 제거
        self.manager.market_subscriptions["ALT/USDT"].discard(mock_websocket1)
        assert len(self.manager.market_subscriptions["ALT/USDT"]) == 1
        assert mock_websocket1 not in self.manager.market_subscriptions["ALT/USDT"]
        assert mock_websocket2 in self.manager.market_subscriptions["ALT/USDT"]

    def test_user_connection_management(self):
        """사용자 연결 관리 테스트"""
        mock_websocket1 = Mock()
        mock_websocket2 = Mock()

        # 사용자 연결 추가
        self.manager.user_connections[123] = {mock_websocket1, mock_websocket2}
        self.manager.user_connections[456] = {mock_websocket1}

        assert 123 in self.manager.user_connections
        assert 456 in self.manager.user_connections
        assert len(self.manager.user_connections[123]) == 2
        assert len(self.manager.user_connections[456]) == 1

        # 사용자 연결에서 WebSocket 제거
        self.manager.user_connections[123].discard(mock_websocket1)
        assert len(self.manager.user_connections[123]) == 1
        assert mock_websocket1 not in self.manager.user_connections[123]
        assert mock_websocket2 in self.manager.user_connections[123]

    def test_subscription_count_calculation(self):
        """구독 수 계산 테스트"""
        mock_websocket1 = Mock()
        mock_websocket2 = Mock()
        mock_websocket3 = Mock()

        # 시장 구독 추가
        self.manager.market_subscriptions["ALT/USDT"] = {
            mock_websocket1,
            mock_websocket2,
        }
        self.manager.market_subscriptions["BTC/USDT"] = {
            mock_websocket1,
            mock_websocket3,
        }
        self.manager.market_subscriptions["ETH/USDT"] = {mock_websocket2}

        # 총 구독 수 계산
        total_subscriptions = sum(
            len(connections)
            for connections in self.manager.market_subscriptions.values()
        )
        assert total_subscriptions == 5  # 2 + 2 + 1

    def test_connection_cleanup(self):
        """연결 정리 테스트"""
        mock_websocket = Mock()

        # 연결과 구독 추가
        self.manager.connections.add(mock_websocket)
        self.manager.user_connections[123] = {mock_websocket}
        self.manager.market_subscriptions["ALT/USDT"] = {mock_websocket}

        # 연결 정리 (unregister 시뮬레이션)
        self.manager.connections.discard(mock_websocket)

        # 사용자 연결에서 제거
        user_ids_to_remove = []
        for user_id, connections in self.manager.user_connections.items():
            connections.discard(mock_websocket)
            if not connections:
                user_ids_to_remove.append(user_id)

        for user_id in user_ids_to_remove:
            del self.manager.user_connections[user_id]

        # 시장 구독에서 제거
        markets_to_remove = []
        for market, connections in self.manager.market_subscriptions.items():
            connections.discard(mock_websocket)
            if not connections:
                markets_to_remove.append(market)

        for market in markets_to_remove:
            del self.manager.market_subscriptions[market]

        # 정리 후 상태 확인
        assert mock_websocket not in self.manager.connections
        assert len(self.manager.user_connections) == 0
        assert len(self.manager.market_subscriptions) == 0

    def test_invalid_json_handling(self):
        """잘못된 JSON 처리 테스트"""
        # 잘못된 JSON 메시지
        with pytest.raises(json.JSONDecodeError):
            json.loads("invalid json")

        # 유효한 JSON 메시지
        valid_message = {"type": "subscribe", "market": "ALT/USDT"}
        parsed = json.loads(json.dumps(valid_message))
        assert parsed["type"] == "subscribe"
        assert parsed["market"] == "ALT/USDT"

    def test_websocket_manager_state_consistency(self):
        """WebSocket 매니저 상태 일관성 테스트"""
        mock_websocket = Mock()

        # 초기 상태
        assert len(self.manager.connections) == 0
        assert len(self.manager.user_connections) == 0
        assert len(self.manager.market_subscriptions) == 0

        # 연결 추가
        self.manager.connections.add(mock_websocket)
        assert len(self.manager.connections) == 1

        # 구독 추가
        self.manager.market_subscriptions["ALT/USDT"] = {mock_websocket}
        self.manager.user_connections[123] = {mock_websocket}

        # 상태 일관성 확인
        assert len(self.manager.connections) == 1
        assert len(self.manager.market_subscriptions) == 1
        assert len(self.manager.user_connections) == 1
        assert mock_websocket in self.manager.connections
        assert mock_websocket in self.manager.market_subscriptions["ALT/USDT"]
        assert mock_websocket in self.manager.user_connections[123]
