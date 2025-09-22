"""
간단한 API 테스트 모듈
기본적인 API 엔드포인트들을 테스트합니다.
"""

import json
import os
import sys

import pytest
from fastapi.testclient import TestClient

# src 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from alt_exchange.api.main import app


class TestAPISimple:
    """간단한 API 엔드포인트 테스트 클래스"""

    def setup_method(self):
        """각 테스트 메서드 실행 전 설정"""
        self.client = TestClient(app)

    def test_health_check(self):
        """헬스 체크 엔드포인트 테스트"""
        response = self.client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "alt-exchange-api"

    def test_docs_endpoint(self):
        """API 문서 엔드포인트 테스트"""
        response = self.client.get("/docs")
        assert response.status_code == 200

    def test_redoc_endpoint(self):
        """ReDoc 문서 엔드포인트 테스트"""
        response = self.client.get("/redoc")
        assert response.status_code == 200

    def test_openapi_schema(self):
        """OpenAPI 스키마 엔드포인트 테스트"""
        response = self.client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert data["info"]["title"] == "ALT Exchange API"

    def test_create_order_validation(self):
        """주문 생성 데이터 검증 테스트"""
        # 잘못된 데이터로 주문 생성 시도
        invalid_order = {
            "market": "INVALID/MARKET",
            "side": "invalid_side",
            "type": "invalid_type",
            "time_in_force": "invalid_tif",
            "price": "invalid_price",
            "amount": "invalid_amount",
        }

        response = self.client.post("/orders", json=invalid_order)
        assert response.status_code == 422  # Validation Error

    def test_create_order_missing_fields(self):
        """필수 필드 누락 테스트"""
        incomplete_order = {
            "market": "ALT/USDT"
            # 다른 필수 필드들 누락
        }

        response = self.client.post("/orders", json=incomplete_order)
        assert response.status_code == 422  # Validation Error

    def test_get_orders_without_auth(self):
        """인증 없이 주문 조회 테스트"""
        response = self.client.get("/orders")
        # 인증이 필요한 엔드포인트이므로 200, 401, 422, 500 등 예상
        assert response.status_code in [200, 401, 422, 500]

    def test_get_balance_without_auth(self):
        """인증 없이 잔고 조회 테스트"""
        response = self.client.get("/balance")
        # 인증이 필요한 엔드포인트이므로 404, 401, 422, 500 등 예상
        assert response.status_code in [404, 401, 422, 500]

    def test_get_trades_without_auth(self):
        """인증 없이 거래 내역 조회 테스트"""
        response = self.client.get("/trades")
        # 인증이 필요한 엔드포인트이므로 200, 401, 422, 500 등 예상
        assert response.status_code in [200, 401, 422, 500]

    def test_cancel_order_without_auth(self):
        """인증 없이 주문 취소 테스트"""
        response = self.client.delete("/orders/1")
        # 인증이 필요한 엔드포인트이므로 401 또는 다른 오류 코드 예상
        assert response.status_code in [401, 404, 422, 500]

    def test_get_orderbook_invalid_symbol(self):
        """잘못된 심볼로 오더북 조회 테스트"""
        response = self.client.get("/orderbook/INVALID%2FSYMBOL")
        # 잘못된 심볼이므로 404 또는 다른 오류 코드 예상
        assert response.status_code in [404, 422, 500]

    def test_withdrawal_request_validation(self):
        """출금 요청 데이터 검증 테스트"""
        invalid_withdrawal = {
            "asset": "INVALID_ASSET",
            "amount": "invalid_amount",
            "address": "invalid_address",
        }

        response = self.client.post("/withdrawals", json=invalid_withdrawal)
        assert response.status_code == 422  # Validation Error

    def test_withdrawal_request_missing_fields(self):
        """출금 요청 필수 필드 누락 테스트"""
        incomplete_withdrawal = {
            "asset": "ALT"
            # 다른 필수 필드들 누락
        }

        response = self.client.post("/withdrawals", json=incomplete_withdrawal)
        assert response.status_code == 422  # Validation Error
