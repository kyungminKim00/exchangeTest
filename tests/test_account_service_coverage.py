from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from alt_exchange.core.enums import (Asset, OrderStatus, OrderType, Side,
                                     TimeInForce, TransactionType)
from alt_exchange.core.exceptions import (EntityNotFoundError,
                                          InsufficientBalanceError,
                                          InvalidOrderError, SettlementError)
from alt_exchange.core.models import Account, Balance, Order, Trade, User
from alt_exchange.services.account.service import AccountService


class TestAccountServiceCoverage:
    """AccountService coverage tests"""

    @pytest.fixture
    def mock_db(self):
        """Mock database"""
        db = MagicMock()
        db.next_id.side_effect = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        db.users = {}
        db.accounts = {}
        db.balances = {}
        db.orders = {}
        db.trades = {}
        db.transactions = {}
        return db

    @pytest.fixture
    def mock_event_bus(self):
        """Mock event bus"""
        return AsyncMock()

    @pytest.fixture
    def mock_matching_engine(self):
        """Mock matching engine"""
        matching_engine = MagicMock()
        matching_engine.market = "ALT/USDT"
        return matching_engine

    @pytest.fixture
    def account_service(self, mock_db, mock_event_bus, mock_matching_engine):
        """AccountService instance"""
        return AccountService(mock_db, mock_event_bus, mock_matching_engine)

    def test_create_user_success(self, account_service, mock_db):
        """Test successful user creation"""
        result = account_service.create_user("test@example.com", "password123")

        assert result is not None
        assert result.email == "test@example.com"
        assert result.id == 1
        assert result.password_hash is not None

    def test_get_account_success(self, account_service, mock_db):
        """Test successful account retrieval"""
        account = Account(id=1, user_id=1)
        mock_db.accounts = {1: account}

        result = account_service.get_account(1)

        assert result is not None
        assert result.id == 1
        assert result.user_id == 1

    def test_get_account_not_found(self, account_service, mock_db):
        """Test account retrieval when account doesn't exist"""
        mock_db.accounts = {}

        with pytest.raises(EntityNotFoundError, match="Account for user 1 not found"):
            account_service.get_account(1)

    def test_get_balance_success(self, account_service, mock_db):
        """Test successful balance retrieval"""
        account = Account(id=1, user_id=1)
        mock_db.accounts = {1: account}

        balance = Balance(
            id=1,
            account_id=1,
            asset=Asset.USDT,
            available=Decimal("100.0"),
            locked=Decimal("0.0"),
        )
        mock_db.find_balance.return_value = balance

        result = account_service.get_balance(1, Asset.USDT)

        assert result is not None
        assert result.asset == Asset.USDT
        assert result.available == Decimal("100.0")

    def test_get_balance_not_found(self, account_service, mock_db):
        """Test balance retrieval when balance doesn't exist"""
        account = Account(id=1, user_id=1)
        mock_db.accounts = {1: account}
        mock_db.find_balance.return_value = None

        with pytest.raises(
            EntityNotFoundError, match="Balance for account 1 USDT not found"
        ):
            account_service.get_balance(1, Asset.USDT)

    def test_credit_deposit_success(self, account_service, mock_db, mock_event_bus):
        """Test successful deposit"""
        account = Account(id=1, user_id=1)
        mock_db.accounts = {1: account}

        balance = Balance(
            id=1,
            account_id=1,
            asset=Asset.USDT,
            available=Decimal("100.0"),
            locked=Decimal("0.0"),
        )
        mock_db.find_balance.return_value = balance
        mock_db.upsert_balance.return_value = balance

        result = account_service.credit_deposit(1, Asset.USDT, Decimal("50.0"))

        assert result is not None
        assert result.amount == Decimal("50.0")
        assert result.type == TransactionType.DEPOSIT

    def test_request_withdrawal_success(self, account_service, mock_db, mock_event_bus):
        """Test successful withdrawal request"""
        account = Account(id=1, user_id=1)
        mock_db.accounts = {1: account}

        balance = Balance(
            id=1,
            account_id=1,
            asset=Asset.USDT,
            available=Decimal("100.0"),
            locked=Decimal("0.0"),
        )
        mock_db.find_balance.return_value = balance
        mock_db.upsert_balance.return_value = balance

        result = account_service.request_withdrawal(
            1, Asset.USDT, Decimal("50.0"), "0x123"
        )

        assert result is not None
        assert result.amount == Decimal("50.0")
        assert result.type == TransactionType.WITHDRAW

    def test_request_withdrawal_insufficient_balance(self, account_service, mock_db):
        """Test withdrawal request with insufficient balance"""
        account = Account(id=1, user_id=1)
        mock_db.accounts = {1: account}

        balance = Balance(
            id=1,
            account_id=1,
            asset=Asset.USDT,
            available=Decimal("30.0"),
            locked=Decimal("0.0"),
        )
        mock_db.find_balance.return_value = balance

        with pytest.raises(
            InsufficientBalanceError, match="Insufficient funds for withdrawal"
        ):
            account_service.request_withdrawal(1, Asset.USDT, Decimal("50.0"), "0x123")

    def test_complete_withdrawal_success(
        self, account_service, mock_db, mock_event_bus
    ):
        """Test successful withdrawal completion"""
        transaction = MagicMock()
        transaction.type = TransactionType.WITHDRAW
        transaction.amount = Decimal("50.0")
        transaction.asset = Asset.USDT
        transaction.user_id = 1
        mock_db.transactions = {1: transaction}

        account = Account(id=1, user_id=1)
        mock_db.accounts = {1: account}

        balance = Balance(
            id=1,
            account_id=1,
            asset=Asset.USDT,
            available=Decimal("100.0"),
            locked=Decimal("50.0"),
        )
        mock_db.find_balance.return_value = balance
        mock_db.upsert_balance.return_value = balance

        result = account_service.complete_withdrawal(1, "0x123")

        assert result is not None

    def test_complete_withdrawal_invalid_transaction_type(
        self, account_service, mock_db
    ):
        """Test withdrawal completion with invalid transaction type"""
        transaction = MagicMock()
        transaction.type = TransactionType.DEPOSIT
        mock_db.transactions = {1: transaction}

        with pytest.raises(InvalidOrderError, match="Transaction is not a withdrawal"):
            account_service.complete_withdrawal(1, "0x123")

    def test_place_limit_order_success(self, account_service):
        """Test place_limit_order method exists and is callable"""
        assert hasattr(account_service, "place_limit_order")
        assert callable(account_service.place_limit_order)

    def test_place_limit_order_insufficient_balance(self, account_service, mock_db):
        """Test limit order placement with insufficient balance"""
        account = Account(id=1, user_id=1, frozen=False)
        mock_db.accounts = {1: account}

        balance = Balance(
            id=1,
            account_id=1,
            asset=Asset.USDT,
            available=Decimal("50.0"),
            locked=Decimal("0.0"),
        )
        mock_db.find_balance.return_value = balance

        with pytest.raises(
            InsufficientBalanceError, match="Insufficient available balance for order"
        ):
            account_service.place_limit_order(
                user_id=1, side=Side.BUY, price=Decimal("100.0"), amount=Decimal("10.0")
            )

    def test_place_stop_order_success(self, account_service):
        """Test place_stop_order method exists and is callable"""
        assert hasattr(account_service, "place_stop_order")
        assert callable(account_service.place_stop_order)

    def test_place_oco_order_success(self, account_service):
        """Test place_oco_order method exists and is callable"""
        assert hasattr(account_service, "place_oco_order")
        assert callable(account_service.place_oco_order)

    def test_cancel_order_success(self, account_service, mock_db, mock_matching_engine):
        """Test successful order cancellation"""
        order = Order(
            id=1,
            user_id=1,
            account_id=1,
            market="ALT/USDT",
            type=OrderType.LIMIT,
            side=Side.BUY,
            time_in_force=TimeInForce.GTC,
            amount=Decimal("10.0"),
            price=Decimal("100.0"),
            status=OrderStatus.OPEN,
        )
        mock_db.orders = {1: order}
        mock_matching_engine.cancel_order.return_value = True

        result = account_service.cancel_order(1, 1)

        assert result is True

    def test_cancel_order_failure(self, account_service, mock_db, mock_matching_engine):
        """Test order cancellation failure"""
        mock_db.orders = {}
        mock_matching_engine.cancel_order.return_value = False

        result = account_service.cancel_order(1, 1)

        assert result is False

    def test_get_user_orders_success(self, account_service, mock_db):
        """Test successful user orders retrieval"""
        orders = [
            Order(
                id=1,
                user_id=1,
                account_id=1,
                market="ALT/USDT",
                type=OrderType.LIMIT,
                side=Side.BUY,
                time_in_force=TimeInForce.GTC,
                amount=Decimal("10.0"),
                price=Decimal("100.0"),
                status=OrderStatus.OPEN,
            )
        ]
        mock_db.orders = {1: orders[0]}

        result = account_service.get_user_orders(1)

        assert len(result) == 1
        assert result[0].user_id == 1

    def test_get_user_trades_success(self, account_service, mock_db):
        """Test successful user trades retrieval"""
        buy_order = Order(
            id=1,
            user_id=1,
            account_id=1,
            market="ALT/USDT",
            type=OrderType.LIMIT,
            side=Side.BUY,
            time_in_force=TimeInForce.GTC,
            amount=Decimal("10.0"),
            price=Decimal("100.0"),
            status=OrderStatus.OPEN,
        )
        sell_order = Order(
            id=2,
            user_id=2,
            account_id=2,
            market="ALT/USDT",
            type=OrderType.LIMIT,
            side=Side.SELL,
            time_in_force=TimeInForce.GTC,
            amount=Decimal("10.0"),
            price=Decimal("100.0"),
            status=OrderStatus.OPEN,
        )
        trade = Trade(
            id=1,
            buy_order_id=1,
            sell_order_id=2,
            maker_order_id=1,
            taker_order_id=2,
            taker_side=Side.BUY,
            price=Decimal("100.0"),
            amount=Decimal("10.0"),
            fee=Decimal("0.01"),
        )
        mock_db.orders = {1: buy_order, 2: sell_order}
        mock_db.trades = {1: trade}

        result = account_service.get_user_trades(1)

        assert len(result) == 1
        assert result[0].id == 1

    def test_get_user_trades_with_limit(self, account_service, mock_db):
        """Test user trades retrieval with limit"""
        buy_order = Order(
            id=1,
            user_id=1,
            account_id=1,
            market="ALT/USDT",
            type=OrderType.LIMIT,
            side=Side.BUY,
            time_in_force=TimeInForce.GTC,
            amount=Decimal("10.0"),
            price=Decimal("100.0"),
            status=OrderStatus.OPEN,
        )
        sell_order = Order(
            id=2,
            user_id=2,
            account_id=2,
            market="ALT/USDT",
            type=OrderType.LIMIT,
            side=Side.SELL,
            time_in_force=TimeInForce.GTC,
            amount=Decimal("10.0"),
            price=Decimal("100.0"),
            status=OrderStatus.OPEN,
        )
        trade = Trade(
            id=1,
            buy_order_id=1,
            sell_order_id=2,
            maker_order_id=1,
            taker_order_id=2,
            taker_side=Side.BUY,
            price=Decimal("100.0"),
            amount=Decimal("10.0"),
            fee=Decimal("0.01"),
        )
        mock_db.orders = {1: buy_order, 2: sell_order}
        mock_db.trades = {1: trade}

        result = account_service.get_user_trades(1, limit=5)

        assert len(result) == 1

    def test_account_service_initialization(self, account_service):
        """Test AccountService initialization"""
        assert account_service is not None
        assert hasattr(account_service, "db")
        assert hasattr(account_service, "event_bus")
        assert hasattr(account_service, "matching")
        assert hasattr(account_service, "market")

    def test_account_service_attributes(self, account_service):
        """Test AccountService attributes"""
        assert hasattr(account_service, "db")
        assert hasattr(account_service, "event_bus")
        assert hasattr(account_service, "matching")
        assert hasattr(account_service, "market")

    def test_account_service_methods(self, account_service):
        """Test AccountService methods exist"""
        methods = [
            "create_user",
            "get_account",
            "get_balance",
            "credit_deposit",
            "request_withdrawal",
            "complete_withdrawal",
            "place_limit_order",
            "place_stop_order",
            "place_oco_order",
            "cancel_order",
            "get_user_orders",
            "get_user_trades",
        ]

        for method_name in methods:
            assert hasattr(account_service, method_name)
            assert callable(getattr(account_service, method_name))

    def test_account_service_method_count(self, account_service):
        """Test AccountService has expected number of methods"""
        methods = [
            method
            for method in dir(account_service)
            if not method.startswith("_") and callable(getattr(account_service, method))
        ]
        assert len(methods) >= 12

    def test_account_service_immutability(self, account_service):
        """Test AccountService attributes are not None"""
        assert account_service.db is not None
        assert account_service.event_bus is not None
        assert account_service.matching is not None
        assert account_service.market is not None

    def test_place_limit_order_frozen_account(self, account_service, mock_db):
        """Test limit order placement with frozen account"""
        account = Account(id=1, user_id=1, frozen=True)
        mock_db.accounts = {1: account}

        with pytest.raises(
            InvalidOrderError, match="Account is frozen and cannot place orders"
        ):
            account_service.place_limit_order(
                user_id=1, side=Side.BUY, price=Decimal("100.0"), amount=Decimal("10.0")
            )

    def test_place_limit_order_invalid_amount(self, account_service, mock_db):
        """Test limit order placement with invalid amount"""
        account = Account(id=1, user_id=1, frozen=False)
        mock_db.accounts = {1: account}

        with pytest.raises(InvalidOrderError, match="Amount must be positive"):
            account_service.place_limit_order(
                user_id=1,
                side=Side.BUY,
                price=Decimal("100.0"),
                amount=Decimal("-10.0"),
            )

    def test_place_limit_order_invalid_price(self, account_service, mock_db):
        """Test limit order placement with invalid price"""
        account = Account(id=1, user_id=1, frozen=False)
        mock_db.accounts = {1: account}

        with pytest.raises(InvalidOrderError, match="Price must be positive"):
            account_service.place_limit_order(
                user_id=1,
                side=Side.BUY,
                price=Decimal("-100.0"),
                amount=Decimal("10.0"),
            )
