"""
Tests for database abstraction layer
"""

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from alt_exchange.core.enums import Asset, OrderStatus, OrderType, Side, TimeInForce
from alt_exchange.core.models import Account, Balance, Order, User
from alt_exchange.infra.database import DatabaseFactory
from alt_exchange.infra.database.in_memory import InMemoryDatabase, InMemoryUnitOfWork


class TestDatabaseFactory:
    """Test database factory functionality"""

    def test_create_inmemory_database(self):
        """Test creating in-memory database"""
        db = DatabaseFactory.create_database("inmemory")
        assert isinstance(db, InMemoryDatabase)

    def test_create_database_auto_detect(self):
        """Test auto-detection of database type"""
        db = DatabaseFactory.create_database()
        assert isinstance(db, InMemoryDatabase)

    def test_create_for_testing(self):
        """Test creating database for testing"""
        db = DatabaseFactory.create_for_testing()
        assert isinstance(db, InMemoryDatabase)

    def test_unsupported_database_type(self):
        """Test error for unsupported database type"""
        with pytest.raises(ValueError, match="Unsupported database type"):
            DatabaseFactory.create_database("unsupported")


class TestInMemoryDatabase:
    """Test in-memory database implementation"""

    @pytest.fixture
    def db(self):
        """Create in-memory database for testing"""
        return InMemoryDatabase()

    def test_next_id(self, db):
        """Test ID generation"""
        user_id = db.next_id("users")
        assert user_id == 1

        account_id = db.next_id("accounts")
        assert account_id == 1

    def test_user_operations(self, db):
        """Test user CRUD operations"""
        # Create user
        user = User(id=1, email="test@example.com", password_hash="hashed_password")
        db.insert_user(user)

        # Retrieve user
        retrieved_user = db.get_user(1)
        assert retrieved_user is not None
        assert retrieved_user.email == "test@example.com"

        # Retrieve user by email
        user_by_email = db.get_user_by_email("test@example.com")
        assert user_by_email is not None
        assert user_by_email.id == 1

    def test_account_operations(self, db):
        """Test account CRUD operations"""
        # Create user first
        user = User(id=1, email="test@example.com", password_hash="hash")
        db.insert_user(user)

        # Create account
        account = Account(id=1, user_id=1)
        db.insert_account(account)

        # Retrieve account
        retrieved_account = db.get_account(1)
        assert retrieved_account is not None
        assert retrieved_account.user_id == 1

        # Get accounts by user
        user_accounts = db.get_accounts_by_user(1)
        assert len(user_accounts) == 1
        assert user_accounts[0].id == 1

    def test_balance_operations(self, db):
        """Test balance CRUD operations"""
        # Create user and account first
        user = User(id=1, email="test@example.com", password_hash="hash")
        db.insert_user(user)
        account = Account(id=1, user_id=1)
        db.insert_account(account)

        # Create balance
        balance = Balance(
            id=1,
            account_id=1,
            asset=Asset.ALT,
            available=Decimal("100.0"),
            locked=Decimal("10.0"),
        )
        db.upsert_balance(balance)

        # Find balance
        found_balance = db.find_balance(1, Asset.ALT)
        assert found_balance is not None
        assert found_balance.available == Decimal("100.0")
        assert found_balance.locked == Decimal("10.0")

        # Get balances by account
        account_balances = db.get_balances_by_account(1)
        assert len(account_balances) == 1
        assert account_balances[0].asset == Asset.ALT

    def test_order_operations(self, db):
        """Test order CRUD operations"""
        # Create user and account first
        user = User(id=1, email="test@example.com", password_hash="hash")
        db.insert_user(user)
        account = Account(id=1, user_id=1)
        db.insert_account(account)

        # Create order
        order = Order(
            id=1,
            user_id=1,
            account_id=1,
            market="ALT/USDT",
            side=Side.BUY,
            type=OrderType.LIMIT,
            time_in_force=TimeInForce.GTC,
            price=Decimal("100.0"),
            amount=Decimal("1.0"),
        )
        db.insert_order(order)

        # Retrieve order
        retrieved_order = db.get_order(1)
        assert retrieved_order is not None
        assert retrieved_order.market == "ALT/USDT"
        assert retrieved_order.side == Side.BUY

        # Update order
        order.status = OrderStatus.FILLED
        order.filled = Decimal("1.0")
        db.update_order(order)

        updated_order = db.get_order(1)
        assert updated_order.status == OrderStatus.FILLED
        assert updated_order.filled == Decimal("1.0")

    def test_database_clone(self, db):
        """Test database cloning for testing"""
        # Add some data
        user = User(id=1, email="test@example.com", password_hash="hash")
        db.insert_user(user)

        # Clone database
        cloned_db = db.clone()

        # Verify clone has same data
        cloned_user = cloned_db.get_user(1)
        assert cloned_user is not None
        assert cloned_user.email == "test@example.com"

        # Verify they are independent
        user2 = User(id=2, email="test2@example.com", password_hash="hash2")
        cloned_db.insert_user(user2)

        assert db.get_user(2) is None
        assert cloned_db.get_user(2) is not None


class TestInMemoryUnitOfWork:
    """Test in-memory unit of work implementation"""

    @pytest.fixture
    def db(self):
        """Create in-memory database for testing"""
        return InMemoryDatabase()

    def test_successful_transaction(self, db):
        """Test successful transaction commit"""
        with InMemoryUnitOfWork(db) as uow:
            user = User(id=1, email="test@example.com", password_hash="hash")
            db.insert_user(user)
            uow.commit()

        # Verify user was committed
        retrieved_user = db.get_user(1)
        assert retrieved_user is not None
        assert retrieved_user.email == "test@example.com"

    def test_failed_transaction_rollback(self, db):
        """Test transaction rollback on exception"""
        try:
            with InMemoryUnitOfWork(db) as uow:
                user = User(id=1, email="test@example.com", password_hash="hash")
                db.insert_user(user)
                # Simulate an error
                raise ValueError("Test error")
        except ValueError:
            pass

        # Verify user was not committed
        retrieved_user = db.get_user(1)
        assert retrieved_user is None

    def test_manual_rollback(self, db):
        """Test manual transaction rollback"""
        with InMemoryUnitOfWork(db) as uow:
            user = User(id=1, email="test@example.com", password_hash="hash")
            db.insert_user(user)
            uow.rollback()

        # Verify user was not committed
        retrieved_user = db.get_user(1)
        assert retrieved_user is None
