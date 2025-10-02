"""
Account Service 테스트
"""

from decimal import Decimal

import pytest

from alt_exchange.core.enums import (Asset, OrderStatus, OrderType, Side,
                                     TimeInForce)
from alt_exchange.core.models import Account, Balance, Order, User
from alt_exchange.infra.database.in_memory import InMemoryDatabase
from alt_exchange.infra.event_bus import InMemoryEventBus
from alt_exchange.services.account.service import AccountService
from alt_exchange.services.matching.engine import MatchingEngine


class TestAccountService:
    def setup_method(self):
        self.db = InMemoryDatabase()
        self.event_bus = InMemoryEventBus()
        self.matching_engine = MatchingEngine("ALT/USDT", self.db, self.event_bus)
        self.service = AccountService(self.db, self.event_bus, self.matching_engine)

    def test_create_user(self):
        user = self.service.create_user("test@example.com", "password123")

        assert user.email == "test@example.com"
        assert user.password_hash is not None
        assert user.id is not None

        # Verify account was created
        account = self.service.get_account(user.id)
        assert account.user_id == user.id

        # Verify balances were created for all assets
        for asset in Asset:
            balance = self.service.get_balance(user.id, asset)
            assert balance.asset == asset
            assert balance.available == Decimal("0")
            assert balance.locked == Decimal("0")

    def test_get_account(self):
        user = self.service.create_user("test@example.com", "password123")
        account = self.service.get_account(user.id)

        assert account.user_id == user.id
        assert account.id is not None

    def test_get_balance(self):
        user = self.service.create_user("test@example.com", "password123")
        balance = self.service.get_balance(user.id, Asset.ALT)

        assert balance.asset == Asset.ALT
        assert balance.available == Decimal("0")
        assert balance.locked == Decimal("0")

    def test_place_limit_order(self):
        user = self.service.create_user("test@example.com", "password123")

        # Add some balance first - need enough for price * amount * (1 + fee_rate)
        account = self.service.get_account(user.id)
        balance = self.service.get_balance(user.id, Asset.USDT)
        balance.available = Decimal(
            "2000.0"
        )  # More than needed: 100 * 10 * 1.001 = 1001
        self.db.upsert_balance(balance)

        order = self.service.place_limit_order(
            user_id=user.id,
            side=Side.BUY,
            price=Decimal("100.0"),
            amount=Decimal("10.0"),
            time_in_force=TimeInForce.GTC,
        )

        assert order.user_id == user.id
        assert order.side == Side.BUY
        assert order.type == OrderType.LIMIT
        assert order.price == Decimal("100.0")
        assert order.amount == Decimal("10.0")
        assert order.time_in_force == TimeInForce.GTC
        assert order.status == OrderStatus.OPEN

    def test_place_stop_order(self):
        user = self.service.create_user("test@example.com", "password123")

        # Add some balance first - need enough for price * amount * (1 + fee_rate)
        account = self.service.get_account(user.id)
        balance = self.service.get_balance(user.id, Asset.USDT)
        balance.available = Decimal(
            "2000.0"
        )  # More than needed: 100 * 10 * 1.001 = 1001
        self.db.upsert_balance(balance)

        order = self.service.place_stop_order(
            user_id=user.id,
            side=Side.BUY,
            price=Decimal("100.0"),
            stop_price=Decimal("90.0"),
            amount=Decimal("10.0"),
            time_in_force=TimeInForce.GTC,
        )

        assert order.user_id == user.id
        assert order.side == Side.BUY
        assert order.type == OrderType.STOP
        assert order.price == Decimal("100.0")
        assert order.stop_price == Decimal("90.0")
        assert order.amount == Decimal("10.0")
        assert order.status == OrderStatus.OPEN

    def test_cancel_order(self):
        user = self.service.create_user("test@example.com", "password123")

        # Add some balance first - need enough for price * amount * (1 + fee_rate)
        account = self.service.get_account(user.id)
        balance = self.service.get_balance(user.id, Asset.USDT)
        balance.available = Decimal(
            "2000.0"
        )  # More than needed: 100 * 10 * 1.001 = 1001
        self.db.upsert_balance(balance)

        order = self.service.place_limit_order(
            user_id=user.id,
            side=Side.BUY,
            price=Decimal("100.0"),
            amount=Decimal("10.0"),
            time_in_force=TimeInForce.GTC,
        )

        success = self.service.cancel_order(user.id, order.id)
        assert success is True

        # Verify order was cancelled
        updated_order = self.db.get_order(order.id)
        assert updated_order.status == OrderStatus.CANCELED

    def test_get_user_orders(self):
        user = self.service.create_user("test@example.com", "password123")

        # Add some balance first - need enough for price * amount * (1 + fee_rate)
        account = self.service.get_account(user.id)
        balance = self.service.get_balance(user.id, Asset.USDT)
        balance.available = Decimal(
            "2000.0"
        )  # More than needed: 100 * 10 * 1.001 = 1001
        self.db.upsert_balance(balance)

        # Add ALT balance for sell order
        alt_balance = self.service.get_balance(user.id, Asset.ALT)
        alt_balance.available = Decimal("100.0")
        self.db.upsert_balance(alt_balance)

        # Place multiple orders
        order1 = self.service.place_limit_order(
            user_id=user.id,
            side=Side.BUY,
            price=Decimal("100.0"),
            amount=Decimal("10.0"),
            time_in_force=TimeInForce.GTC,
        )

        order2 = self.service.place_limit_order(
            user_id=user.id,
            side=Side.SELL,
            price=Decimal("110.0"),
            amount=Decimal("5.0"),
            time_in_force=TimeInForce.GTC,
        )

        orders = self.service.get_user_orders(user.id)
        assert len(orders) == 2
        assert order1.id in [o.id for o in orders]
        assert order2.id in [o.id for o in orders]

    def test_get_user_trades(self):
        user = self.service.create_user("test@example.com", "password123")

        # Add some balance first
        account = self.service.get_account(user.id)
        balance = self.service.get_balance(user.id, Asset.USDT)
        balance.available = Decimal("1000.0")
        self.db.upsert_balance(balance)

        trades = self.service.get_user_trades(user.id)
        assert len(trades) == 0  # No trades initially
