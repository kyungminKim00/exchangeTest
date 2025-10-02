"""
Tests for PostgreSQLDatabase to improve coverage
"""

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock, call, patch

import pytest

from alt_exchange.core.enums import (AccountStatus, Asset, OrderStatus,
                                     OrderType, Side, TimeInForce,
                                     TransactionStatus, TransactionType)
from alt_exchange.core.models import (Account, AuditLog, Balance, Order, Trade,
                                      Transaction, User)
from alt_exchange.infra.database.postgres import (AccountModel, AuditLogModel,
                                                  BalanceModel, OrderModel,
                                                  PostgreSQLDatabase,
                                                  PostgreSQLUnitOfWork,
                                                  TradeModel, TransactionModel,
                                                  UserModel)


class TestPostgreSQLDatabaseCoverage:
    """Tests for PostgreSQLDatabase to improve coverage"""

    @pytest.fixture
    def mock_engine(self):
        """Mock SQLAlchemy engine"""
        engine = MagicMock()
        engine.connect.return_value.__enter__ = MagicMock()
        engine.connect.return_value.__exit__ = MagicMock()
        return engine

    @pytest.fixture
    def mock_session(self):
        """Mock database session"""
        session = MagicMock()
        session.add = MagicMock()
        session.flush = MagicMock()
        session.commit = MagicMock()
        session.rollback = MagicMock()
        session.close = MagicMock()
        session.query = MagicMock()
        session.execute = MagicMock()
        return session

    @pytest.fixture
    def postgres_db(self, mock_engine):
        """PostgreSQLDatabase with mocked engine"""
        with patch(
            "alt_exchange.infra.database.postgres.create_engine",
            return_value=mock_engine,
        ):
            with patch(
                "alt_exchange.infra.database.postgres.sessionmaker"
            ) as mock_sessionmaker:
                mock_sessionmaker.return_value = MagicMock()
                with patch(
                    "alt_exchange.infra.database.postgres.Base.metadata.create_all"
                ):
                    db = PostgreSQLDatabase("postgresql://test:test@localhost/test")
                    db.engine = mock_engine
                    db.SessionLocal = MagicMock()
                    return db

    def test_postgres_database_initialization(self, postgres_db):
        """Test PostgreSQLDatabase initialization"""
        assert postgres_db is not None
        assert postgres_db.engine is not None
        assert postgres_db.SessionLocal is not None

    def test_get_session_context_manager(self, postgres_db, mock_session):
        """Test get_session context manager"""
        postgres_db.SessionLocal.return_value = mock_session

        with postgres_db.get_session() as session:
            assert session == mock_session

        mock_session.commit.assert_called_once()
        mock_session.close.assert_called_once()

    def test_get_session_context_manager_with_exception(
        self, postgres_db, mock_session
    ):
        """Test get_session context manager with exception"""
        postgres_db.SessionLocal.return_value = mock_session

        with pytest.raises(Exception, match="Test error"):
            with postgres_db.get_session() as session:
                raise Exception("Test error")

        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()

    def test_next_id(self, postgres_db, mock_session):
        """Test next_id method"""
        postgres_db.SessionLocal.return_value = mock_session
        mock_session.execute.return_value.scalar.return_value = 123

        result = postgres_db.next_id("users")

        assert result == 123
        mock_session.execute.assert_called_once_with("SELECT nextval('users_id_seq')")

    def test_insert_user(self, postgres_db, mock_session):
        """Test insert_user method"""
        postgres_db.SessionLocal.return_value = mock_session

        user = User(
            id=1,
            email="test@example.com",
            password_hash="hashed_password",
            created_at=datetime.now(timezone.utc),
        )

        result = postgres_db.insert_user(user)

        assert result is not None
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()

    def test_get_user(self, postgres_db, mock_session):
        """Test get_user method"""
        postgres_db.SessionLocal.return_value = mock_session

        # Mock the query chain
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_one = MagicMock()

        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.one.return_value = mock_one

        # Mock the _user_from_model method
        mock_user = MagicMock()
        with patch.object(
            postgres_db, "_user_from_model", return_value=mock_user
        ) as mock_convert:
            result = postgres_db.get_user(1)
            assert result is not None
            mock_convert.assert_called_once_with(mock_one)

    def test_get_user_not_found(self, postgres_db, mock_session):
        """Test get_user method when user not found"""
        postgres_db.SessionLocal.return_value = mock_session

        # Mock the query chain to raise NoResultFound
        from sqlalchemy.orm.exc import NoResultFound

        mock_query = MagicMock()
        mock_filter = MagicMock()

        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.one.side_effect = NoResultFound()

        result = postgres_db.get_user(1)
        assert result is None

    def test_get_user_by_email(self, postgres_db, mock_session):
        """Test get_user_by_email method"""
        postgres_db.SessionLocal.return_value = mock_session

        # Mock the query chain
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_one = MagicMock()

        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.one.return_value = mock_one

        # Mock the _user_from_model method
        mock_user = MagicMock()
        with patch.object(
            postgres_db, "_user_from_model", return_value=mock_user
        ) as mock_convert:
            result = postgres_db.get_user_by_email("test@example.com")
            assert result is not None
            mock_convert.assert_called_once_with(mock_one)

    def test_get_user_by_email_not_found(self, postgres_db, mock_session):
        """Test get_user_by_email method when user not found"""
        postgres_db.SessionLocal.return_value = mock_session

        # Mock the query chain to raise NoResultFound
        from sqlalchemy.orm.exc import NoResultFound

        mock_query = MagicMock()
        mock_filter = MagicMock()

        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.one.side_effect = NoResultFound()

        result = postgres_db.get_user_by_email("test@example.com")
        assert result is None

    def test_insert_account(self, postgres_db, mock_session):
        """Test insert_account method"""
        postgres_db.SessionLocal.return_value = mock_session

        account = Account(id=1, user_id=1, status=AccountStatus.ACTIVE, kyc_level=1)

        result = postgres_db.insert_account(account)

        assert result is not None
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()

    def test_get_account(self, postgres_db, mock_session):
        """Test get_account method"""
        postgres_db.SessionLocal.return_value = mock_session

        # Mock the query chain
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_one = MagicMock()

        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.one.return_value = mock_one

        # Mock the _account_from_model method
        mock_account = MagicMock()
        with patch.object(
            postgres_db, "_account_from_model", return_value=mock_account
        ) as mock_convert:
            result = postgres_db.get_account(1)
            assert result is not None
            mock_convert.assert_called_once_with(mock_one)

    def test_get_accounts_by_user(self, postgres_db, mock_session):
        """Test get_accounts_by_user method"""
        postgres_db.SessionLocal.return_value = mock_session

        # Mock the query chain
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_all = MagicMock()
        mock_all.return_value = [MagicMock(), MagicMock()]

        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.all = mock_all

        # Mock the _account_from_model method
        mock_account = MagicMock()
        with patch.object(
            postgres_db, "_account_from_model", return_value=mock_account
        ) as mock_convert:
            result = postgres_db.get_accounts_by_user(1)
            assert len(result) == 2
            assert mock_convert.call_count == 2

    def test_upsert_balance_existing(self, postgres_db, mock_session):
        """Test upsert_balance method with existing balance"""
        postgres_db.SessionLocal.return_value = mock_session

        # Mock the query chain to return existing balance
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_first = MagicMock()

        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = mock_first

        balance = Balance(
            id=1,
            account_id=1,
            asset=Asset.USDT,
            available=Decimal("1000.0"),
            locked=Decimal("0.0"),
            updated_at=datetime.now(timezone.utc),
        )

        # Mock the _balance_from_model method
        mock_balance = MagicMock()
        with patch.object(
            postgres_db, "_balance_from_model", return_value=mock_balance
        ) as mock_convert:
            result = postgres_db.upsert_balance(balance)
            assert result is not None
            mock_convert.assert_called_once_with(mock_first)

    def test_upsert_balance_new(self, postgres_db, mock_session):
        """Test upsert_balance method with new balance"""
        postgres_db.SessionLocal.return_value = mock_session

        # Mock the query chain to return None (no existing balance)
        mock_query = MagicMock()
        mock_filter = MagicMock()

        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = None

        balance = Balance(
            id=1,
            account_id=1,
            asset=Asset.USDT,
            available=Decimal("1000.0"),
            locked=Decimal("0.0"),
            updated_at=datetime.now(timezone.utc),
        )

        # Mock the _balance_from_model method
        mock_balance = MagicMock()
        with patch.object(
            postgres_db, "_balance_from_model", return_value=mock_balance
        ) as mock_convert:
            result = postgres_db.upsert_balance(balance)
            assert result is not None
            mock_session.add.assert_called_once()
            mock_session.flush.assert_called_once()
            mock_convert.assert_called_once()

    def test_find_balance(self, postgres_db, mock_session):
        """Test find_balance method"""
        postgres_db.SessionLocal.return_value = mock_session

        # Mock the query chain
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_one = MagicMock()

        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.one.return_value = mock_one

        # Mock the _balance_from_model method
        mock_balance = MagicMock()
        with patch.object(
            postgres_db, "_balance_from_model", return_value=mock_balance
        ) as mock_convert:
            result = postgres_db.find_balance(1, Asset.USDT)
            assert result is not None
            mock_convert.assert_called_once_with(mock_one)

    def test_find_balance_not_found(self, postgres_db, mock_session):
        """Test find_balance method when balance not found"""
        postgres_db.SessionLocal.return_value = mock_session

        # Mock the query chain to raise NoResultFound
        from sqlalchemy.orm.exc import NoResultFound

        mock_query = MagicMock()
        mock_filter = MagicMock()

        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.one.side_effect = NoResultFound()

        result = postgres_db.find_balance(1, Asset.USDT)
        assert result is None

    def test_get_balances_by_account(self, postgres_db, mock_session):
        """Test get_balances_by_account method"""
        postgres_db.SessionLocal.return_value = mock_session

        # Mock the query chain
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_all = MagicMock()
        mock_all.return_value = [MagicMock(), MagicMock()]

        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.all = mock_all

        # Mock the _balance_from_model method
        mock_balance = MagicMock()
        with patch.object(
            postgres_db, "_balance_from_model", return_value=mock_balance
        ) as mock_convert:
            result = postgres_db.get_balances_by_account(1)
            assert len(result) == 2
            assert mock_convert.call_count == 2

    def test_insert_order(self, postgres_db, mock_session):
        """Test insert_order method"""
        postgres_db.SessionLocal.return_value = mock_session

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
            filled=Decimal("0.0"),
            status=OrderStatus.OPEN,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        result = postgres_db.insert_order(order)

        assert result is not None
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()

    def test_update_order(self, postgres_db, mock_session):
        """Test update_order method"""
        postgres_db.SessionLocal.return_value = mock_session

        # Mock the query chain
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_one = MagicMock()

        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.one.return_value = mock_one

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
            filled=Decimal("0.0"),
            status=OrderStatus.OPEN,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        postgres_db.update_order(order)

        mock_session.flush.assert_called_once()

    def test_get_order(self, postgres_db, mock_session):
        """Test get_order method"""
        postgres_db.SessionLocal.return_value = mock_session

        # Mock the query chain
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_one = MagicMock()

        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.one.return_value = mock_one

        # Mock the _order_from_model method
        mock_order = MagicMock()
        with patch.object(
            postgres_db, "_order_from_model", return_value=mock_order
        ) as mock_convert:
            result = postgres_db.get_order(1)
            assert result is not None
            mock_convert.assert_called_once_with(mock_one)

    def test_get_orders_by_user(self, postgres_db, mock_session):
        """Test get_orders_by_user method"""
        postgres_db.SessionLocal.return_value = mock_session

        # Mock the query chain
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_all = MagicMock()
        mock_all.return_value = [MagicMock(), MagicMock()]

        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.all = mock_all

        # Mock the _order_from_model method
        mock_order = MagicMock()
        with patch.object(
            postgres_db, "_order_from_model", return_value=mock_order
        ) as mock_convert:
            result = postgres_db.get_orders_by_user(1)
            assert len(result) == 2
            assert mock_convert.call_count == 2

    def test_get_orders_by_account(self, postgres_db, mock_session):
        """Test get_orders_by_account method"""
        postgres_db.SessionLocal.return_value = mock_session

        # Mock the query chain
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_all = MagicMock()
        mock_all.return_value = [MagicMock(), MagicMock()]

        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.all = mock_all

        # Mock the _order_from_model method
        mock_order = MagicMock()
        with patch.object(
            postgres_db, "_order_from_model", return_value=mock_order
        ) as mock_convert:
            result = postgres_db.get_orders_by_account(1)
            assert len(result) == 2
            assert mock_convert.call_count == 2

    def test_insert_trade(self, postgres_db, mock_session):
        """Test insert_trade method"""
        postgres_db.SessionLocal.return_value = mock_session

        trade = Trade(
            id=1,
            buy_order_id=1,
            sell_order_id=2,
            maker_order_id=1,
            taker_order_id=2,
            taker_side=Side.BUY,
            price=Decimal("100.0"),
            amount=Decimal("5.0"),
            fee=Decimal("0.1"),
            created_at=datetime.now(timezone.utc),
        )

        result = postgres_db.insert_trade(trade)

        assert result is not None
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()

    def test_get_trade(self, postgres_db, mock_session):
        """Test get_trade method"""
        postgres_db.SessionLocal.return_value = mock_session

        # Mock the query chain
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_one = MagicMock()

        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.one.return_value = mock_one

        # Mock the _trade_from_model method
        mock_trade = MagicMock()
        with patch.object(
            postgres_db, "_trade_from_model", return_value=mock_trade
        ) as mock_convert:
            result = postgres_db.get_trade(1)
            assert result is not None
            mock_convert.assert_called_once_with(mock_one)

    def test_get_trades_by_user(self, postgres_db, mock_session):
        """Test get_trades_by_user method"""
        postgres_db.SessionLocal.return_value = mock_session

        # Mock the query chain for buy orders
        mock_query1 = MagicMock()
        mock_join1 = MagicMock()
        mock_filter1 = MagicMock()
        mock_all1 = MagicMock()
        mock_all1.return_value = [MagicMock()]

        # Mock the query chain for sell orders
        mock_query2 = MagicMock()
        mock_join2 = MagicMock()
        mock_filter2 = MagicMock()
        mock_all2 = MagicMock()
        mock_all2.return_value = [MagicMock()]

        mock_session.query.side_effect = [mock_query1, mock_query2]
        mock_query1.join.return_value = mock_join1
        mock_join1.filter.return_value = mock_filter1
        mock_filter1.all = mock_all1

        mock_query2.join.return_value = mock_join2
        mock_join2.filter.return_value = mock_filter2
        mock_filter2.all = mock_all2

        # Mock the _trade_from_model method
        mock_trade = MagicMock()
        with patch.object(
            postgres_db, "_trade_from_model", return_value=mock_trade
        ) as mock_convert:
            result = postgres_db.get_trades_by_user(1)
            assert len(result) == 2
            assert mock_convert.call_count == 2

    def test_insert_transaction(self, postgres_db, mock_session):
        """Test insert_transaction method"""
        postgres_db.SessionLocal.return_value = mock_session

        transaction = Transaction(
            id=1,
            user_id=1,
            tx_hash="0x123",
            chain="ethereum",
            asset=Asset.USDT,
            type=TransactionType.DEPOSIT,
            status=TransactionStatus.PENDING,
            confirmations=0,
            amount=Decimal("1000.0"),
            address="0xabc",
            created_at=datetime.now(timezone.utc),
        )

        result = postgres_db.insert_transaction(transaction)

        assert result is not None
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()

    def test_update_transaction(self, postgres_db, mock_session):
        """Test update_transaction method"""
        postgres_db.SessionLocal.return_value = mock_session

        # Mock the query chain
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_one = MagicMock()

        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.one.return_value = mock_one

        transaction = Transaction(
            id=1,
            user_id=1,
            tx_hash="0x123",
            chain="ethereum",
            asset=Asset.USDT,
            type=TransactionType.DEPOSIT,
            status=TransactionStatus.PENDING,
            confirmations=0,
            amount=Decimal("1000.0"),
            address="0xabc",
            created_at=datetime.now(timezone.utc),
        )

        postgres_db.update_transaction(transaction)

        mock_session.flush.assert_called_once()

    def test_get_transaction(self, postgres_db, mock_session):
        """Test get_transaction method"""
        postgres_db.SessionLocal.return_value = mock_session

        # Mock the query chain
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_one = MagicMock()

        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.one.return_value = mock_one

        # Mock the _transaction_from_model method
        mock_transaction = MagicMock()
        with patch.object(
            postgres_db, "_transaction_from_model", return_value=mock_transaction
        ) as mock_convert:
            result = postgres_db.get_transaction(1)
            assert result is not None
            mock_convert.assert_called_once_with(mock_one)

    def test_get_transactions_by_user(self, postgres_db, mock_session):
        """Test get_transactions_by_user method"""
        postgres_db.SessionLocal.return_value = mock_session

        # Mock the query chain
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_all = MagicMock()
        mock_all.return_value = [MagicMock(), MagicMock()]

        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.all = mock_all

        # Mock the _transaction_from_model method
        mock_transaction = MagicMock()
        with patch.object(
            postgres_db, "_transaction_from_model", return_value=mock_transaction
        ) as mock_convert:
            result = postgres_db.get_transactions_by_user(1)
            assert len(result) == 2
            assert mock_convert.call_count == 2

    def test_insert_audit(self, postgres_db, mock_session):
        """Test insert_audit method"""
        postgres_db.SessionLocal.return_value = mock_session

        audit_log = AuditLog(
            id=1,
            actor="user123",
            action="LOGIN",
            entity="User",
            metadata={"ip": "192.168.1.1"},
            created_at=datetime.now(timezone.utc),
        )

        result = postgres_db.insert_audit(audit_log)

        assert result is not None
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()

    def test_get_audit_logs(self, postgres_db, mock_session):
        """Test get_audit_logs method"""
        postgres_db.SessionLocal.return_value = mock_session

        # Mock the query chain
        mock_query = MagicMock()
        mock_order_by = MagicMock()
        mock_limit = MagicMock()
        mock_all = MagicMock()
        mock_all.return_value = [MagicMock(), MagicMock()]

        mock_session.query.return_value = mock_query
        mock_query.order_by.return_value = mock_order_by
        mock_order_by.limit.return_value = mock_limit
        mock_limit.all = mock_all

        # Mock the _audit_from_model method
        mock_audit_log = MagicMock()
        with patch.object(
            postgres_db, "_audit_from_model", return_value=mock_audit_log
        ) as mock_convert:
            result = postgres_db.get_audit_logs(limit=10)
            assert len(result) == 2
            assert mock_convert.call_count == 2

    def test_model_conversion_methods(self, postgres_db):
        """Test model conversion methods"""
        # Test _user_from_model
        user_model = MagicMock()
        user_model.id = 1
        user_model.email = "test@example.com"
        user_model.password_hash = "hash"
        user_model.created_at = datetime.now(timezone.utc)
        user_model.last_login = None

        user = postgres_db._user_from_model(user_model)
        assert user.id == 1
        assert user.email == "test@example.com"

        # Test _account_from_model
        account_model = MagicMock()
        account_model.id = 1
        account_model.user_id = 1
        account_model.status = AccountStatus.ACTIVE
        account_model.kyc_level = 1

        account = postgres_db._account_from_model(account_model)
        assert account.id == 1
        assert account.user_id == 1

        # Test _balance_from_model
        balance_model = MagicMock()
        balance_model.id = 1
        balance_model.account_id = 1
        balance_model.asset = Asset.USDT
        balance_model.available = Decimal("1000.0")
        balance_model.locked = Decimal("0.0")
        balance_model.updated_at = datetime.now(timezone.utc)

        balance = postgres_db._balance_from_model(balance_model)
        assert balance.id == 1
        assert balance.account_id == 1

        # Test _order_from_model
        order_model = MagicMock()
        order_model.id = 1
        order_model.user_id = 1
        order_model.account_id = 1
        order_model.market = "ALT/USDT"
        order_model.side = Side.BUY
        order_model.type = OrderType.LIMIT
        order_model.time_in_force = TimeInForce.GTC
        order_model.price = Decimal("100.0")
        order_model.amount = Decimal("10.0")
        order_model.filled = Decimal("0.0")
        order_model.status = OrderStatus.OPEN
        order_model.created_at = datetime.now(timezone.utc)
        order_model.updated_at = datetime.now(timezone.utc)

        order = postgres_db._order_from_model(order_model)
        assert order.id == 1
        assert order.user_id == 1

        # Test _trade_from_model
        trade_model = MagicMock()
        trade_model.id = 1
        trade_model.buy_order_id = 1
        trade_model.sell_order_id = 2
        trade_model.maker_order_id = 1
        trade_model.taker_order_id = 2
        trade_model.taker_side = Side.BUY
        trade_model.price = Decimal("100.0")
        trade_model.amount = Decimal("5.0")
        trade_model.fee = Decimal("0.1")
        trade_model.created_at = datetime.now(timezone.utc)

        trade = postgres_db._trade_from_model(trade_model)
        assert trade.id == 1
        assert trade.buy_order_id == 1

        # Test _transaction_from_model
        transaction_model = MagicMock()
        transaction_model.id = 1
        transaction_model.user_id = 1
        transaction_model.tx_hash = "0x123"
        transaction_model.chain = "ethereum"
        transaction_model.asset = Asset.USDT
        transaction_model.type = TransactionType.DEPOSIT
        transaction_model.status = TransactionStatus.PENDING
        transaction_model.confirmations = 0
        transaction_model.amount = Decimal("1000.0")
        transaction_model.address = "0xabc"
        transaction_model.created_at = datetime.now(timezone.utc)

        transaction = postgres_db._transaction_from_model(transaction_model)
        assert transaction.id == 1
        assert transaction.user_id == 1

        # Test _audit_from_model
        audit_model = MagicMock()
        audit_model.id = 1
        audit_model.actor = "user123"
        audit_model.action = "LOGIN"
        audit_model.entity = "User"
        audit_model.metadata_json = '{"ip": "192.168.1.1"}'
        audit_model.created_at = datetime.now(timezone.utc)

        audit = postgres_db._audit_from_model(audit_model)
        assert audit.id == 1
        assert audit.actor == "user123"

    def test_audit_from_model_empty_metadata(self, postgres_db):
        """Test _audit_from_model with empty metadata"""
        audit_model = MagicMock()
        audit_model.id = 1
        audit_model.actor = "user123"
        audit_model.action = "LOGIN"
        audit_model.entity = "User"
        audit_model.metadata_json = None
        audit_model.created_at = datetime.now(timezone.utc)

        audit = postgres_db._audit_from_model(audit_model)
        assert audit.id == 1
        assert audit.metadata == {}


class TestPostgreSQLUnitOfWorkCoverage:
    """Tests for PostgreSQLUnitOfWork to improve coverage"""

    @pytest.fixture
    def mock_db(self):
        """Mock PostgreSQLDatabase"""
        return MagicMock()

    @pytest.fixture
    def mock_session(self):
        """Mock database session"""
        session = MagicMock()
        session.commit = MagicMock()
        session.rollback = MagicMock()
        session.close = MagicMock()
        return session

    @pytest.fixture
    def uow(self, mock_db):
        """PostgreSQLUnitOfWork instance"""
        return PostgreSQLUnitOfWork(mock_db)

    def test_unit_of_work_initialization(self, uow, mock_db):
        """Test PostgreSQLUnitOfWork initialization"""
        assert uow.db == mock_db
        assert uow.session is None

    def test_unit_of_work_enter(self, uow, mock_db, mock_session):
        """Test PostgreSQLUnitOfWork context manager enter"""
        mock_db.SessionLocal.return_value = mock_session

        with uow as uow_context:
            assert uow_context == uow
            assert uow.session == mock_session

    def test_unit_of_work_exit_success(self, uow, mock_db, mock_session):
        """Test PostgreSQLUnitOfWork context manager exit on success"""
        mock_db.SessionLocal.return_value = mock_session

        with uow:
            pass

        mock_session.commit.assert_called_once()
        mock_session.close.assert_called_once()
        assert uow.session is None

    def test_unit_of_work_exit_with_exception(self, uow, mock_db, mock_session):
        """Test PostgreSQLUnitOfWork context manager exit with exception"""
        mock_db.SessionLocal.return_value = mock_session

        with pytest.raises(Exception, match="Test error"):
            with uow:
                raise Exception("Test error")

        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()
        assert uow.session is None

    def test_unit_of_work_commit(self, uow, mock_db, mock_session):
        """Test PostgreSQLUnitOfWork commit"""
        mock_db.SessionLocal.return_value = mock_session

        with uow:
            uow.commit()
            mock_session.commit.assert_called_once()

    def test_unit_of_work_rollback(self, uow, mock_db, mock_session):
        """Test PostgreSQLUnitOfWork rollback"""
        mock_db.SessionLocal.return_value = mock_session

        with uow:
            uow.rollback()
            mock_session.rollback.assert_called_once()

    def test_unit_of_work_commit_without_session(self, uow):
        """Test PostgreSQLUnitOfWork commit without session"""
        uow.commit()  # Should not raise exception

    def test_unit_of_work_rollback_without_session(self, uow):
        """Test PostgreSQLUnitOfWork rollback without session"""
        uow.rollback()  # Should not raise exception
