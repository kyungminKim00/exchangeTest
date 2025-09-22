from __future__ import annotations

from alt_exchange.infra.datastore import InMemoryDatabase
from alt_exchange.infra.event_bus import InMemoryEventBus
from alt_exchange.services.account.service import AccountService
from alt_exchange.services.market_data.broadcaster import MarketDataBroadcaster
from alt_exchange.services.matching.engine import MatchingEngine
from alt_exchange.services.wallet.service import WalletService


def build_application_context(market: str = "ALT/USDT") -> dict:
    """Creates a fully wired service graph for tests or interactive sessions."""
    db = InMemoryDatabase()
    bus = InMemoryEventBus()
    matching = MatchingEngine(market=market, db=db, event_bus=bus)
    account = AccountService(db=db, event_bus=bus, matching_engine=matching)
    wallet = WalletService(account_service=account)
    market_data = MarketDataBroadcaster(matching=matching, event_bus=bus)
    return {
        "db": db,
        "event_bus": bus,
        "matching": matching,
        "account_service": account,
        "wallet_service": wallet,
        "market_data": market_data,
    }
