"""
Additional tests for InMemoryDatabase to improve coverage
"""

from decimal import Decimal
from unittest.mock import Mock

import pytest

from alt_exchange.core.enums import (Asset, OrderStatus, OrderType, Side,
                                     TimeInForce, TransactionStatus,
                                     TransactionType)
from alt_exchange.core.models import (Account, Balance, Order, Trade,
                                      Transaction, User)
from alt_exchange.infra.database.in_memory import (InMemoryDatabase,
                                                   InMemoryUnitOfWork)


class TestInMemoryAdditional:
    """Additional tests for InMemoryDatabase"""

    @pytest.fixture
    def in_memory_db(self):
        """Create InMemoryDatabase instance"""
        return InMemoryDatabase()

    def test_in_memory_database_methods(self, in_memory_db):
        """Test InMemoryDatabase methods exist"""
        assert hasattr(in_memory_db, "get_order")
        assert hasattr(in_memory_db, "get_trade")
        assert hasattr(in_memory_db, "get_account")
        assert hasattr(in_memory_db, "find_balance")
        assert hasattr(in_memory_db, "get_transaction")
        assert hasattr(in_memory_db, "get_user")
        assert hasattr(in_memory_db, "insert_order")
        assert hasattr(in_memory_db, "insert_trade")
        assert hasattr(in_memory_db, "insert_account")
        assert hasattr(in_memory_db, "upsert_balance")
        assert hasattr(in_memory_db, "insert_transaction")
        assert hasattr(in_memory_db, "insert_user")
        assert hasattr(in_memory_db, "next_id")
        assert hasattr(in_memory_db, "clone")
        assert hasattr(in_memory_db, "restore")

    def test_in_memory_database_get_order(self, in_memory_db):
        """Test get_order method"""
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
        )
        in_memory_db.orders[1] = order
        result = in_memory_db.get_order(1)
        assert result == order

    def test_in_memory_database_get_order_not_found(self, in_memory_db):
        """Test get_order method when order not found"""
        result = in_memory_db.get_order(999)
        assert result is None

    def test_in_memory_database_get_trade(self, in_memory_db):
        """Test get_trade method"""
        trade = Trade(
            id=1,
            buy_order_id=1,
            sell_order_id=2,
            maker_order_id=1,
            taker_order_id=2,
            taker_side=Side.BUY,
            price=Decimal("100.0"),
            amount=Decimal("10.0"),
            fee=Decimal("0.1"),
        )
        in_memory_db.trades[1] = trade
        result = in_memory_db.get_trade(1)
        assert result == trade

    def test_in_memory_database_get_trade_not_found(self, in_memory_db):
        """Test get_trade method when trade not found"""
        result = in_memory_db.get_trade(999)
        assert result is None

    def test_in_memory_database_get_account(self, in_memory_db):
        """Test get_account method"""
        account = Account(id=1, user_id=1)
        in_memory_db.accounts[1] = account
        result = in_memory_db.get_account(1)
        assert result == account

    def test_in_memory_database_get_account_not_found(self, in_memory_db):
        """Test get_account method when account not found"""
        result = in_memory_db.get_account(999)
        assert result is None

    def test_in_memory_database_find_balance(self, in_memory_db):
        """Test find_balance method"""
        balance = Balance(
            id=1,
            account_id=1,
            asset=Asset.USDT,
            available=Decimal("1000.0"),
            locked=Decimal("0.0"),
        )
        in_memory_db.balances[1] = balance
        in_memory_db._balance_index[(1, Asset.USDT)] = 1
        result = in_memory_db.find_balance(1, Asset.USDT)
        assert result == balance

    def test_in_memory_database_find_balance_not_found(self, in_memory_db):
        """Test find_balance method when balance not found"""
        result = in_memory_db.find_balance(999, Asset.USDT)
        assert result is None

    def test_in_memory_database_get_transaction(self, in_memory_db):
        """Test get_transaction method"""
        transaction = Transaction(
            id=1,
            user_id=1,
            type=TransactionType.DEPOSIT,
            asset=Asset.USDT,
            amount=Decimal("100.0"),
            status=TransactionStatus.PENDING,
            tx_hash="test_hash",
            chain="test_chain",
            confirmations=1,
            address="test_address",
        )
        in_memory_db.transactions[1] = transaction
        result = in_memory_db.get_transaction(1)
        assert result == transaction

    def test_in_memory_database_get_transaction_not_found(self, in_memory_db):
        """Test get_transaction method when transaction not found"""
        result = in_memory_db.get_transaction(999)
        assert result is None

    def test_in_memory_database_get_user(self, in_memory_db):
        """Test get_user method"""
        user = User(id=1, email="test@example.com", password_hash="hash")
        in_memory_db.users[1] = user
        result = in_memory_db.get_user(1)
        assert result == user

    def test_in_memory_database_get_user_not_found(self, in_memory_db):
        """Test get_user method when user not found"""
        result = in_memory_db.get_user(999)
        assert result is None

    def test_in_memory_database_insert_order(self, in_memory_db):
        """Test insert_order method"""
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
        )
        result = in_memory_db.insert_order(order)
        assert result == order
        assert in_memory_db.orders[1] == order

    def test_in_memory_database_insert_trade(self, in_memory_db):
        """Test insert_trade method"""
        trade = Trade(
            id=1,
            buy_order_id=1,
            sell_order_id=2,
            maker_order_id=1,
            taker_order_id=2,
            taker_side=Side.BUY,
            price=Decimal("100.0"),
            amount=Decimal("10.0"),
            fee=Decimal("0.1"),
        )
        result = in_memory_db.insert_trade(trade)
        assert result == trade
        assert in_memory_db.trades[1] == trade

    def test_in_memory_database_insert_account(self, in_memory_db):
        """Test insert_account method"""
        account = Account(id=1, user_id=1)
        result = in_memory_db.insert_account(account)
        assert result == account
        assert in_memory_db.accounts[1] == account

    def test_in_memory_database_upsert_balance(self, in_memory_db):
        """Test upsert_balance method"""
        balance = Balance(
            id=1,
            account_id=1,
            asset=Asset.USDT,
            available=Decimal("1000.0"),
            locked=Decimal("0.0"),
        )
        result = in_memory_db.upsert_balance(balance)
        assert result == balance
        assert in_memory_db.balances[1] == balance
        assert in_memory_db._balance_index[(1, Asset.USDT)] == 1

    def test_in_memory_database_insert_transaction(self, in_memory_db):
        """Test insert_transaction method"""
        transaction = Transaction(
            id=1,
            user_id=1,
            type=TransactionType.DEPOSIT,
            asset=Asset.USDT,
            amount=Decimal("100.0"),
            status=TransactionStatus.PENDING,
            tx_hash="test_hash",
            chain="test_chain",
            confirmations=1,
            address="test_address",
        )
        result = in_memory_db.insert_transaction(transaction)
        assert result == transaction
        assert in_memory_db.transactions[1] == transaction

    def test_in_memory_database_insert_user(self, in_memory_db):
        """Test insert_user method"""
        user = User(id=1, email="test@example.com", password_hash="hash")
        result = in_memory_db.insert_user(user)
        assert result == user
        assert in_memory_db.users[1] == user

    def test_in_memory_database_next_id(self, in_memory_db):
        """Test next_id method"""
        id1 = in_memory_db.next_id("test_table")
        id2 = in_memory_db.next_id("test_table")
        assert id1 == 1
        assert id2 == 2

    def test_in_memory_database_clone(self, in_memory_db):
        """Test clone method"""
        # Add some data
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
        )
        in_memory_db.orders[1] = order

        # Clone database
        cloned_db = in_memory_db.clone()
        assert cloned_db.orders[1] == order
        assert cloned_db is not in_memory_db

    def test_in_memory_database_restore(self, in_memory_db):
        """Test restore method"""
        # Add some data
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
        )
        in_memory_db.orders[1] = order

        # Create snapshot
        snapshot = in_memory_db.clone()

        # Add more data
        order2 = Order(
            id=2,
            user_id=2,
            account_id=2,
            market="ALT/USDT",
            side=Side.SELL,
            type=OrderType.LIMIT,
            time_in_force=TimeInForce.GTC,
            price=Decimal("200.0"),
            amount=Decimal("5.0"),
            filled=Decimal("0.0"),
            status=OrderStatus.OPEN,
        )
        in_memory_db.orders[2] = order2

        # Restore from snapshot
        in_memory_db.restore(snapshot)
        assert 1 in in_memory_db.orders
        assert 2 not in in_memory_db.orders

    def test_in_memory_database_get_user_by_email(self, in_memory_db):
        """Test get_user_by_email method"""
        user = User(id=1, email="test@example.com", password_hash="hash")
        in_memory_db.users[1] = user
        result = in_memory_db.get_user_by_email("test@example.com")
        assert result == user

    def test_in_memory_database_get_user_by_email_not_found(self, in_memory_db):
        """Test get_user_by_email method when user not found"""
        result = in_memory_db.get_user_by_email("notfound@example.com")
        assert result is None

    def test_in_memory_database_get_accounts_by_user(self, in_memory_db):
        """Test get_accounts_by_user method"""
        account1 = Account(id=1, user_id=1)
        account2 = Account(id=2, user_id=1)
        account3 = Account(id=3, user_id=2)
        in_memory_db.accounts[1] = account1
        in_memory_db.accounts[2] = account2
        in_memory_db.accounts[3] = account3

        result = in_memory_db.get_accounts_by_user(1)
        assert len(result) == 2
        assert account1 in result
        assert account2 in result
        assert account3 not in result

    def test_in_memory_database_get_balances_by_account(self, in_memory_db):
        """Test get_balances_by_account method"""
        balance1 = Balance(id=1, account_id=1, asset=Asset.USDT)
        balance2 = Balance(id=2, account_id=1, asset=Asset.ALT)
        balance3 = Balance(id=3, account_id=2, asset=Asset.USDT)
        in_memory_db.balances[1] = balance1
        in_memory_db.balances[2] = balance2
        in_memory_db.balances[3] = balance3

        result = in_memory_db.get_balances_by_account(1)
        assert len(result) == 2
        assert balance1 in result
        assert balance2 in result
        assert balance3 not in result

    def test_in_memory_database_get_orders_by_user(self, in_memory_db):
        """Test get_orders_by_user method"""
        order1 = Order(
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
        )
        order2 = Order(
            id=2,
            user_id=1,
            account_id=1,
            market="ALT/USDT",
            side=Side.SELL,
            type=OrderType.LIMIT,
            time_in_force=TimeInForce.GTC,
            price=Decimal("200.0"),
            amount=Decimal("5.0"),
            filled=Decimal("0.0"),
            status=OrderStatus.OPEN,
        )
        order3 = Order(
            id=3,
            user_id=2,
            account_id=2,
            market="ALT/USDT",
            side=Side.BUY,
            type=OrderType.LIMIT,
            time_in_force=TimeInForce.GTC,
            price=Decimal("150.0"),
            amount=Decimal("8.0"),
            filled=Decimal("0.0"),
            status=OrderStatus.OPEN,
        )
        in_memory_db.orders[1] = order1
        in_memory_db.orders[2] = order2
        in_memory_db.orders[3] = order3

        result = in_memory_db.get_orders_by_user(1)
        assert len(result) == 2
        assert order1 in result
        assert order2 in result
        assert order3 not in result

    def test_in_memory_database_get_orders_by_account(self, in_memory_db):
        """Test get_orders_by_account method"""
        order1 = Order(
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
        )
        order2 = Order(
            id=2,
            user_id=1,
            account_id=1,
            market="ALT/USDT",
            side=Side.SELL,
            type=OrderType.LIMIT,
            time_in_force=TimeInForce.GTC,
            price=Decimal("200.0"),
            amount=Decimal("5.0"),
            filled=Decimal("0.0"),
            status=OrderStatus.OPEN,
        )
        order3 = Order(
            id=3,
            user_id=2,
            account_id=2,
            market="ALT/USDT",
            side=Side.BUY,
            type=OrderType.LIMIT,
            time_in_force=TimeInForce.GTC,
            price=Decimal("150.0"),
            amount=Decimal("8.0"),
            filled=Decimal("0.0"),
            status=OrderStatus.OPEN,
        )
        in_memory_db.orders[1] = order1
        in_memory_db.orders[2] = order2
        in_memory_db.orders[3] = order3

        result = in_memory_db.get_orders_by_account(1)
        assert len(result) == 2
        assert order1 in result
        assert order2 in result
        assert order3 not in result

    def test_in_memory_database_get_trades_by_user(self, in_memory_db):
        """Test get_trades_by_user method"""
        # Create orders first
        order1 = Order(
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
        )
        order2 = Order(
            id=2,
            user_id=2,
            account_id=2,
            market="ALT/USDT",
            side=Side.SELL,
            type=OrderType.LIMIT,
            time_in_force=TimeInForce.GTC,
            price=Decimal("100.0"),
            amount=Decimal("10.0"),
            filled=Decimal("0.0"),
            status=OrderStatus.OPEN,
        )
        order3 = Order(
            id=3,
            user_id=3,
            account_id=3,
            market="ALT/USDT",
            side=Side.BUY,
            type=OrderType.LIMIT,
            time_in_force=TimeInForce.GTC,
            price=Decimal("150.0"),
            amount=Decimal("8.0"),
            filled=Decimal("0.0"),
            status=OrderStatus.OPEN,
        )
        in_memory_db.orders[1] = order1
        in_memory_db.orders[2] = order2
        in_memory_db.orders[3] = order3

        # Create trades
        trade1 = Trade(
            id=1,
            buy_order_id=1,
            sell_order_id=2,
            maker_order_id=1,
            taker_order_id=2,
            taker_side=Side.BUY,
            price=Decimal("100.0"),
            amount=Decimal("10.0"),
            fee=Decimal("0.1"),
        )
        trade2 = Trade(
            id=2,
            buy_order_id=3,
            sell_order_id=2,
            maker_order_id=2,
            taker_order_id=3,
            taker_side=Side.BUY,
            price=Decimal("100.0"),
            amount=Decimal("5.0"),
            fee=Decimal("0.05"),
        )
        in_memory_db.trades[1] = trade1
        in_memory_db.trades[2] = trade2

        result = in_memory_db.get_trades_by_user(1)
        assert len(result) == 1
        assert trade1 in result

    def test_in_memory_database_get_transactions_by_user(self, in_memory_db):
        """Test get_transactions_by_user method"""
        transaction1 = Transaction(
            id=1,
            user_id=1,
            type=TransactionType.DEPOSIT,
            asset=Asset.USDT,
            amount=Decimal("100.0"),
            status=TransactionStatus.PENDING,
            tx_hash="test_hash1",
            chain="test_chain",
            confirmations=1,
            address="test_address1",
        )
        transaction2 = Transaction(
            id=2,
            user_id=1,
            type=TransactionType.WITHDRAW,
            asset=Asset.USDT,
            amount=Decimal("50.0"),
            status=TransactionStatus.PENDING,
            tx_hash="test_hash2",
            chain="test_chain",
            confirmations=1,
            address="test_address2",
        )
        transaction3 = Transaction(
            id=3,
            user_id=2,
            type=TransactionType.DEPOSIT,
            asset=Asset.USDT,
            amount=Decimal("200.0"),
            status=TransactionStatus.PENDING,
            tx_hash="test_hash3",
            chain="test_chain",
            confirmations=1,
            address="test_address3",
        )
        in_memory_db.transactions[1] = transaction1
        in_memory_db.transactions[2] = transaction2
        in_memory_db.transactions[3] = transaction3

        result = in_memory_db.get_transactions_by_user(1)
        assert len(result) == 2
        assert transaction1 in result
        assert transaction2 in result
        assert transaction3 not in result

    def test_in_memory_database_update_account(self, in_memory_db):
        """Test update_account method"""
        account = Account(id=1, user_id=1)
        in_memory_db.accounts[1] = account

        updated_account = Account(id=1, user_id=1, frozen=True)
        in_memory_db.update_account(updated_account)

        assert in_memory_db.accounts[1] == updated_account

    def test_in_memory_database_update_order(self, in_memory_db):
        """Test update_order method"""
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
        )
        in_memory_db.orders[1] = order

        updated_order = Order(
            id=1,
            user_id=1,
            account_id=1,
            market="ALT/USDT",
            side=Side.BUY,
            type=OrderType.LIMIT,
            time_in_force=TimeInForce.GTC,
            price=Decimal("100.0"),
            amount=Decimal("10.0"),
            filled=Decimal("5.0"),
            status=OrderStatus.PARTIAL,
        )
        in_memory_db.update_order(updated_order)

        assert in_memory_db.orders[1] == updated_order

    def test_in_memory_database_update_transaction(self, in_memory_db):
        """Test update_transaction method"""
        transaction = Transaction(
            id=1,
            user_id=1,
            type=TransactionType.DEPOSIT,
            asset=Asset.USDT,
            amount=Decimal("100.0"),
            status=TransactionStatus.PENDING,
            tx_hash="test_hash",
            chain="test_chain",
            confirmations=1,
            address="test_address",
        )
        in_memory_db.transactions[1] = transaction

        updated_transaction = Transaction(
            id=1,
            user_id=1,
            type=TransactionType.DEPOSIT,
            asset=Asset.USDT,
            amount=Decimal("100.0"),
            status=TransactionStatus.CONFIRMED,
            tx_hash="test_hash",
            chain="test_chain",
            confirmations=6,
            address="test_address",
        )
        in_memory_db.update_transaction(updated_transaction)

        assert in_memory_db.transactions[1] == updated_transaction


class TestInMemoryUnitOfWork:
    """Tests for InMemoryUnitOfWork"""

    @pytest.fixture
    def in_memory_db(self):
        """Create InMemoryDatabase instance"""
        return InMemoryDatabase()

    @pytest.fixture
    def uow(self, in_memory_db):
        """Create InMemoryUnitOfWork instance"""
        return InMemoryUnitOfWork(in_memory_db)

    def test_in_memory_unit_of_work_context_manager(self, uow):
        """Test InMemoryUnitOfWork as context manager"""
        with uow as uow_instance:
            assert uow_instance is uow
            assert uow._snapshot is not None

    def test_in_memory_unit_of_work_commit(self, uow):
        """Test commit method"""
        with uow:
            uow.commit()
            assert uow._committed is True

    def test_in_memory_unit_of_work_rollback(self, uow):
        """Test rollback method"""
        with uow:
            uow.rollback()
            assert uow._committed is True

    def test_in_memory_unit_of_work_rollback_on_exception(self, uow):
        """Test rollback on exception"""
        # Add some data to database
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
        )
        uow.db.orders[1] = order

        try:
            with uow:
                # Add more data
                order2 = Order(
                    id=2,
                    user_id=2,
                    account_id=2,
                    market="ALT/USDT",
                    side=Side.SELL,
                    type=OrderType.LIMIT,
                    time_in_force=TimeInForce.GTC,
                    price=Decimal("200.0"),
                    amount=Decimal("5.0"),
                    filled=Decimal("0.0"),
                    status=OrderStatus.OPEN,
                )
                uow.db.orders[2] = order2
                raise Exception("Test exception")
        except Exception:
            pass

        # Should be rolled back
        assert 1 in uow.db.orders
        assert 2 not in uow.db.orders
