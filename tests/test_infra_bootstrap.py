"""
Bootstrap 테스트
"""

import os

import pytest

from alt_exchange.infra.bootstrap import (build_application_context,
                                          build_production_context)


class TestBootstrap:
    def test_build_application_context(self):
        context = build_application_context()

        # Verify all required services are present
        assert "db" in context
        assert "event_bus" in context
        assert "matching" in context
        assert "account_service" in context
        assert "wallet_service" in context
        assert "admin_service" in context
        assert "market_data" in context

        # Verify services are properly initialized
        assert context["db"] is not None
        assert context["event_bus"] is not None
        assert context["matching"] is not None
        assert context["account_service"] is not None
        assert context["wallet_service"] is not None
        assert context["admin_service"] is not None
        assert context["market_data"] is not None

    def test_build_application_context_with_custom_market(self):
        context = build_application_context("BTC/USDT")

        # Verify market is set correctly
        assert context["matching"].market == "BTC/USDT"

    def test_build_production_context(self):
        # Skip this test as it requires actual PostgreSQL connection
        pytest.skip("Production context test requires PostgreSQL connection")

    def test_build_production_context_with_custom_market(self):
        # Skip this test as it requires actual PostgreSQL connection
        pytest.skip("Production context test requires PostgreSQL connection")
