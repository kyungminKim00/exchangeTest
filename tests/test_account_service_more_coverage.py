"""
Additional tests for AccountService to improve coverage.
Focuses on uncovered lines and edge cases.
"""

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, Mock, patch

import pytest

from alt_exchange.core.enums import (Asset, OrderStatus, OrderType, Side,
                                     TimeInForce, TransactionStatus,
                                     TransactionType)
from alt_exchange.core.exceptions import (EntityNotFoundError,
                                          InsufficientBalanceError,
                                          InvalidOrderError, OrderLinkError,
                                          SettlementError, StopOrderError)
from alt_exchange.core.models import Account, Balance, Order, Transaction, User
from alt_exchange.infra.database.in_memory import InMemoryUnitOfWork
from alt_exchange.services.account.service import AccountService


class TestAccountServiceMoreCoverage:
    """Test AccountService methods for better coverage."""

    @pytest.fixture
    def mock_db(self):
        """Mock database."""
        db = Mock()
        db.next_id = Mock(side_effect=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        db.accounts = {}
        db.balances = {}
        db.orders = {}
        db.transactions = {}
        db.users = {}

        # Mock methods
        db.get_account = Mock()
        db.find_balance = Mock()
        db.upsert_balance = Mock()
        db.insert_order = Mock()
        db.insert_transaction = Mock()
        db.upsert_account = Mock()
        db.upsert_user = Mock()

        return db

    @pytest.fixture
    def mock_event_bus(self):
        """Mock event bus."""
        return AsyncMock()

    @pytest.fixture
    def mock_matching_engine(self):
        """Mock matching engine."""
        engine = Mock()
        engine.market = "ALT/USDT"
        return engine

    @pytest.fixture
    def account_service(self, mock_db, mock_event_bus, mock_matching_engine):
        """AccountService instance."""
        return AccountService(
            db=mock_db, event_bus=mock_event_bus, matching_engine=mock_matching_engine
        )

    def test_complete_withdrawal_transaction_not_found(self, account_service, mock_db):
        """Test complete_withdrawal when transaction not found."""
        mock_db.transactions = {}

        with pytest.raises(EntityNotFoundError, match="Transaction 1 not found"):
            account_service.complete_withdrawal(1, "hash", 1)

    def test_complete_withdrawal_invalid_transaction_type(
        self, account_service, mock_db
    ):
        """Test complete_withdrawal with invalid transaction type."""
        tx = Transaction(
            id=1,
            user_id=1,
            asset=Asset.USDT,
            amount=Decimal("100"),
            type=TransactionType.DEPOSIT,
            status=TransactionStatus.PENDING,
            tx_hash="",
            chain="",
            confirmations=0,
            address="",
        )
        mock_db.transactions = {1: tx}

        with pytest.raises(InvalidOrderError, match="Transaction is not a withdrawal"):
            account_service.complete_withdrawal(1, "hash", 1)

    def test_complete_withdrawal_insufficient_locked_balance(
        self, account_service, mock_db
    ):
        """Test complete_withdrawal with insufficient locked balance."""
        tx = Transaction(
            id=1,
            user_id=1,
            asset=Asset.USDT,
            amount=Decimal("100"),
            type=TransactionType.WITHDRAW,
            status=TransactionStatus.PENDING,
            tx_hash="",
            chain="",
            confirmations=0,
            address="",
        )
        mock_db.transactions = {1: tx}

        account = Account(id=1, user_id=1)
        mock_db.accounts = {1: account}

        balance = Balance(
            id=1,
            account_id=1,
            asset=Asset.USDT,
            available=Decimal("50"),
            locked=Decimal("50"),
        )
        mock_db.find_balance.return_value = balance

        with pytest.raises(
            SettlementError, match="Locked balance lower than withdrawal amount"
        ):
            account_service.complete_withdrawal(1, "hash", 1)

    def test_place_stop_order_account_frozen(self, account_service, mock_db):
        """Test place_stop_order with frozen account."""
        account = Account(id=1, user_id=1, frozen=True)
        mock_db.accounts = {1: account}

        with pytest.raises(InvalidOrderError, match="Account is frozen"):
            account_service.place_stop_order(
                1, Side.BUY, Decimal("100"), Decimal("1"), Decimal("95")
            )

    def test_place_stop_order_zero_amount(self, account_service, mock_db):
        """Test place_stop_order with zero amount."""
        account = Account(id=1, user_id=1, frozen=False)
        mock_db.accounts = {1: account}

        with pytest.raises(InvalidOrderError, match="Amount must be positive"):
            account_service.place_stop_order(
                1, Side.BUY, Decimal("100"), Decimal("95"), Decimal("0")
            )

    def test_place_stop_order_zero_price(self, account_service, mock_db):
        """Test place_stop_order with zero price."""
        account = Account(id=1, user_id=1, frozen=False)
        mock_db.accounts = {1: account}

        with pytest.raises(InvalidOrderError, match="Price must be positive"):
            account_service.place_stop_order(
                1, Side.BUY, Decimal("0"), Decimal("95"), Decimal("1")
            )

    def test_place_stop_order_zero_stop_price(self, account_service, mock_db):
        """Test place_stop_order with zero stop price."""
        account = Account(id=1, user_id=1, frozen=False)
        mock_db.accounts = {1: account}

        with pytest.raises(StopOrderError, match="Stop price must be positive"):
            account_service.place_stop_order(
                1, Side.BUY, Decimal("100"), Decimal("0"), Decimal("1")
            )

    def test_place_stop_order_none_stop_price(self, account_service, mock_db):
        """Test place_stop_order with None stop price."""
        account = Account(id=1, user_id=1, frozen=False)
        mock_db.accounts = {1: account}

        with pytest.raises(StopOrderError, match="Stop price must be positive"):
            account_service.place_stop_order(
                1, Side.BUY, Decimal("100"), None, Decimal("1")
            )

    def test_place_stop_order_insufficient_balance(self, account_service, mock_db):
        """Test place_stop_order with insufficient balance."""
        account = Account(id=1, user_id=1, frozen=False)
        mock_db.accounts = {1: account}

        balance = Balance(
            id=1,
            account_id=1,
            asset=Asset.USDT,
            available=Decimal("50"),
            locked=Decimal("0"),
        )
        mock_db.find_balance.return_value = balance

        with pytest.raises(
            InsufficientBalanceError, match="Insufficient available balance for order"
        ):
            account_service.place_stop_order(
                1, Side.BUY, Decimal("100"), Decimal("95"), Decimal("1")
            )

    def test_place_oco_order_account_frozen(self, account_service, mock_db):
        """Test place_oco_order with frozen account."""
        account = Account(id=1, user_id=1, frozen=True)
        mock_db.accounts = {1: account}

        with pytest.raises(InvalidOrderError, match="Account is frozen"):
            account_service.place_oco_order(
                1, Side.BUY, Decimal("100"), Decimal("1"), Decimal("95")
            )

    def test_place_oco_order_zero_amount(self, account_service, mock_db):
        """Test place_oco_order with zero amount."""
        account = Account(id=1, user_id=1, frozen=False)
        mock_db.accounts = {1: account}

        with pytest.raises(InvalidOrderError, match="Amount must be positive"):
            account_service.place_oco_order(
                1, Side.BUY, Decimal("100"), Decimal("95"), Decimal("0")
            )

    def test_place_oco_order_zero_price(self, account_service, mock_db):
        """Test place_oco_order with zero price."""
        account = Account(id=1, user_id=1, frozen=False)
        mock_db.accounts = {1: account}

        with pytest.raises(InvalidOrderError, match="Price must be positive"):
            account_service.place_oco_order(
                1, Side.BUY, Decimal("0"), Decimal("95"), Decimal("1")
            )

    def test_place_oco_order_zero_stop_price(self, account_service, mock_db):
        """Test place_oco_order with zero stop price."""
        account = Account(id=1, user_id=1, frozen=False)
        mock_db.accounts = {1: account}

        with pytest.raises(OrderLinkError, match="Stop price must be positive"):
            account_service.place_oco_order(
                1, Side.BUY, Decimal("100"), Decimal("0"), Decimal("1")
            )

    def test_place_oco_order_none_stop_price(self, account_service, mock_db):
        """Test place_oco_order with None stop price."""
        account = Account(id=1, user_id=1, frozen=False)
        mock_db.accounts = {1: account}

        with pytest.raises(OrderLinkError, match="Stop price must be positive"):
            account_service.place_oco_order(
                1, Side.BUY, Decimal("100"), None, Decimal("1")
            )

    def test_place_oco_order_insufficient_balance(self, account_service, mock_db):
        """Test place_oco_order with insufficient balance."""
        account = Account(id=1, user_id=1, frozen=False)
        mock_db.accounts = {1: account}

        balance = Balance(
            id=1,
            account_id=1,
            asset=Asset.USDT,
            available=Decimal("50"),
            locked=Decimal("0"),
        )
        mock_db.find_balance.return_value = balance

        with pytest.raises(
            InsufficientBalanceError, match="Insufficient available balance for order"
        ):
            account_service.place_oco_order(
                1, Side.BUY, Decimal("100"), Decimal("95"), Decimal("1")
            )

    def test_place_oco_order_negative_stop_price(self, account_service, mock_db):
        """Test place_oco_order with negative stop price."""
        account = Account(id=1, user_id=1, frozen=False)
        mock_db.accounts = {1: account}

        with pytest.raises(OrderLinkError, match="Stop price must be positive"):
            account_service.place_oco_order(
                1, Side.BUY, Decimal("100"), Decimal("-1"), Decimal("1")
            )

    def test_place_oco_order_negative_price(self, account_service, mock_db):
        """Test place_oco_order with negative price."""
        account = Account(id=1, user_id=1, frozen=False)
        mock_db.accounts = {1: account}

        with pytest.raises(InvalidOrderError, match="Price must be positive"):
            account_service.place_oco_order(
                1, Side.BUY, Decimal("-1"), Decimal("95"), Decimal("1")
            )
