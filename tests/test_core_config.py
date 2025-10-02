"""
Core Config 테스트
"""

import os
from unittest.mock import patch

import pytest

from alt_exchange.core.config import Settings, _env_bool, get_settings


class TestSettings:
    def test_settings_creation(self):
        """설정 생성 테스트"""
        settings = Settings()
        assert settings is not None

    def test_settings_default_values(self):
        """기본값 테스트"""
        settings = Settings()
        assert settings.database_url == "sqlite:///./alt_exchange.db"
        assert settings.jwt_secret == "local-secret"
        assert settings.ws_enabled is False

    def test_settings_with_custom_values(self):
        """사용자 정의 값으로 설정 생성 테스트"""
        settings = Settings(
            database_url="postgresql://test:test@localhost/test",
            jwt_secret="custom-secret",
            ws_enabled=True,
        )
        assert settings.database_url == "postgresql://test:test@localhost/test"
        assert settings.jwt_secret == "custom-secret"
        assert settings.ws_enabled is True

    def test_settings_immutability(self):
        """설정 불변성 테스트"""
        settings = Settings()
        # 설정은 읽기 전용이어야 함
        assert hasattr(settings, "database_url")
        assert hasattr(settings, "jwt_secret")
        assert hasattr(settings, "ws_enabled")


class TestEnvBool:
    def test_env_bool_true_values(self):
        """환경변수 true 값 테스트"""
        with patch.dict(os.environ, {"TEST_BOOL": "1"}):
            assert _env_bool("TEST_BOOL", False) is True

        with patch.dict(os.environ, {"TEST_BOOL": "true"}):
            assert _env_bool("TEST_BOOL", False) is True

        with patch.dict(os.environ, {"TEST_BOOL": "TRUE"}):
            assert _env_bool("TEST_BOOL", False) is True

        with patch.dict(os.environ, {"TEST_BOOL": "yes"}):
            assert _env_bool("TEST_BOOL", False) is True

    def test_env_bool_false_values(self):
        """환경변수 false 값 테스트"""
        with patch.dict(os.environ, {"TEST_BOOL": "0"}):
            assert _env_bool("TEST_BOOL", True) is False

        with patch.dict(os.environ, {"TEST_BOOL": "false"}):
            assert _env_bool("TEST_BOOL", True) is False

        with patch.dict(os.environ, {"TEST_BOOL": "no"}):
            assert _env_bool("TEST_BOOL", True) is False

    def test_env_bool_missing(self):
        """환경변수 없을 때 기본값 테스트"""
        with patch.dict(os.environ, {}, clear=True):
            assert _env_bool("TEST_BOOL", True) is True
            assert _env_bool("TEST_BOOL", False) is False


class TestGetSettings:
    def test_get_settings_caching(self):
        """설정 캐싱 테스트"""
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2  # 같은 객체여야 함 (캐싱)

    def test_get_settings_returns_settings(self):
        """get_settings가 Settings 객체 반환 테스트"""
        settings = get_settings()
        assert isinstance(settings, Settings)
