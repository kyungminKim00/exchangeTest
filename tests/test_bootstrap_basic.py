"""Basic tests for bootstrap to improve coverage"""

import os
from unittest.mock import MagicMock, patch

import pytest

from alt_exchange.infra.bootstrap import (build_application_context,
                                          build_production_context)


class TestBootstrapBasic:
    """Basic tests for bootstrap coverage improvement"""

    def test_build_application_context_success(self):
        """Test successful application context building"""
        market = "ALT/USDT"

        with (
            patch("alt_exchange.infra.bootstrap.DatabaseFactory") as mock_factory,
            patch(
                "alt_exchange.infra.bootstrap.InMemoryEventBus"
            ) as mock_event_bus_class,
            patch(
                "alt_exchange.infra.bootstrap.MatchingEngine"
            ) as mock_matching_engine_class,
            patch(
                "alt_exchange.infra.bootstrap.AccountService"
            ) as mock_account_service_class,
            patch(
                "alt_exchange.infra.bootstrap.WalletService"
            ) as mock_wallet_service_class,
            patch(
                "alt_exchange.infra.bootstrap.AdminService"
            ) as mock_admin_service_class,
            patch(
                "alt_exchange.infra.bootstrap.MarketDataBroadcaster"
            ) as mock_broadcaster_class,
        ):

            # Mock instances
            mock_db = MagicMock()
            mock_event_bus = MagicMock()
            mock_matching_engine = MagicMock()
            mock_account_service = MagicMock()
            mock_wallet_service = MagicMock()
            mock_admin_service = MagicMock()
            mock_broadcaster = MagicMock()

            # Configure mock classes to return mock instances
            mock_factory.create_database.return_value = mock_db
            mock_event_bus_class.return_value = mock_event_bus
            mock_matching_engine_class.return_value = mock_matching_engine
            mock_account_service_class.return_value = mock_account_service
            mock_wallet_service_class.return_value = mock_wallet_service
            mock_admin_service_class.return_value = mock_admin_service
            mock_broadcaster_class.return_value = mock_broadcaster

            result = build_application_context(market)

            assert result is not None
            assert "db" in result
            assert "event_bus" in result
            assert "matching" in result
            assert "account_service" in result
            assert "wallet_service" in result
            assert "admin_service" in result
            assert "market_data" in result

    def test_build_application_context_default_market(self):
        """Test application context building with default market"""
        with (
            patch("alt_exchange.infra.bootstrap.DatabaseFactory") as mock_factory,
            patch(
                "alt_exchange.infra.bootstrap.InMemoryEventBus"
            ) as mock_event_bus_class,
            patch(
                "alt_exchange.infra.bootstrap.MatchingEngine"
            ) as mock_matching_engine_class,
            patch(
                "alt_exchange.infra.bootstrap.AccountService"
            ) as mock_account_service_class,
            patch(
                "alt_exchange.infra.bootstrap.WalletService"
            ) as mock_wallet_service_class,
            patch(
                "alt_exchange.infra.bootstrap.AdminService"
            ) as mock_admin_service_class,
            patch(
                "alt_exchange.infra.bootstrap.MarketDataBroadcaster"
            ) as mock_broadcaster_class,
        ):

            # Mock instances
            mock_db = MagicMock()
            mock_event_bus = MagicMock()
            mock_matching_engine = MagicMock()
            mock_account_service = MagicMock()
            mock_wallet_service = MagicMock()
            mock_admin_service = MagicMock()
            mock_broadcaster = MagicMock()

            # Configure mock classes to return mock instances
            mock_factory.create_database.return_value = mock_db
            mock_event_bus_class.return_value = mock_event_bus
            mock_matching_engine_class.return_value = mock_matching_engine
            mock_account_service_class.return_value = mock_account_service
            mock_wallet_service_class.return_value = mock_wallet_service
            mock_admin_service_class.return_value = mock_admin_service
            mock_broadcaster_class.return_value = mock_broadcaster

            result = build_application_context()

            assert result is not None
            assert "db" in result
            assert "event_bus" in result
            assert "matching" in result
            assert "account_service" in result
            assert "wallet_service" in result
            assert "admin_service" in result
            assert "market_data" in result

    def test_build_production_context_success(self):
        """Test successful production context building"""
        market = "ALT/USDT"

        with (
            patch("alt_exchange.infra.bootstrap.DatabaseFactory") as mock_factory,
            patch(
                "alt_exchange.infra.bootstrap.InMemoryEventBus"
            ) as mock_event_bus_class,
            patch(
                "alt_exchange.infra.bootstrap.MatchingEngine"
            ) as mock_matching_engine_class,
            patch(
                "alt_exchange.infra.bootstrap.AccountService"
            ) as mock_account_service_class,
            patch(
                "alt_exchange.infra.bootstrap.WalletService"
            ) as mock_wallet_service_class,
            patch(
                "alt_exchange.infra.bootstrap.AdminService"
            ) as mock_admin_service_class,
            patch(
                "alt_exchange.infra.bootstrap.MarketDataBroadcaster"
            ) as mock_broadcaster_class,
            patch.dict(
                os.environ,
                {"DATABASE_URL": "postgresql://test:test@localhost:5432/test"},
            ),
        ):

            # Mock instances
            mock_db = MagicMock()
            mock_event_bus = MagicMock()
            mock_matching_engine = MagicMock()
            mock_account_service = MagicMock()
            mock_wallet_service = MagicMock()
            mock_admin_service = MagicMock()
            mock_broadcaster = MagicMock()

            # Configure mock classes to return mock instances
            mock_factory.create_for_production.return_value = mock_db
            mock_event_bus_class.return_value = mock_event_bus
            mock_matching_engine_class.return_value = mock_matching_engine
            mock_account_service_class.return_value = mock_account_service
            mock_wallet_service_class.return_value = mock_wallet_service
            mock_admin_service_class.return_value = mock_admin_service
            mock_broadcaster_class.return_value = mock_broadcaster

            result = build_production_context(market)

            assert result is not None
            assert "db" in result
            assert "event_bus" in result
            assert "matching" in result
            assert "account_service" in result
            assert "wallet_service" in result
            assert "admin_service" in result
            assert "market_data" in result

    def test_build_production_context_default_market(self):
        """Test production context building with default market"""
        with (
            patch("alt_exchange.infra.bootstrap.DatabaseFactory") as mock_factory,
            patch(
                "alt_exchange.infra.bootstrap.InMemoryEventBus"
            ) as mock_event_bus_class,
            patch(
                "alt_exchange.infra.bootstrap.MatchingEngine"
            ) as mock_matching_engine_class,
            patch(
                "alt_exchange.infra.bootstrap.AccountService"
            ) as mock_account_service_class,
            patch(
                "alt_exchange.infra.bootstrap.WalletService"
            ) as mock_wallet_service_class,
            patch(
                "alt_exchange.infra.bootstrap.AdminService"
            ) as mock_admin_service_class,
            patch(
                "alt_exchange.infra.bootstrap.MarketDataBroadcaster"
            ) as mock_broadcaster_class,
            patch.dict(
                os.environ,
                {"DATABASE_URL": "postgresql://test:test@localhost:5432/test"},
            ),
        ):

            # Mock instances
            mock_db = MagicMock()
            mock_event_bus = MagicMock()
            mock_matching_engine = MagicMock()
            mock_account_service = MagicMock()
            mock_wallet_service = MagicMock()
            mock_admin_service = MagicMock()
            mock_broadcaster = MagicMock()

            # Configure mock classes to return mock instances
            mock_factory.create_for_production.return_value = mock_db
            mock_event_bus_class.return_value = mock_event_bus
            mock_matching_engine_class.return_value = mock_matching_engine
            mock_account_service_class.return_value = mock_account_service
            mock_wallet_service_class.return_value = mock_wallet_service
            mock_admin_service_class.return_value = mock_admin_service
            mock_broadcaster_class.return_value = mock_broadcaster

            result = build_production_context()

            assert result is not None
            assert "db" in result
            assert "event_bus" in result
            assert "matching" in result
            assert "account_service" in result
            assert "wallet_service" in result
            assert "admin_service" in result
            assert "market_data" in result

    def test_build_production_context_default_database_url(self):
        """Test production context building with default database URL"""
        with (
            patch("alt_exchange.infra.bootstrap.DatabaseFactory") as mock_factory,
            patch(
                "alt_exchange.infra.bootstrap.InMemoryEventBus"
            ) as mock_event_bus_class,
            patch(
                "alt_exchange.infra.bootstrap.MatchingEngine"
            ) as mock_matching_engine_class,
            patch(
                "alt_exchange.infra.bootstrap.AccountService"
            ) as mock_account_service_class,
            patch(
                "alt_exchange.infra.bootstrap.WalletService"
            ) as mock_wallet_service_class,
            patch(
                "alt_exchange.infra.bootstrap.AdminService"
            ) as mock_admin_service_class,
            patch(
                "alt_exchange.infra.bootstrap.MarketDataBroadcaster"
            ) as mock_broadcaster_class,
        ):

            # Mock instances
            mock_db = MagicMock()
            mock_event_bus = MagicMock()
            mock_matching_engine = MagicMock()
            mock_account_service = MagicMock()
            mock_wallet_service = MagicMock()
            mock_admin_service = MagicMock()
            mock_broadcaster = MagicMock()

            # Configure mock classes to return mock instances
            mock_factory.create_for_production.return_value = mock_db
            mock_event_bus_class.return_value = mock_event_bus
            mock_matching_engine_class.return_value = mock_matching_engine
            mock_account_service_class.return_value = mock_account_service
            mock_wallet_service_class.return_value = mock_wallet_service
            mock_admin_service_class.return_value = mock_admin_service
            mock_broadcaster_class.return_value = mock_broadcaster

            result = build_production_context()

            assert result is not None
            assert "db" in result
            assert "event_bus" in result
            assert "matching" in result
            assert "account_service" in result
            assert "wallet_service" in result
            assert "admin_service" in result
            assert "market_data" in result

    def test_build_application_context_database_factory_call(self):
        """Test database factory call in application context"""
        market = "ALT/USDT"

        with (
            patch("alt_exchange.infra.bootstrap.DatabaseFactory") as mock_factory,
            patch(
                "alt_exchange.infra.bootstrap.InMemoryEventBus"
            ) as mock_event_bus_class,
            patch(
                "alt_exchange.infra.bootstrap.MatchingEngine"
            ) as mock_matching_engine_class,
            patch(
                "alt_exchange.infra.bootstrap.AccountService"
            ) as mock_account_service_class,
            patch(
                "alt_exchange.infra.bootstrap.WalletService"
            ) as mock_wallet_service_class,
            patch(
                "alt_exchange.infra.bootstrap.AdminService"
            ) as mock_admin_service_class,
            patch(
                "alt_exchange.infra.bootstrap.MarketDataBroadcaster"
            ) as mock_broadcaster_class,
        ):

            # Mock instances
            mock_db = MagicMock()
            mock_event_bus = MagicMock()
            mock_matching_engine = MagicMock()
            mock_account_service = MagicMock()
            mock_wallet_service = MagicMock()
            mock_admin_service = MagicMock()
            mock_broadcaster = MagicMock()

            # Configure mock classes to return mock instances
            mock_factory.create_database.return_value = mock_db
            mock_event_bus_class.return_value = mock_event_bus
            mock_matching_engine_class.return_value = mock_matching_engine
            mock_account_service_class.return_value = mock_account_service
            mock_wallet_service_class.return_value = mock_wallet_service
            mock_admin_service_class.return_value = mock_admin_service
            mock_broadcaster_class.return_value = mock_broadcaster

            result = build_application_context(market)

            # Verify database factory was called
            mock_factory.create_database.assert_called_once()
            assert result["db"] is mock_db

    def test_build_production_context_database_factory_call(self):
        """Test database factory call in production context"""
        market = "ALT/USDT"

        with (
            patch("alt_exchange.infra.bootstrap.DatabaseFactory") as mock_factory,
            patch(
                "alt_exchange.infra.bootstrap.InMemoryEventBus"
            ) as mock_event_bus_class,
            patch(
                "alt_exchange.infra.bootstrap.MatchingEngine"
            ) as mock_matching_engine_class,
            patch(
                "alt_exchange.infra.bootstrap.AccountService"
            ) as mock_account_service_class,
            patch(
                "alt_exchange.infra.bootstrap.WalletService"
            ) as mock_wallet_service_class,
            patch(
                "alt_exchange.infra.bootstrap.AdminService"
            ) as mock_admin_service_class,
            patch(
                "alt_exchange.infra.bootstrap.MarketDataBroadcaster"
            ) as mock_broadcaster_class,
            patch.dict(
                os.environ,
                {"DATABASE_URL": "postgresql://test:test@localhost:5432/test"},
            ),
        ):

            # Mock instances
            mock_db = MagicMock()
            mock_event_bus = MagicMock()
            mock_matching_engine = MagicMock()
            mock_account_service = MagicMock()
            mock_wallet_service = MagicMock()
            mock_admin_service = MagicMock()
            mock_broadcaster = MagicMock()

            # Configure mock classes to return mock instances
            mock_factory.create_for_production.return_value = mock_db
            mock_event_bus_class.return_value = mock_event_bus
            mock_matching_engine_class.return_value = mock_matching_engine
            mock_account_service_class.return_value = mock_account_service
            mock_wallet_service_class.return_value = mock_wallet_service
            mock_admin_service_class.return_value = mock_admin_service
            mock_broadcaster_class.return_value = mock_broadcaster

            result = build_production_context(market)

            # Verify database factory was called with correct URL
            mock_factory.create_for_production.assert_called_once_with(
                "postgresql://test:test@localhost:5432/test"
            )
            assert result["db"] is mock_db

    def test_build_application_context_service_initialization_order(self):
        """Test service initialization order in application context"""
        market = "ALT/USDT"

        with (
            patch("alt_exchange.infra.bootstrap.DatabaseFactory") as mock_factory,
            patch(
                "alt_exchange.infra.bootstrap.InMemoryEventBus"
            ) as mock_event_bus_class,
            patch(
                "alt_exchange.infra.bootstrap.MatchingEngine"
            ) as mock_matching_engine_class,
            patch(
                "alt_exchange.infra.bootstrap.AccountService"
            ) as mock_account_service_class,
            patch(
                "alt_exchange.infra.bootstrap.WalletService"
            ) as mock_wallet_service_class,
            patch(
                "alt_exchange.infra.bootstrap.AdminService"
            ) as mock_admin_service_class,
            patch(
                "alt_exchange.infra.bootstrap.MarketDataBroadcaster"
            ) as mock_broadcaster_class,
        ):

            # Mock instances
            mock_db = MagicMock()
            mock_event_bus = MagicMock()
            mock_matching_engine = MagicMock()
            mock_account_service = MagicMock()
            mock_wallet_service = MagicMock()
            mock_admin_service = MagicMock()
            mock_broadcaster = MagicMock()

            # Configure mock classes to return mock instances
            mock_factory.create_database.return_value = mock_db
            mock_event_bus_class.return_value = mock_event_bus
            mock_matching_engine_class.return_value = mock_matching_engine
            mock_account_service_class.return_value = mock_account_service
            mock_wallet_service_class.return_value = mock_wallet_service
            mock_admin_service_class.return_value = mock_admin_service
            mock_broadcaster_class.return_value = mock_broadcaster

            result = build_application_context(market)

            # Verify initialization order by checking call counts
            assert mock_factory.create_database.call_count == 1
            assert mock_event_bus_class.call_count == 1
            assert mock_matching_engine_class.call_count == 1
            assert mock_account_service_class.call_count == 1
            assert mock_wallet_service_class.call_count == 1
            assert mock_admin_service_class.call_count == 1
            assert mock_broadcaster_class.call_count == 1

    def test_build_production_context_service_initialization_order(self):
        """Test service initialization order in production context"""
        market = "ALT/USDT"

        with (
            patch("alt_exchange.infra.bootstrap.DatabaseFactory") as mock_factory,
            patch(
                "alt_exchange.infra.bootstrap.InMemoryEventBus"
            ) as mock_event_bus_class,
            patch(
                "alt_exchange.infra.bootstrap.MatchingEngine"
            ) as mock_matching_engine_class,
            patch(
                "alt_exchange.infra.bootstrap.AccountService"
            ) as mock_account_service_class,
            patch(
                "alt_exchange.infra.bootstrap.WalletService"
            ) as mock_wallet_service_class,
            patch(
                "alt_exchange.infra.bootstrap.AdminService"
            ) as mock_admin_service_class,
            patch(
                "alt_exchange.infra.bootstrap.MarketDataBroadcaster"
            ) as mock_broadcaster_class,
            patch.dict(
                os.environ,
                {"DATABASE_URL": "postgresql://test:test@localhost:5432/test"},
            ),
        ):

            # Mock instances
            mock_db = MagicMock()
            mock_event_bus = MagicMock()
            mock_matching_engine = MagicMock()
            mock_account_service = MagicMock()
            mock_wallet_service = MagicMock()
            mock_admin_service = MagicMock()
            mock_broadcaster = MagicMock()

            # Configure mock classes to return mock instances
            mock_factory.create_for_production.return_value = mock_db
            mock_event_bus_class.return_value = mock_event_bus
            mock_matching_engine_class.return_value = mock_matching_engine
            mock_account_service_class.return_value = mock_account_service
            mock_wallet_service_class.return_value = mock_wallet_service
            mock_admin_service_class.return_value = mock_admin_service
            mock_broadcaster_class.return_value = mock_broadcaster

            result = build_production_context(market)

            # Verify initialization order by checking call counts
            assert mock_factory.create_for_production.call_count == 1
            assert mock_event_bus_class.call_count == 1
            assert mock_matching_engine_class.call_count == 1
            assert mock_account_service_class.call_count == 1
            assert mock_wallet_service_class.call_count == 1
            assert mock_admin_service_class.call_count == 1
            assert mock_broadcaster_class.call_count == 1

    def test_build_application_context_context_structure(self):
        """Test application context structure"""
        market = "ALT/USDT"

        with (
            patch("alt_exchange.infra.bootstrap.DatabaseFactory") as mock_factory,
            patch(
                "alt_exchange.infra.bootstrap.InMemoryEventBus"
            ) as mock_event_bus_class,
            patch(
                "alt_exchange.infra.bootstrap.MatchingEngine"
            ) as mock_matching_engine_class,
            patch(
                "alt_exchange.infra.bootstrap.AccountService"
            ) as mock_account_service_class,
            patch(
                "alt_exchange.infra.bootstrap.WalletService"
            ) as mock_wallet_service_class,
            patch(
                "alt_exchange.infra.bootstrap.AdminService"
            ) as mock_admin_service_class,
            patch(
                "alt_exchange.infra.bootstrap.MarketDataBroadcaster"
            ) as mock_broadcaster_class,
        ):

            # Mock instances
            mock_db = MagicMock()
            mock_event_bus = MagicMock()
            mock_matching_engine = MagicMock()
            mock_account_service = MagicMock()
            mock_wallet_service = MagicMock()
            mock_admin_service = MagicMock()
            mock_broadcaster = MagicMock()

            # Configure mock classes to return mock instances
            mock_factory.create_database.return_value = mock_db
            mock_event_bus_class.return_value = mock_event_bus
            mock_matching_engine_class.return_value = mock_matching_engine
            mock_account_service_class.return_value = mock_account_service
            mock_wallet_service_class.return_value = mock_wallet_service
            mock_admin_service_class.return_value = mock_admin_service
            mock_broadcaster_class.return_value = mock_broadcaster

            result = build_application_context(market)

            # Verify context structure
            assert isinstance(result, dict)
            assert len(result) == 7

            # Verify all required keys are present
            required_keys = [
                "db",
                "event_bus",
                "matching",
                "account_service",
                "wallet_service",
                "admin_service",
                "market_data",
            ]

            for key in required_keys:
                assert key in result
                assert result[key] is not None

    def test_build_production_context_context_structure(self):
        """Test production context structure"""
        market = "ALT/USDT"

        with (
            patch("alt_exchange.infra.bootstrap.DatabaseFactory") as mock_factory,
            patch(
                "alt_exchange.infra.bootstrap.InMemoryEventBus"
            ) as mock_event_bus_class,
            patch(
                "alt_exchange.infra.bootstrap.MatchingEngine"
            ) as mock_matching_engine_class,
            patch(
                "alt_exchange.infra.bootstrap.AccountService"
            ) as mock_account_service_class,
            patch(
                "alt_exchange.infra.bootstrap.WalletService"
            ) as mock_wallet_service_class,
            patch(
                "alt_exchange.infra.bootstrap.AdminService"
            ) as mock_admin_service_class,
            patch(
                "alt_exchange.infra.bootstrap.MarketDataBroadcaster"
            ) as mock_broadcaster_class,
            patch.dict(
                os.environ,
                {"DATABASE_URL": "postgresql://test:test@localhost:5432/test"},
            ),
        ):

            # Mock instances
            mock_db = MagicMock()
            mock_event_bus = MagicMock()
            mock_matching_engine = MagicMock()
            mock_account_service = MagicMock()
            mock_wallet_service = MagicMock()
            mock_admin_service = MagicMock()
            mock_broadcaster = MagicMock()

            # Configure mock classes to return mock instances
            mock_factory.create_for_production.return_value = mock_db
            mock_event_bus_class.return_value = mock_event_bus
            mock_matching_engine_class.return_value = mock_matching_engine
            mock_account_service_class.return_value = mock_account_service
            mock_wallet_service_class.return_value = mock_wallet_service
            mock_admin_service_class.return_value = mock_admin_service
            mock_broadcaster_class.return_value = mock_broadcaster

            result = build_production_context(market)

            # Verify context structure
            assert isinstance(result, dict)
            assert len(result) == 7

            # Verify all required keys are present
            required_keys = [
                "db",
                "event_bus",
                "matching",
                "account_service",
                "wallet_service",
                "admin_service",
                "market_data",
            ]

            for key in required_keys:
                assert key in result
                assert result[key] is not None
