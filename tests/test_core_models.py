"""
Core models 테스트
"""

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from alt_exchange.core.enums import (AccountStatus, Asset, OrderStatus,
                                     OrderType, Side, TimeInForce,
                                     TransactionStatus, TransactionType)
from alt_exchange.core.models import (Account, AuditLog, Balance, Order, Trade,
                                      Transaction, User)


class TestUser:
    def test_user_creation(self):
        user = User(id=1, email="test@example.com", password_hash="hashed_password")
        assert user.id == 1
        assert user.email == "test@example.com"
        assert user.password_hash == "hashed_password"
        assert isinstance(user.created_at, datetime)

    def test_user_with_optional_fields(self):
        user = User(
            id=2,
            email="test2@example.com",
            password_hash="hashed_password2",
            last_login=datetime.now(timezone.utc),
        )
        assert user.last_login is not None


class TestAccount:
    def test_account_creation(self):
        account = Account(id=1, user_id=1)
        assert account.id == 1
        assert account.user_id == 1
        assert account.status == AccountStatus.ACTIVE
        assert account.kyc_level == 0
        assert account.frozen is False


class TestBalance:
    def test_balance_creation(self):
        balance = Balance(
            id=1,
            account_id=1,
            asset=Asset.ALT,
            available=Decimal("100.0"),
            locked=Decimal("10.0"),
        )
        assert balance.id == 1
        assert balance.account_id == 1
        assert balance.asset == Asset.ALT
        assert balance.available == Decimal("100.0")
        assert balance.locked == Decimal("10.0")
        assert isinstance(balance.updated_at, datetime)


class TestOrder:
    def test_order_creation(self):
        order = Order(
            id=1,
            user_id=1,
            account_id=1,
            market="ALT/USDT",
            side=Side.BUY,
            type=OrderType.LIMIT,
            time_in_force=TimeInForce.GTC,
            price=Decimal("100.0"),
            amount=Decimal("10.0"),
        )
        assert order.id == 1
        assert order.user_id == 1
        assert order.account_id == 1
        assert order.market == "ALT/USDT"
        assert order.side == Side.BUY
        assert order.type == OrderType.LIMIT
        assert order.time_in_force == TimeInForce.GTC
        assert order.price == Decimal("100.0")
        assert order.amount == Decimal("10.0")
        assert order.filled == Decimal("0")
        assert order.status == OrderStatus.OPEN

    def test_order_remaining(self):
        order = Order(
            id=1,
            user_id=1,
            account_id=1,
            market="ALT/USDT",
            side=Side.BUY,
            type=OrderType.LIMIT,
            time_in_force=TimeInForce.GTC,
            price=Decimal("100.0"),
            amount=Decimal("10.0"),
            filled=Decimal("3.0"),
        )
        assert order.remaining() == Decimal("7.0")


class TestTrade:
    def test_trade_creation(self):
        trade = Trade(
            id=1,
            buy_order_id=1,
            sell_order_id=2,
            maker_order_id=1,
            taker_order_id=2,
            taker_side=Side.BUY,
            price=Decimal("100.0"),
            amount=Decimal("5.0"),
            fee=Decimal("0.5"),
        )
        assert trade.id == 1
        assert trade.buy_order_id == 1
        assert trade.sell_order_id == 2
        assert trade.maker_order_id == 1
        assert trade.taker_order_id == 2
        assert trade.taker_side == Side.BUY
        assert trade.price == Decimal("100.0")
        assert trade.amount == Decimal("5.0")
        assert trade.fee == Decimal("0.5")
        assert isinstance(trade.created_at, datetime)


class TestTransaction:
    def test_transaction_creation(self):
        transaction = Transaction(
            id=1,
            user_id=1,
            tx_hash="0x123",
            chain="BSC",
            asset=Asset.ALT,
            type=TransactionType.DEPOSIT,
            status=TransactionStatus.PENDING,
            confirmations=0,
            amount=Decimal("100.0"),
            address="0xabc",
        )
        assert transaction.id == 1
        assert transaction.user_id == 1
        assert transaction.tx_hash == "0x123"
        assert transaction.chain == "BSC"
        assert transaction.asset == Asset.ALT
        assert transaction.type == TransactionType.DEPOSIT
        assert transaction.status == TransactionStatus.PENDING
        assert transaction.confirmations == 0
        assert transaction.amount == Decimal("100.0")
        assert transaction.address == "0xabc"
        assert isinstance(transaction.created_at, datetime)


class TestAuditLog:
    def test_audit_log_creation(self):
        audit_log = AuditLog(
            id=1,
            actor="admin_1",
            action="withdrawal_approved",
            entity="transaction",
            metadata={"amount": "100.0", "asset": "ALT"},
        )
        assert audit_log.id == 1
        assert audit_log.actor == "admin_1"
        assert audit_log.action == "withdrawal_approved"
        assert audit_log.entity == "transaction"
        assert audit_log.metadata == {"amount": "100.0", "asset": "ALT"}
        assert isinstance(audit_log.created_at, datetime)
