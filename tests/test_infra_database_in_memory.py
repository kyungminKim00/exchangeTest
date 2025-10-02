"""
InMemory database 테스트
"""

from decimal import Decimal

import pytest

from alt_exchange.core.enums import (AccountStatus, Asset, OrderStatus,
                                     OrderType, Side, TimeInForce,
                                     TransactionStatus, TransactionType)
from alt_exchange.core.models import (Account, AuditLog, Balance, Order, Trade,
                                      Transaction, User)
from alt_exchange.infra.database.in_memory import (InMemoryDatabase,
                                                   InMemoryUnitOfWork)


class TestInMemoryDatabase:
    def test_database_creation(self):
        db = InMemoryDatabase()
        assert db is not None

    def test_next_id(self):
        db = InMemoryDatabase()
        id1 = db.next_id("users")
        id2 = db.next_id("users")
        assert id1 == 1
        assert id2 == 2

    def test_user_operations(self):
        db = InMemoryDatabase()
        user = User(id=1, email="test@example.com", password_hash="hashed_password")

        # Insert user
        inserted_user = db.insert_user(user)
        assert inserted_user == user

        # Get user
        retrieved_user = db.get_user(1)
        assert retrieved_user == user

        # Get user by email
        user_by_email = db.get_user_by_email("test@example.com")
        assert user_by_email == user

    def test_account_operations(self):
        db = InMemoryDatabase()
        account = Account(id=1, user_id=1)

        # Insert account
        inserted_account = db.insert_account(account)
        assert inserted_account == account

        # Get account
        retrieved_account = db.get_account(1)
        assert retrieved_account == account

    def test_balance_operations(self):
        db = InMemoryDatabase()
        balance = Balance(
            id=1,
            account_id=1,
            asset=Asset.ALT,
            available=Decimal("100.0"),
            locked=Decimal("10.0"),
        )

        # Upsert balance
        upserted_balance = db.upsert_balance(balance)
        assert upserted_balance == balance

        # Find balance
        found_balance = db.find_balance(1, Asset.ALT)
        assert found_balance == balance

    def test_order_operations(self):
        db = InMemoryDatabase()
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

        # Insert order
        inserted_order = db.insert_order(order)
        assert inserted_order == order

        # Update order
        order.filled = Decimal("5.0")
        db.update_order(order)

        # Get order
        retrieved_order = db.get_order(1)
        assert retrieved_order.filled == Decimal("5.0")

    def test_trade_operations(self):
        db = InMemoryDatabase()
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

        # Insert trade
        inserted_trade = db.insert_trade(trade)
        assert inserted_trade == trade

        # Get trade
        retrieved_trade = db.get_trade(1)
        assert retrieved_trade == trade

    def test_transaction_operations(self):
        db = InMemoryDatabase()
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

        # Insert transaction
        inserted_transaction = db.insert_transaction(transaction)
        assert inserted_transaction == transaction

        # Update transaction
        transaction.status = TransactionStatus.CONFIRMED
        db.update_transaction(transaction)

        # Get transaction
        retrieved_transaction = db.get_transaction(1)
        assert retrieved_transaction.status == TransactionStatus.CONFIRMED

    def test_audit_log_operations(self):
        db = InMemoryDatabase()
        audit_log = AuditLog(
            id=1,
            actor="admin_1",
            action="withdrawal_approved",
            entity="transaction",
            metadata={"amount": "100.0", "asset": "ALT"},
        )

        # Insert audit log
        inserted_audit_log = db.insert_audit_log(audit_log)
        assert inserted_audit_log == audit_log

        # Get audit logs
        retrieved_audit_logs = db.get_audit_logs()
        assert len(retrieved_audit_logs) == 1
        assert retrieved_audit_logs[0] == audit_log


class TestInMemoryUnitOfWork:
    def test_unit_of_work_commit(self):
        db = InMemoryDatabase()

        with InMemoryUnitOfWork(db) as uow:
            user = User(id=1, email="test@example.com", password_hash="hashed_password")
            db.insert_user(user)
            uow.commit()

        # Verify user was committed
        retrieved_user = db.get_user(1)
        assert retrieved_user == user

    def test_unit_of_work_rollback(self):
        db = InMemoryDatabase()

        try:
            with InMemoryUnitOfWork(db) as uow:
                user = User(
                    id=1, email="test@example.com", password_hash="hashed_password"
                )
                db.insert_user(user)
                # Simulate an error
                raise Exception("Test error")
        except Exception:
            pass

        # Verify user was not committed
        retrieved_user = db.get_user(1)
        assert retrieved_user is None
