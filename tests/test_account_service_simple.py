"""
Simple tests for AccountService to improve coverage
"""

from decimal import Decimal
from unittest.mock import AsyncMock, Mock

import pytest

from alt_exchange.core.enums import (Asset, OrderStatus, OrderType, Side,
                                     TimeInForce, TransactionStatus,
                                     TransactionType)
from alt_exchange.core.exceptions import (EntityNotFoundError,
                                          InsufficientBalanceError)
from alt_exchange.core.models import Account, Balance, Order, Transaction, User
from alt_exchange.services.account.service import AccountService


class TestAccountServiceSimple:
    """Simple tests for AccountService"""

    @pytest.fixture
    def mock_db(self):
        """Create mock database"""
        db = Mock()
        db.accounts = {}
        db.balances = {}
        db.orders = {}
        db.transactions = {}
        db.users = {}
        return db

    @pytest.fixture
    def mock_matching_engine(self):
        """Create mock matching engine"""
        engine = Mock()
        engine.market = "ALT/USDT"
        return engine

    @pytest.fixture
    def mock_event_bus(self):
        """Create mock event bus"""
        return AsyncMock()

    @pytest.fixture
    def account_service(self, mock_db, mock_matching_engine, mock_event_bus):
        """Create AccountService instance"""
        return AccountService(
            db=mock_db, matching_engine=mock_matching_engine, event_bus=mock_event_bus
        )

    def test_get_account_success(self, account_service, mock_db):
        """Test get_account method success"""
        user_id = 1
        account = Account(id=1, user_id=user_id)
        mock_db.accounts = {1: account}

        result = account_service.get_account(user_id)

        assert result == account

    def test_get_account_not_found(self, account_service, mock_db):
        """Test get_account method when account not found"""
        user_id = 1
        mock_db.accounts = {}

        with pytest.raises(EntityNotFoundError, match="Account for user 1 not found"):
            account_service.get_account(user_id)

    def test_get_balance_success(self, account_service, mock_db):
        """Test get_balance method success"""
        user_id = 1
        account = Account(id=1, user_id=user_id)
        balance = Balance(
            id=1, account_id=1, asset=Asset.USDT, available=Decimal("1000.0")
        )
        mock_db.accounts = {1: account}
        mock_db.find_balance.return_value = balance

        result = account_service.get_balance(user_id, Asset.USDT)

        assert result == balance

    def test_get_balance_not_found(self, account_service, mock_db):
        """Test get_balance method when balance not found"""
        user_id = 1
        account = Account(id=1, user_id=user_id)
        mock_db.accounts = {1: account}
        mock_db.find_balance.return_value = None

        with pytest.raises(
            EntityNotFoundError, match="Balance for account 1 USDT not found"
        ):
            account_service.get_balance(user_id, Asset.USDT)

    def test_credit_deposit_success(self, account_service, mock_db):
        """Test credit_deposit method success"""
        user_id = 1
        asset = Asset.USDT
        amount = Decimal("100.0")
        account = Account(id=1, user_id=user_id)
        balance = Balance(id=1, account_id=1, asset=asset, available=Decimal("0.0"))

        mock_db.accounts = {1: account}
        mock_db.find_balance.return_value = balance
        mock_db.next_id.return_value = 1

        result = account_service.credit_deposit(user_id, asset, amount)

        assert result.amount == amount
        assert result.user_id == user_id
        assert result.asset == asset

    def test_request_withdrawal_success(self, account_service, mock_db):
        """Test request_withdrawal method success"""
        user_id = 1
        asset = Asset.USDT
        amount = Decimal("100.0")
        address = "test_address"
        account = Account(id=1, user_id=user_id)
        balance = Balance(id=1, account_id=1, asset=asset, available=Decimal("1000.0"))

        mock_db.accounts = {1: account}
        mock_db.find_balance.return_value = balance
        mock_db.next_id.return_value = 1

        result = account_service.request_withdrawal(user_id, asset, amount, address)

        assert result.amount == amount
        assert result.user_id == user_id
        assert result.asset == asset

    def test_account_service_attributes(self, account_service):
        """Test AccountService attributes"""
        assert hasattr(account_service, "db")
        assert hasattr(account_service, "event_bus")
        assert hasattr(account_service, "matching")
        assert hasattr(account_service, "market")

    def test_account_service_methods(self, account_service):
        """Test AccountService methods exist"""
        assert hasattr(account_service, "create_user")
        assert hasattr(account_service, "get_account")
        assert hasattr(account_service, "get_balance")
        assert hasattr(account_service, "credit_deposit")
        assert hasattr(account_service, "request_withdrawal")
        assert hasattr(account_service, "complete_withdrawal")
        assert hasattr(account_service, "place_limit_order")
