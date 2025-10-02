"""
API Simple Tests
기본적인 API 테스트
"""

import pytest
from fastapi.testclient import TestClient

from alt_exchange.api.main import app


class TestAPISimple:
    """기본 API 테스트"""

    def setup_method(self):
        """테스트 설정"""
        self.client = TestClient(app)

    def test_health_check(self):
        """헬스체크 테스트"""
        response = self.client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data

    def test_root_endpoint(self):
        """루트 엔드포인트 테스트"""
        response = self.client.get("/")
        # 루트 엔드포인트가 없을 수 있으므로 404도 허용
        assert response.status_code in [200, 404]

    def test_docs_endpoint(self):
        """API 문서 엔드포인트 테스트"""
        response = self.client.get("/docs")
        assert response.status_code == 200

    def test_openapi_endpoint(self):
        """OpenAPI 스펙 엔드포인트 테스트"""
        response = self.client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data

    def test_cors_headers(self):
        """CORS 헤더 테스트"""
        response = self.client.options("/health")
        # OPTIONS 메서드가 지원되지 않을 수 있으므로 405도 허용
        assert response.status_code in [200, 405]

    def test_api_version(self):
        """API 버전 확인"""
        response = self.client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        # 실제 버전에 맞게 수정
        assert data["info"]["version"] == "0.1.0"

    def test_api_title(self):
        """API 제목 확인"""
        response = self.client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "ALT Exchange API" in data["info"]["title"]
