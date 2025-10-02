"""
Additional tests for AccountService methods to improve coverage.
Focus on _settle_trades, _rebalance_after_order, _release_locked_funds, and other low-coverage methods.
"""

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, Mock, patch

import pytest

from alt_exchange.core.events import BalanceChanged
from alt_exchange.core.exceptions import (EntityNotFoundError,
                                          InsufficientBalanceError,
                                          InvalidOrderError, OrderLinkError,
                                          StopOrderError)
from alt_exchange.core.models import (Account, Asset, Balance, Order,
                                      OrderStatus, OrderType, Side,
                                      TimeInForce, Trade, Transaction,
                                      TransactionType, User)
from alt_exchange.infra.database.in_memory import InMemoryUnitOfWork
from alt_exchange.services.account.service import AccountService


class TestAccountServiceAdditionalMethods:
    """Test additional AccountService methods for better coverage."""

    @pytest.fixture
    def mock_db(self):
        """Mock database."""
        db = Mock()
        db.next_id = Mock(side_effect=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        db.orders = {}
        db.accounts = {}
        db.balances = {}
        db.users = {}
        db.trades = {}
        db.transactions = {}
        db.upsert_balance = Mock()
        db.insert_order = Mock()
        db.insert_trade = Mock()
        db.insert_transaction = Mock()
        return db

    @pytest.fixture
    def mock_matching_engine(self):
        """Mock matching engine."""
        engine = Mock()
        engine.market = "ALT/USDT"
        engine.submit = Mock(return_value=[])
        engine.cancel_order = Mock(return_value=True)
        return engine

    @pytest.fixture
    def mock_event_bus(self):
        """Mock event bus."""
        return AsyncMock()

    @pytest.fixture
    def account_service(self, mock_db, mock_matching_engine, mock_event_bus):
        """AccountService instance with mocked dependencies."""
        return AccountService(
            db=mock_db, event_bus=mock_event_bus, matching_engine=mock_matching_engine
        )

    def test_release_locked_funds_buy_order(self, account_service, mock_db):
        """Test _release_locked_funds for buy order."""
        # Setup
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
            status=OrderStatus.PARTIAL,
        )

        balance = Balance(
            id=1,
            account_id=1,
            asset=Asset.USDT,
            available=Decimal("500.0"),
            locked=Decimal("700.0"),
        )
        mock_db.balances = {1: balance}

        # Mock _ensure_balance to return the balance
        with patch.object(account_service, "_ensure_balance", return_value=balance):
            account_service._release_locked_funds(order)

        # Verify balance was updated
        mock_db.upsert_balance.assert_called_once()
        updated_balance = mock_db.upsert_balance.call_args[0][0]
        assert updated_balance.asset == Asset.USDT
        # For buy order: remaining = 7.0, price = 100.0, fee_rate = 0.001
        # Locked amount = 7.0 * 100.0 * 1.001 = 700.7
        # New locked = 700.0 - 700.7 = -0.7
        assert updated_balance.locked == Decimal("-0.7")
        # Available should increase by the released amount (700.7)
        assert updated_balance.available == Decimal("1200.7")

    def test_release_locked_funds_sell_order(self, account_service, mock_db):
        """Test _release_locked_funds for sell order."""
        # Setup
        order = Order(
            id=1,
            user_id=1,
            account_id=1,
            market="ALT/USDT",
            side=Side.SELL,
            type=OrderType.LIMIT,
            time_in_force=TimeInForce.GTC,
            price=Decimal("100.0"),
            amount=Decimal("10.0"),
            filled=Decimal("3.0"),
            status=OrderStatus.PARTIAL,
        )

        balance = Balance(
            id=1,
            account_id=1,
            asset=Asset.ALT,
            available=Decimal("50.0"),
            locked=Decimal("7.0"),
        )
        mock_db.balances = {1: balance}

        # Mock _ensure_balance to return the balance
        with patch.object(account_service, "_ensure_balance", return_value=balance):
            account_service._release_locked_funds(order)

        # Verify balance was updated
        mock_db.upsert_balance.assert_called_once()
        updated_balance = mock_db.upsert_balance.call_args[0][0]
        assert updated_balance.asset == Asset.ALT
        # For sell order: remaining = 7.0
        # New locked = 7.0 - 7.0 = 0
        assert updated_balance.locked == Decimal("0")
        # Available should increase by the released amount (7.0)
        assert updated_balance.available == Decimal("57.0")

    def test_cancel_order_success(self, account_service, mock_db, mock_matching_engine):
        """Test cancel_order success."""
        # Setup
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
            status=OrderStatus.OPEN,
        )
        mock_db.orders = {1: order}
        mock_matching_engine.cancel_order.return_value = True

        # Mock _release_locked_funds
        with patch.object(account_service, "_release_locked_funds"):
            result = account_service.cancel_order(1, 1)

        assert result is True
        mock_matching_engine.cancel_order.assert_called_once_with(1)

    def test_cancel_order_not_found(self, account_service, mock_db):
        """Test cancel_order when order not found."""
        mock_db.orders = {}

        result = account_service.cancel_order(1, 1)
        assert result is False

    def test_cancel_order_wrong_user(self, account_service, mock_db):
        """Test cancel_order when order belongs to different user."""
        order = Order(
            id=1,
            user_id=2,  # Different user
            account_id=1,
            market="ALT/USDT",
            side=Side.BUY,
            type=OrderType.LIMIT,
            time_in_force=TimeInForce.GTC,
            price=Decimal("100.0"),
            amount=Decimal("10.0"),
            status=OrderStatus.OPEN,
        )
        mock_db.orders = {1: order}

        result = account_service.cancel_order(1, 1)
        assert result is False

    def test_cancel_order_not_cancellable_status(self, account_service, mock_db):
        """Test cancel_order when order status is not cancellable."""
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
            status=OrderStatus.FILLED,  # Not cancellable
        )
        mock_db.orders = {1: order}

        result = account_service.cancel_order(1, 1)
        assert result is False

    def test_cancel_order_matching_engine_failure(
        self, account_service, mock_db, mock_matching_engine
    ):
        """Test cancel_order when matching engine fails."""
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
            status=OrderStatus.OPEN,
        )
        mock_db.orders = {1: order}
        mock_matching_engine.cancel_order.return_value = False

        result = account_service.cancel_order(1, 1)
        assert result is False

    def test_place_stop_order_insufficient_balance(self, account_service, mock_db):
        """Test place_stop_order with insufficient balance."""
        # Setup account
        account = Account(id=1, user_id=1)
        mock_db.accounts = {1: account}

        # Setup insufficient balance
        balance = Balance(
            id=1,
            account_id=1,
            asset=Asset.USDT,
            available=Decimal("50.0"),  # Insufficient
            locked=Decimal("0.0"),
        )
        mock_db.balances = {1: balance}

        # Mock _ensure_balance
        with patch.object(account_service, "_ensure_balance", return_value=balance):
            with pytest.raises(InsufficientBalanceError):
                account_service.place_stop_order(
                    user_id=1,
                    side=Side.BUY,
                    price=Decimal("100.0"),
                    stop_price=Decimal("90.0"),
                    amount=Decimal("1.0"),
                )

    def test_place_stop_order_frozen_account(self, account_service, mock_db):
        """Test place_stop_order with frozen account."""
        # Setup frozen account
        account = Account(id=1, user_id=1, frozen=True)
        mock_db.accounts = {1: account}

        with pytest.raises(InvalidOrderError, match="Account is frozen"):
            account_service.place_stop_order(
                user_id=1,
                side=Side.BUY,
                price=Decimal("100.0"),
                stop_price=Decimal("90.0"),
                amount=Decimal("1.0"),
            )

    def test_place_stop_order_invalid_amount(self, account_service, mock_db):
        """Test place_stop_order with invalid amount."""
        # Setup account
        account = Account(id=1, user_id=1)
        mock_db.accounts = {1: account}

        with pytest.raises(InvalidOrderError, match="Amount must be positive"):
            account_service.place_stop_order(
                user_id=1,
                side=Side.BUY,
                price=Decimal("100.0"),
                stop_price=Decimal("90.0"),
                amount=Decimal("0.0"),  # Invalid
            )

    def test_place_stop_order_invalid_price(self, account_service, mock_db):
        """Test place_stop_order with invalid price."""
        # Setup account
        account = Account(id=1, user_id=1)
        mock_db.accounts = {1: account}

        with pytest.raises(InvalidOrderError, match="Price must be positive"):
            account_service.place_stop_order(
                user_id=1,
                side=Side.BUY,
                price=Decimal("0.0"),  # Invalid
                stop_price=Decimal("90.0"),
                amount=Decimal("1.0"),
            )

    def test_place_stop_order_invalid_stop_price(self, account_service, mock_db):
        """Test place_stop_order with invalid stop price."""
        # Setup account
        account = Account(id=1, user_id=1)
        mock_db.accounts = {1: account}

        with pytest.raises(StopOrderError, match="Stop price must be positive"):
            account_service.place_stop_order(
                user_id=1,
                side=Side.BUY,
                price=Decimal("100.0"),
                stop_price=Decimal("0.0"),  # Invalid
                amount=Decimal("1.0"),
            )

    def test_place_oco_order_insufficient_balance(self, account_service, mock_db):
        """Test place_oco_order with insufficient balance."""
        # Setup account
        account = Account(id=1, user_id=1)
        mock_db.accounts = {1: account}

        # Setup insufficient balance
        balance = Balance(
            id=1,
            account_id=1,
            asset=Asset.USDT,
            available=Decimal("50.0"),  # Insufficient
            locked=Decimal("0.0"),
        )
        mock_db.balances = {1: balance}

        # Mock _ensure_balance
        with patch.object(account_service, "_ensure_balance", return_value=balance):
            with pytest.raises(InsufficientBalanceError):
                account_service.place_oco_order(
                    user_id=1,
                    side=Side.BUY,
                    price=Decimal("100.0"),
                    stop_price=Decimal("90.0"),
                    amount=Decimal("1.0"),
                )

    def test_place_oco_order_frozen_account(self, account_service, mock_db):
        """Test place_oco_order with frozen account."""
        # Setup frozen account
        account = Account(id=1, user_id=1, frozen=True)
        mock_db.accounts = {1: account}

        with pytest.raises(InvalidOrderError, match="Account is frozen"):
            account_service.place_oco_order(
                user_id=1,
                side=Side.BUY,
                price=Decimal("100.0"),
                stop_price=Decimal("90.0"),
                amount=Decimal("1.0"),
            )

    def test_place_oco_order_invalid_amount(self, account_service, mock_db):
        """Test place_oco_order with invalid amount."""
        # Setup account
        account = Account(id=1, user_id=1)
        mock_db.accounts = {1: account}

        with pytest.raises(InvalidOrderError, match="Amount must be positive"):
            account_service.place_oco_order(
                user_id=1,
                side=Side.BUY,
                price=Decimal("100.0"),
                stop_price=Decimal("90.0"),
                amount=Decimal("0.0"),  # Invalid
            )

    def test_place_oco_order_invalid_price(self, account_service, mock_db):
        """Test place_oco_order with invalid price."""
        # Setup account
        account = Account(id=1, user_id=1)
        mock_db.accounts = {1: account}

        with pytest.raises(InvalidOrderError, match="Price must be positive"):
            account_service.place_oco_order(
                user_id=1,
                side=Side.BUY,
                price=Decimal("0.0"),  # Invalid
                stop_price=Decimal("90.0"),
                amount=Decimal("1.0"),
            )

    def test_place_oco_order_invalid_stop_price(self, account_service, mock_db):
        """Test place_oco_order with invalid stop price."""
        # Setup account
        account = Account(id=1, user_id=1)
        mock_db.accounts = {1: account}

        with pytest.raises(OrderLinkError, match="Stop price must be positive"):
            account_service.place_oco_order(
                user_id=1,
                side=Side.BUY,
                price=Decimal("100.0"),
                stop_price=Decimal("0.0"),  # Invalid
                amount=Decimal("1.0"),
            )

    def test_get_account_not_found(self, account_service, mock_db):
        """Test get_account when account not found."""
        mock_db.accounts = {}

        with pytest.raises(EntityNotFoundError, match="Account for user 1 not found"):
            account_service.get_account(1)

    def test_get_balance_not_found(self, account_service, mock_db):
        """Test get_balance when balance not found."""
        mock_db.balances = {}

        with pytest.raises(EntityNotFoundError, match="Account for user 1 not found"):
            account_service.get_balance(1, Asset.USDT)

    def test_ensure_balance_existing(self, account_service, mock_db):
        """Test _ensure_balance when balance already exists."""
        balance = Balance(
            id=1,
            account_id=1,
            asset=Asset.USDT,
            available=Decimal("100.0"),
            locked=Decimal("0.0"),
        )
        mock_db.find_balance.return_value = balance

        result = account_service._ensure_balance(1, Asset.USDT)
        assert result == balance
        mock_db.find_balance.assert_called_once_with(1, Asset.USDT)

    def test_ensure_balance_new(self, account_service, mock_db):
        """Test _ensure_balance when creating new balance."""
        mock_db.find_balance.return_value = None
        mock_db.next_id.return_value = 1

        result = account_service._ensure_balance(1, Asset.USDT)

        assert result.account_id == 1
        assert result.asset == Asset.USDT
        assert result.available == Decimal("0")
        assert result.locked == Decimal("0")
        mock_db.upsert_balance.assert_called_once()
        mock_db.find_balance.assert_called_once_with(1, Asset.USDT)

    def test_lock_required_buy(self, account_service):
        """Test _lock_required for buy order."""
        result = account_service._lock_required(
            Side.BUY, Decimal("100.0"), Decimal("1.0")
        )
        expected = Decimal("100.1")  # price * amount * (1 + FEE_RATE)
        assert result == expected

    def test_lock_required_sell(self, account_service):
        """Test _lock_required for sell order."""
        result = account_service._lock_required(
            Side.SELL, Decimal("100.0"), Decimal("1.0")
        )
        expected = Decimal("1.0")  # just amount for sell
        assert result == expected
