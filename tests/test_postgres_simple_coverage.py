"""Simple tests for postgres.py to improve coverage."""

from decimal import Decimal
from unittest.mock import MagicMock, Mock, patch

import pytest

from alt_exchange.core.enums import (Asset, OrderStatus, OrderType, Side,
                                     TimeInForce, TransactionStatus,
                                     TransactionType)
from alt_exchange.core.models import (Account, Balance, Order, Trade,
                                      Transaction, User)
from alt_exchange.infra.database.postgres import PostgreSQLDatabase


class TestPostgresSimpleCoverage:
    """Simple tests for PostgreSQLDatabase to improve coverage."""

    @pytest.fixture
    def mock_engine(self):
        """Mock SQLAlchemy engine."""
        engine = Mock()
        engine.connect.return_value.__enter__ = Mock(return_value=Mock())
        engine.connect.return_value.__exit__ = Mock(return_value=None)
        return engine

    @pytest.fixture
    def mock_session(self):
        """Mock SQLAlchemy session."""
        session = Mock()
        session.add = Mock()
        session.commit = Mock()
        session.rollback = Mock()
        session.close = Mock()
        session.query = Mock()
        session.execute = Mock()
        return session

    @pytest.fixture
    def postgres_db(self, mock_engine, mock_session):
        """PostgreSQLDatabase instance with mocked dependencies."""
        with (
            patch(
                "alt_exchange.infra.database.postgres.create_engine",
                return_value=mock_engine,
            ),
            patch(
                "alt_exchange.infra.database.postgres.sessionmaker",
                return_value=Mock(return_value=mock_session),
            ),
        ):
            return PostgreSQLDatabase("postgresql://test:test@localhost/test")

    def test_postgres_database_init(self, postgres_db):
        """Test PostgreSQLDatabase initialization."""
        assert postgres_db.engine is not None
        assert postgres_db.SessionLocal is not None

    def test_postgres_database_get_session(self, postgres_db, mock_session):
        """Test get_session method."""
        session = postgres_db.get_session()
        assert session is not None

    def test_postgres_database_insert_user(self, postgres_db, mock_session):
        """Test insert_user method."""
        user = User(id=1, email="test@example.com", password_hash="hash")
        result = postgres_db.insert_user(user)
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        assert result is not None

    def test_postgres_database_insert_account(self, postgres_db, mock_session):
        """Test insert_account method."""
        account = Account(id=1, user_id=1)
        result = postgres_db.insert_account(account)
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        assert result is not None

    def test_postgres_database_upsert_balance(self, postgres_db, mock_session):
        """Test upsert_balance method."""
        balance = Balance(
            id=1,
            account_id=1,
            asset=Asset.USDT,
            available=Decimal("100.0"),
            locked=Decimal("0.0"),
        )
        result = postgres_db.upsert_balance(balance)
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        assert result is not None

    def test_postgres_database_insert_order(self, postgres_db, mock_session):
        """Test insert_order method."""
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
            filled=Decimal("0.0"),
            status=OrderStatus.OPEN,
        )
        result = postgres_db.insert_order(order)
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        assert result is not None

    def test_postgres_database_insert_trade(self, postgres_db, mock_session):
        """Test insert_trade method."""
        trade = Trade(
            id=1,
            buy_order_id=1,
            sell_order_id=2,
            maker_order_id=1,
            taker_order_id=2,
            taker_side=Side.BUY,
            price=Decimal("100.0"),
            amount=Decimal("1.0"),
            fee=Decimal("0.1"),
        )
        result = postgres_db.insert_trade(trade)
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        assert result is not None

    def test_postgres_database_insert_transaction(self, postgres_db, mock_session):
        """Test insert_transaction method."""
        transaction = Transaction(
            id=1,
            user_id=1,
            tx_hash="test_hash",
            chain="test_chain",
            confirmations=1,
            address="test_address",
            amount=Decimal("100.0"),
            asset=Asset.USDT,
            type=TransactionType.DEPOSIT,
            status=TransactionStatus.PENDING,
        )
        result = postgres_db.insert_transaction(transaction)
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        assert result is not None

    def test_postgres_database_get_user(self, postgres_db, mock_session):
        """Test get_user method."""
        mock_user = Mock()
        mock_session.query.return_value.filter.return_value.first.return_value = (
            mock_user
        )
        result = postgres_db.get_user(1)
        assert result is not None

    def test_postgres_database_get_account(self, postgres_db, mock_session):
        """Test get_account method."""
        mock_account = Mock()
        mock_session.query.return_value.filter.return_value.first.return_value = (
            mock_account
        )
        result = postgres_db.get_account(1)
        assert result is not None

    def test_postgres_database_find_balance(self, postgres_db, mock_session):
        """Test find_balance method."""
        mock_balance = Mock()
        mock_session.query.return_value.filter.return_value.first.return_value = (
            mock_balance
        )
        result = postgres_db.find_balance(1, Asset.USDT)
        assert result is not None

    def test_postgres_database_get_order(self, postgres_db, mock_session):
        """Test get_order method."""
        mock_order = Mock()
        mock_session.query.return_value.filter.return_value.first.return_value = (
            mock_order
        )
        result = postgres_db.get_order(1)
        assert result is not None

    def test_postgres_database_get_trade(self, postgres_db, mock_session):
        """Test get_trade method."""
        mock_trade = Mock()
        mock_session.query.return_value.filter.return_value.first.return_value = (
            mock_trade
        )
        result = postgres_db.get_trade(1)
        assert result is not None

    def test_postgres_database_get_transaction(self, postgres_db, mock_session):
        """Test get_transaction method."""
        mock_transaction = Mock()
        mock_session.query.return_value.filter.return_value.first.return_value = (
            mock_transaction
        )
        result = postgres_db.get_transaction(1)
        assert result is not None

    def test_postgres_database_update_account(self, postgres_db, mock_session):
        """Test update_account method."""
        account = Account(id=1, user_id=1)
        mock_db_account = Mock()
        mock_session.query.return_value.filter.return_value.first.return_value = (
            mock_db_account
        )
        result = postgres_db.update_account(account)
        mock_session.commit.assert_called_once()
        assert result is not None

    def test_postgres_database_update_order(self, postgres_db, mock_session):
        """Test update_order method."""
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
            filled=Decimal("0.0"),
            status=OrderStatus.OPEN,
        )
        mock_db_order = Mock()
        mock_session.query.return_value.filter.return_value.first.return_value = (
            mock_db_order
        )
        result = postgres_db.update_order(order)
        mock_session.commit.assert_called_once()
        assert result is None  # update_order returns None

    def test_postgres_database_update_transaction(self, postgres_db, mock_session):
        """Test update_transaction method."""
        transaction = Transaction(
            id=1,
            user_id=1,
            tx_hash="test_hash",
            chain="test_chain",
            confirmations=1,
            address="test_address",
            amount=Decimal("100.0"),
            asset=Asset.USDT,
            type=TransactionType.DEPOSIT,
            status=TransactionStatus.PENDING,
        )
        mock_db_transaction = Mock()
        mock_session.query.return_value.filter.return_value.first.return_value = (
            mock_db_transaction
        )
        result = postgres_db.update_transaction(transaction)
        mock_session.commit.assert_called_once()
        assert result is None  # update_transaction returns None

    def test_postgres_database_upsert_balance(self, postgres_db, mock_session):
        """Test upsert_balance method."""
        balance = Balance(
            id=1,
            account_id=1,
            asset=Asset.USDT,
            available=Decimal("100.0"),
            locked=Decimal("0.0"),
        )
        mock_existing_balance = Mock()
        mock_session.query.return_value.filter.return_value.first.return_value = (
            mock_existing_balance
        )
        result = postgres_db.upsert_balance(balance)
        mock_session.commit.assert_called_once()
        assert result is not None

    def test_postgres_database_find_balance(self, postgres_db, mock_session):
        """Test find_balance method."""
        mock_balance = Mock()
        mock_session.query.return_value.filter.return_value.first.return_value = (
            mock_balance
        )
        result = postgres_db.find_balance(1, Asset.USDT)
        assert result is not None

    def test_postgres_database_next_id(self, postgres_db, mock_session):
        """Test next_id method."""
        mock_session.execute.return_value.scalar.return_value = 1
        result = postgres_db.next_id("users")
        assert result == 1
