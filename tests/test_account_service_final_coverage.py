"""
Final tests for AccountService to improve coverage to 95%.
Focus on _settle_trades, _rebalance_after_order, and other low-coverage methods.
"""

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, Mock, patch

import pytest

from alt_exchange.core.events import BalanceChanged
from alt_exchange.core.exceptions import (EntityNotFoundError,
                                          InsufficientBalanceError,
                                          InvalidOrderError, OrderLinkError,
                                          SettlementError, StopOrderError)
from alt_exchange.core.models import (Account, Asset, Balance, Order,
                                      OrderStatus, OrderType, Side,
                                      TimeInForce, Trade, Transaction,
                                      TransactionType, User)
from alt_exchange.infra.database.in_memory import InMemoryUnitOfWork
from alt_exchange.services.account.service import AccountService


class TestAccountServiceFinalCoverage:
    """Test AccountService methods for final coverage improvement."""

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
        db.update_order = Mock()
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

    def test_settle_trades_success(self, account_service, mock_db, mock_event_bus):
        """Test _settle_trades success."""
        # Setup trade
        trade = Trade(
            id=1,
            buy_order_id=1,
            sell_order_id=2,
            maker_order_id=2,
            taker_order_id=1,
            taker_side=Side.BUY,
            price=Decimal("100.0"),
            amount=Decimal("1.0"),
            fee=Decimal("0.1"),
        )

        # Setup buy order
        buy_order = Order(
            id=1,
            user_id=1,
            account_id=1,
            market="ALT/USDT",
            side=Side.BUY,
            type=OrderType.LIMIT,
            time_in_force=TimeInForce.GTC,
            price=Decimal("100.0"),
            amount=Decimal("1.0"),
            status=OrderStatus.OPEN,
        )

        # Setup sell order
        sell_order = Order(
            id=2,
            user_id=2,
            account_id=2,
            market="ALT/USDT",
            side=Side.SELL,
            type=OrderType.LIMIT,
            time_in_force=TimeInForce.GTC,
            price=Decimal("100.0"),
            amount=Decimal("1.0"),
            status=OrderStatus.OPEN,
        )

        # Setup accounts
        buy_account = Account(id=1, user_id=1)
        sell_account = Account(id=2, user_id=2)

        mock_db.orders = {1: buy_order, 2: sell_order}
        mock_db.accounts = {1: buy_account, 2: sell_account}

        # Mock _ensure_balance
        buy_quote_balance = Balance(
            id=1,
            account_id=1,
            asset=Asset.USDT,
            available=Decimal("0"),
            locked=Decimal("100.1"),
        )
        buy_base_balance = Balance(
            id=2,
            account_id=1,
            asset=Asset.ALT,
            available=Decimal("0"),
            locked=Decimal("0"),
        )
        sell_base_balance = Balance(
            id=3,
            account_id=2,
            asset=Asset.ALT,
            available=Decimal("0"),
            locked=Decimal("10.0"),
        )
        sell_quote_balance = Balance(
            id=4,
            account_id=2,
            asset=Asset.USDT,
            available=Decimal("0"),
            locked=Decimal("0"),
        )
        # Additional balances for _rebalance_after_order calls
        buy_quote_balance_rebalance = Balance(
            id=5,
            account_id=1,
            asset=Asset.USDT,
            available=Decimal("0"),
            locked=Decimal("100.1"),
        )
        sell_base_balance_rebalance = Balance(
            id=6,
            account_id=2,
            asset=Asset.ALT,
            available=Decimal("0"),
            locked=Decimal("10.0"),
        )

        with patch.object(account_service, "_ensure_balance") as mock_ensure_balance:
            mock_ensure_balance.side_effect = [
                buy_quote_balance,
                buy_base_balance,
                sell_base_balance,
                sell_quote_balance,
                buy_quote_balance_rebalance,
                sell_base_balance_rebalance,
            ]

            account_service._settle_trades([trade])

            # Verify balances were updated
            assert mock_db.upsert_balance.call_count >= 4

    def test_settle_trades_negative_locked_balance(
        self, account_service, mock_db, mock_event_bus
    ):
        """Test _settle_trades with negative locked balance."""
        # Setup trade
        trade = Trade(
            id=1,
            buy_order_id=1,
            sell_order_id=2,
            maker_order_id=2,
            taker_order_id=1,
            taker_side=Side.BUY,
            price=Decimal("100.0"),
            amount=Decimal("1.0"),
            fee=Decimal("0.1"),
        )

        # Setup buy order
        buy_order = Order(
            id=1,
            user_id=1,
            account_id=1,
            market="ALT/USDT",
            side=Side.BUY,
            type=OrderType.LIMIT,
            time_in_force=TimeInForce.GTC,
            price=Decimal("100.0"),
            amount=Decimal("1.0"),
            status=OrderStatus.OPEN,
        )

        # Setup sell order
        sell_order = Order(
            id=2,
            user_id=2,
            account_id=2,
            market="ALT/USDT",
            side=Side.SELL,
            type=OrderType.LIMIT,
            time_in_force=TimeInForce.GTC,
            price=Decimal("100.0"),
            amount=Decimal("1.0"),
            status=OrderStatus.OPEN,
        )

        # Setup accounts
        buy_account = Account(id=1, user_id=1)
        sell_account = Account(id=2, user_id=2)

        mock_db.orders = {1: buy_order, 2: sell_order}
        mock_db.accounts = {1: buy_account, 2: sell_account}

        # Mock _ensure_balance with insufficient locked balance
        buy_quote_balance = Balance(
            id=1,
            account_id=1,
            asset=Asset.USDT,
            available=Decimal("0"),
            locked=Decimal("50.0"),
        )  # Insufficient

        with patch.object(
            account_service, "_ensure_balance", return_value=buy_quote_balance
        ):
            with pytest.raises(
                SettlementError, match="Negative locked balance for buyer"
            ):
                account_service._settle_trades([trade])

    def test_rebalance_after_order_success(
        self, account_service, mock_db, mock_event_bus
    ):
        """Test _rebalance_after_order success."""
        # Setup order
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
            filled=Decimal("0.5"),
            status=OrderStatus.PARTIAL,
        )

        # Setup account
        account = Account(id=1, user_id=1)
        mock_db.accounts = {1: account}

        # Mock _ensure_balance
        balance = Balance(
            id=1,
            account_id=1,
            asset=Asset.USDT,
            available=Decimal("0"),
            locked=Decimal("100.1"),
        )

        with patch.object(account_service, "_ensure_balance", return_value=balance):
            account_service._rebalance_after_order(order)

            # Verify balance was updated
            mock_db.upsert_balance.assert_called_once()

    def test_rebalance_after_order_negative_locked(
        self, account_service, mock_db, mock_event_bus
    ):
        """Test _rebalance_after_order with negative locked balance."""
        # Setup order
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
            filled=Decimal("0.5"),
            status=OrderStatus.PARTIAL,
        )

        # Setup account
        account = Account(id=1, user_id=1)
        mock_db.accounts = {1: account}

        # Mock _ensure_balance with negative locked balance
        balance = Balance(
            id=1,
            account_id=1,
            asset=Asset.USDT,
            available=Decimal("0"),
            locked=Decimal("-10.0"),
        )

        with patch.object(account_service, "_ensure_balance", return_value=balance):
            with pytest.raises(
                SettlementError, match="Locked balance below expected level"
            ):
                account_service._rebalance_after_order(order)

    def test_expected_locked_canceled_order(self, account_service):
        """Test _expected_locked for canceled order."""
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
            filled=Decimal("0.5"),
            status=OrderStatus.CANCELED,
        )

        result = account_service._expected_locked(order)
        assert result == Decimal("0")

    def test_expected_locked_filled_order(self, account_service):
        """Test _expected_locked for filled order."""
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
            filled=Decimal("1.0"),
            status=OrderStatus.FILLED,
        )

        result = account_service._expected_locked(order)
        assert result == Decimal("0")

    def test_expected_locked_ioc_partial_order(self, account_service):
        """Test _expected_locked for IOC partial order."""
        order = Order(
            id=1,
            user_id=1,
            account_id=1,
            market="ALT/USDT",
            side=Side.BUY,
            type=OrderType.LIMIT,
            time_in_force=TimeInForce.IOC,
            price=Decimal("100.0"),
            amount=Decimal("1.0"),
            filled=Decimal("0.5"),
            status=OrderStatus.PARTIAL,
        )

        result = account_service._expected_locked(order)
        assert result == Decimal("0")

    def test_expected_locked_fok_partial_order(self, account_service):
        """Test _expected_locked for FOK partial order."""
        order = Order(
            id=1,
            user_id=1,
            account_id=1,
            market="ALT/USDT",
            side=Side.BUY,
            type=OrderType.LIMIT,
            time_in_force=TimeInForce.FOK,
            price=Decimal("100.0"),
            amount=Decimal("1.0"),
            filled=Decimal("0.5"),
            status=OrderStatus.PARTIAL,
        )

        result = account_service._expected_locked(order)
        assert result == Decimal("0")

    def test_expected_locked_gtc_partial_order(self, account_service):
        """Test _expected_locked for GTC partial order."""
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
            filled=Decimal("0.5"),
            status=OrderStatus.PARTIAL,
        )

        result = account_service._expected_locked(order)
        # For GTC partial order, should return remaining amount * price * (1 + fee_rate)
        expected = Decimal("0.5") * Decimal("100.0") * Decimal("1.001")
        assert result == expected

    def test_expected_locked_sell_order(self, account_service):
        """Test _expected_locked for sell order."""
        order = Order(
            id=1,
            user_id=1,
            account_id=1,
            market="ALT/USDT",
            side=Side.SELL,
            type=OrderType.LIMIT,
            time_in_force=TimeInForce.GTC,
            price=Decimal("100.0"),
            amount=Decimal("1.0"),
            filled=Decimal("0.5"),
            status=OrderStatus.PARTIAL,
        )

        result = account_service._expected_locked(order)
        # For sell order, should return remaining amount
        assert result == Decimal("0.5")

    def test_place_stop_order_success(
        self, account_service, mock_db, mock_matching_engine, mock_event_bus
    ):
        """Test place_stop_order success."""
        # Setup account
        account = Account(id=1, user_id=1)
        mock_db.accounts = {1: account}

        # Setup sufficient balance
        balance = Balance(
            id=1,
            account_id=1,
            asset=Asset.USDT,
            available=Decimal("1000.0"),
            locked=Decimal("0.0"),
        )
        mock_db.balances = {1: balance}

        # Mock _ensure_balance and _rebalance_after_order
        with (
            patch.object(account_service, "_ensure_balance", return_value=balance),
            patch.object(account_service, "_rebalance_after_order"),
        ):
            result = account_service.place_stop_order(
                user_id=1,
                side=Side.BUY,
                price=Decimal("100.0"),
                stop_price=Decimal("95.0"),
                amount=Decimal("1.0"),
            )

            assert result.user_id == 1
            assert result.side == Side.BUY
            assert result.type == OrderType.STOP
            assert result.price == Decimal("100.0")
            assert result.stop_price == Decimal("95.0")
            assert result.amount == Decimal("1.0")

    def test_place_oco_order_success(
        self, account_service, mock_db, mock_matching_engine, mock_event_bus
    ):
        """Test place_oco_order success."""
        # Setup account
        account = Account(id=1, user_id=1)
        mock_db.accounts = {1: account}

        # Setup sufficient balance
        balance = Balance(
            id=1,
            account_id=1,
            asset=Asset.USDT,
            available=Decimal("1000.0"),
            locked=Decimal("0.0"),
        )
        mock_db.balances = {1: balance}

        # Mock _ensure_balance and _rebalance_after_order
        with (
            patch.object(account_service, "_ensure_balance", return_value=balance),
            patch.object(account_service, "_rebalance_after_order"),
        ):
            main_order, stop_order = account_service.place_oco_order(
                user_id=1,
                side=Side.BUY,
                price=Decimal("100.0"),
                stop_price=Decimal("95.0"),
                amount=Decimal("1.0"),
            )

            assert main_order.user_id == 1
            assert main_order.side == Side.BUY
            assert main_order.type == OrderType.OCO
            assert main_order.price == Decimal("100.0")
            assert main_order.stop_price == Decimal("95.0")
            assert main_order.amount == Decimal("1.0")

            assert stop_order.user_id == 1
            assert stop_order.side == Side.BUY
            assert stop_order.type == OrderType.STOP
            assert stop_order.price == Decimal("95.0")
            assert stop_order.stop_price == Decimal("95.0")
            assert stop_order.amount == Decimal("1.0")
