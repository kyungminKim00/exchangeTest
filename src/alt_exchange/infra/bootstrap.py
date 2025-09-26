from __future__ import annotations

import os

from alt_exchange.infra.database import DatabaseFactory
from alt_exchange.infra.event_bus import InMemoryEventBus
from alt_exchange.services.account.service import AccountService
from alt_exchange.services.admin.service import AdminService
from alt_exchange.services.market_data.broadcaster import MarketDataBroadcaster
from alt_exchange.services.matching.engine import MatchingEngine
from alt_exchange.services.wallet.service import WalletService


def build_application_context(market: str = "ALT/USDT") -> dict:
    """Creates a fully wired service graph for tests or interactive sessions."""
    # Use database factory to create appropriate database instance
    db = DatabaseFactory.create_database()
    bus = InMemoryEventBus()
    matching = MatchingEngine(market=market, db=db, event_bus=bus)
    account = AccountService(db=db, event_bus=bus, matching_engine=matching)
    wallet = WalletService(account_service=account)
    admin = AdminService(
        db=db, event_bus=bus, account_service=account, wallet_service=wallet
    )
    market_data = MarketDataBroadcaster(matching=matching, event_bus=bus)
    return {
        "db": db,
        "event_bus": bus,
        "matching": matching,
        "account_service": account,
        "wallet_service": wallet,
        "admin_service": admin,
        "market_data": market_data,
    }


def build_production_context(market: str = "ALT/USDT") -> dict:
    """Creates a production-ready service graph with PostgreSQL."""
    db = DatabaseFactory.create_for_production(
        os.getenv(
            "DATABASE_URL",
            "postgresql://alt_user:alt_password@localhost:5432/alt_exchange",
        )
    )
    bus = InMemoryEventBus()  # In production, this would be Kafka/Redis
    matching = MatchingEngine(market=market, db=db, event_bus=bus)
    account = AccountService(db=db, event_bus=bus, matching_engine=matching)
    wallet = WalletService(account_service=account)
    admin = AdminService(
        db=db, event_bus=bus, account_service=account, wallet_service=wallet
    )
    market_data = MarketDataBroadcaster(matching=matching, event_bus=bus)
    return {
        "db": db,
        "event_bus": bus,
        "matching": matching,
        "account_service": account,
        "wallet_service": wallet,
        "admin_service": admin,
        "market_data": market_data,
    }
