from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from alt_exchange.core.enums import (AccountStatus, Asset, TransactionStatus,
                                     TransactionType)
from alt_exchange.core.exceptions import (AdminPermissionError,
                                          EntityNotFoundError,
                                          WithdrawalApprovalError)
from alt_exchange.core.models import (Account, AuditLog, Balance, Transaction,
                                      User)
from alt_exchange.services.admin.service import AdminService


class TestAdminServiceExtended:
    """Extended tests for AdminService"""

    @pytest.fixture
    def mock_db(self):
        """Mock database"""
        db = MagicMock()
        db.next_id.return_value = 1
        db.transactions = {}
        db.accounts = {}
        db.users = {}
        db.balances = {}
        db.audit_logs = {}
        db.trades = {}
        return db

    @pytest.fixture
    def mock_event_bus(self):
        """Mock event bus"""
        return MagicMock()

    @pytest.fixture
    def mock_account_service(self):
        """Mock account service"""
        account_service = MagicMock()
        account_service.market = "ALT/USDT"
        account_service.matching = MagicMock()
        account_service.matching.order_book_snapshot.return_value = (
            [(Decimal("1.0"), Decimal("10.0"))],
            [(Decimal("1.1"), Decimal("5.0"))],
        )
        account_service.matching.stop_orders = {}
        account_service.matching.oco_pairs = {}
        return account_service

    @pytest.fixture
    def mock_wallet_service(self):
        """Mock wallet service"""
        return MagicMock()

    @pytest.fixture
    def admin_service(
        self, mock_db, mock_event_bus, mock_account_service, mock_wallet_service
    ):
        """AdminService instance"""
        return AdminService(
            db=mock_db,
            event_bus=mock_event_bus,
            account_service=mock_account_service,
            wallet_service=mock_wallet_service,
        )

    def test_admin_service_initialization(self, admin_service):
        """Test AdminService initialization"""
        assert admin_service is not None
        assert hasattr(admin_service, "db")
        assert hasattr(admin_service, "event_bus")
        assert hasattr(admin_service, "account_service")
        assert hasattr(admin_service, "wallet_service")
        assert hasattr(admin_service, "withdrawal_approvals")

    def test_is_admin_admin_user(self, admin_service):
        """Test _is_admin with admin user"""
        assert admin_service._is_admin(50) is True
        assert admin_service._is_admin(99) is True

    def test_is_admin_regular_user(self, admin_service):
        """Test _is_admin with regular user"""
        assert admin_service._is_admin(100) is False
        assert admin_service._is_admin(200) is False

    def test_log_admin_action(self, admin_service, mock_db):
        """Test _log_admin_action"""
        admin_service._log_admin_action(
            admin_id=1,
            action="test_action",
            entity_type="test_entity",
            entity_id=123,
            metadata={"key": "value"},
        )
        mock_db.insert_audit_log.assert_called_once()

    def test_list_pending_withdrawals_admin_permission_error(self, admin_service):
        """Test list_pending_withdrawals with non-admin user"""
        with pytest.raises(AdminPermissionError, match="Insufficient permissions"):
            admin_service.list_pending_withdrawals(admin_id=200)

    def test_list_pending_withdrawals_success(self, admin_service, mock_db):
        """Test list_pending_withdrawals success"""
        # Create mock transactions
        tx1 = Transaction(
            id=1,
            user_id=1,
            tx_hash=None,
            chain="ethereum",
            type=TransactionType.WITHDRAW,
            status=TransactionStatus.PENDING,
            confirmations=0,
            asset=Asset.USDT,
            amount=Decimal("100.0"),
            address="test_address",
        )
        tx2 = Transaction(
            id=2,
            user_id=2,
            tx_hash=None,
            chain="ethereum",
            type=TransactionType.DEPOSIT,
            status=TransactionStatus.PENDING,
            confirmations=0,
            asset=Asset.USDT,
            amount=Decimal("50.0"),
            address="test_address",
        )
        mock_db.transactions = {1: tx1, 2: tx2}

        result = admin_service.list_pending_withdrawals(admin_id=1)
        assert len(result) == 1
        assert result[0].id == 1
        assert result[0].type == TransactionType.WITHDRAW

    def test_approve_withdrawal_admin_permission_error(self, admin_service):
        """Test approve_withdrawal with non-admin user"""
        with pytest.raises(AdminPermissionError, match="Insufficient permissions"):
            admin_service.approve_withdrawal(admin_id=200, tx_id=1)

    def test_approve_withdrawal_transaction_not_found(self, admin_service, mock_db):
        """Test approve_withdrawal with non-existent transaction"""
        mock_db.transactions = {}
        with pytest.raises(EntityNotFoundError, match="Transaction 1 not found"):
            admin_service.approve_withdrawal(admin_id=1, tx_id=1)

    def test_approve_withdrawal_not_withdrawal(self, admin_service, mock_db):
        """Test approve_withdrawal with non-withdrawal transaction"""
        tx = Transaction(
            id=1,
            user_id=1,
            tx_hash=None,
            chain="ethereum",
            type=TransactionType.DEPOSIT,
            status=TransactionStatus.PENDING,
            confirmations=0,
            asset=Asset.USDT,
            amount=Decimal("100.0"),
            address="test_address",
        )
        mock_db.transactions = {1: tx}
        with pytest.raises(
            WithdrawalApprovalError, match="Transaction is not a withdrawal"
        ):
            admin_service.approve_withdrawal(admin_id=1, tx_id=1)

    def test_approve_withdrawal_not_pending(self, admin_service, mock_db):
        """Test approve_withdrawal with non-pending transaction"""
        tx = Transaction(
            id=1,
            user_id=1,
            tx_hash=None,
            chain="ethereum",
            type=TransactionType.WITHDRAW,
            status=TransactionStatus.CONFIRMED,
            confirmations=0,
            asset=Asset.USDT,
            amount=Decimal("100.0"),
            address="test_address",
        )
        mock_db.transactions = {1: tx}
        with pytest.raises(WithdrawalApprovalError, match="Transaction is not pending"):
            admin_service.approve_withdrawal(admin_id=1, tx_id=1)

    def test_approve_withdrawal_already_approved(self, admin_service, mock_db):
        """Test approve_withdrawal with already approved transaction"""
        tx = Transaction(
            id=1,
            user_id=1,
            tx_hash=None,
            chain="ethereum",
            type=TransactionType.WITHDRAW,
            status=TransactionStatus.PENDING,
            confirmations=0,
            asset=Asset.USDT,
            amount=Decimal("100.0"),
            address="test_address",
        )
        mock_db.transactions = {1: tx}
        admin_service.withdrawal_approvals = {1: [1]}
        with pytest.raises(
            WithdrawalApprovalError, match="Admin has already approved this withdrawal"
        ):
            admin_service.approve_withdrawal(admin_id=1, tx_id=1)

    def test_approve_withdrawal_first_approval(
        self, admin_service, mock_db, mock_wallet_service
    ):
        """Test approve_withdrawal first approval"""
        tx = Transaction(
            id=1,
            user_id=1,
            tx_hash=None,
            chain="ethereum",
            type=TransactionType.WITHDRAW,
            status=TransactionStatus.PENDING,
            confirmations=0,
            asset=Asset.USDT,
            amount=Decimal("100.0"),
            address="test_address",
        )
        mock_db.transactions = {1: tx}
        mock_wallet_service.send_withdrawal.return_value = "tx_hash_123"

        result = admin_service.approve_withdrawal(admin_id=1, tx_id=1)
        assert result.status == TransactionStatus.PENDING
        assert 1 in admin_service.withdrawal_approvals[1]

    def test_approve_withdrawal_second_approval(
        self, admin_service, mock_db, mock_wallet_service, mock_account_service
    ):
        """Test approve_withdrawal second approval"""
        tx = Transaction(
            id=1,
            user_id=1,
            tx_hash=None,
            chain="ethereum",
            type=TransactionType.WITHDRAW,
            status=TransactionStatus.PENDING,
            confirmations=0,
            asset=Asset.USDT,
            amount=Decimal("100.0"),
            address="test_address",
        )
        mock_db.transactions = {1: tx}
        admin_service.withdrawal_approvals = {1: [1]}
        mock_wallet_service.send_withdrawal.return_value = "tx_hash_123"

        result = admin_service.approve_withdrawal(admin_id=2, tx_id=1)
        assert result.status == TransactionStatus.CONFIRMED
        assert result.tx_hash == "tx_hash_123"
        assert 1 not in admin_service.withdrawal_approvals

    def test_reject_withdrawal_admin_permission_error(self, admin_service):
        """Test reject_withdrawal with non-admin user"""
        with pytest.raises(AdminPermissionError, match="Insufficient permissions"):
            admin_service.reject_withdrawal(admin_id=200, tx_id=1, reason="test")

    def test_reject_withdrawal_transaction_not_found(self, admin_service, mock_db):
        """Test reject_withdrawal with non-existent transaction"""
        mock_db.transactions = {}
        with pytest.raises(EntityNotFoundError, match="Transaction 1 not found"):
            admin_service.reject_withdrawal(admin_id=1, tx_id=1, reason="test")

    def test_reject_withdrawal_not_withdrawal(self, admin_service, mock_db):
        """Test reject_withdrawal with non-withdrawal transaction"""
        tx = Transaction(
            id=1,
            user_id=1,
            tx_hash=None,
            chain="ethereum",
            type=TransactionType.DEPOSIT,
            status=TransactionStatus.PENDING,
            confirmations=0,
            asset=Asset.USDT,
            amount=Decimal("100.0"),
            address="test_address",
        )
        mock_db.transactions = {1: tx}
        with pytest.raises(
            WithdrawalApprovalError, match="Transaction is not a withdrawal"
        ):
            admin_service.reject_withdrawal(admin_id=1, tx_id=1, reason="test")

    def test_reject_withdrawal_not_pending(self, admin_service, mock_db):
        """Test reject_withdrawal with non-pending transaction"""
        tx = Transaction(
            id=1,
            user_id=1,
            tx_hash=None,
            chain="ethereum",
            type=TransactionType.WITHDRAW,
            status=TransactionStatus.CONFIRMED,
            confirmations=0,
            asset=Asset.USDT,
            amount=Decimal("100.0"),
            address="test_address",
        )
        mock_db.transactions = {1: tx}
        with pytest.raises(WithdrawalApprovalError, match="Transaction is not pending"):
            admin_service.reject_withdrawal(admin_id=1, tx_id=1, reason="test")

    def test_reject_withdrawal_success(
        self, admin_service, mock_db, mock_account_service
    ):
        """Test reject_withdrawal success"""
        tx = Transaction(
            id=1,
            user_id=1,
            tx_hash=None,
            chain="ethereum",
            type=TransactionType.WITHDRAW,
            status=TransactionStatus.PENDING,
            confirmations=0,
            asset=Asset.USDT,
            amount=Decimal("100.0"),
            address="test_address",
        )
        account = Account(id=1, user_id=1, status=AccountStatus.ACTIVE)
        balance = Balance(
            id=1,
            account_id=1,
            asset=Asset.USDT,
            available=Decimal("0.0"),
            locked=Decimal("100.0"),
        )
        mock_db.transactions = {1: tx}
        mock_db.accounts = {1: account}
        mock_db.balances = {1: balance}
        admin_service.withdrawal_approvals = {1: [1]}
        mock_account_service.get_account.return_value = account
        mock_account_service._ensure_balance.return_value = balance

        result = admin_service.reject_withdrawal(admin_id=1, tx_id=1, reason="test")
        assert result.status == TransactionStatus.FAILED
        assert 1 not in admin_service.withdrawal_approvals

    def test_freeze_account_admin_permission_error(self, admin_service):
        """Test freeze_account with non-admin user"""
        with pytest.raises(AdminPermissionError, match="Insufficient permissions"):
            admin_service.freeze_account(admin_id=200, account_id=1, reason="test")

    def test_freeze_account_not_found(self, admin_service, mock_db):
        """Test freeze_account with non-existent account"""
        mock_db.accounts = {}
        with pytest.raises(EntityNotFoundError, match="Account 1 not found"):
            admin_service.freeze_account(admin_id=1, account_id=1, reason="test")

    def test_freeze_account_already_frozen(self, admin_service, mock_db):
        """Test freeze_account with already frozen account"""
        account = Account(id=1, user_id=1, status=AccountStatus.FROZEN, frozen=True)
        mock_db.accounts = {1: account}
        with pytest.raises(AdminPermissionError, match="Account is already frozen"):
            admin_service.freeze_account(admin_id=1, account_id=1, reason="test")

    def test_freeze_account_success(self, admin_service, mock_db):
        """Test freeze_account success"""
        account = Account(id=1, user_id=1, status=AccountStatus.ACTIVE, frozen=False)
        mock_db.accounts = {1: account}

        result = admin_service.freeze_account(admin_id=1, account_id=1, reason="test")
        assert result.frozen is True
        assert result.status == AccountStatus.FROZEN

    def test_unfreeze_account_admin_permission_error(self, admin_service):
        """Test unfreeze_account with non-admin user"""
        with pytest.raises(AdminPermissionError, match="Insufficient permissions"):
            admin_service.unfreeze_account(admin_id=200, account_id=1)

    def test_unfreeze_account_not_found(self, admin_service, mock_db):
        """Test unfreeze_account with non-existent account"""
        mock_db.accounts = {}
        with pytest.raises(EntityNotFoundError, match="Account 1 not found"):
            admin_service.unfreeze_account(admin_id=1, account_id=1)

    def test_unfreeze_account_not_frozen(self, admin_service, mock_db):
        """Test unfreeze_account with not frozen account"""
        account = Account(id=1, user_id=1, status=AccountStatus.ACTIVE, frozen=False)
        mock_db.accounts = {1: account}
        with pytest.raises(AdminPermissionError, match="Account is not frozen"):
            admin_service.unfreeze_account(admin_id=1, account_id=1)

    def test_unfreeze_account_success(self, admin_service, mock_db):
        """Test unfreeze_account success"""
        account = Account(id=1, user_id=1, status=AccountStatus.FROZEN, frozen=True)
        mock_db.accounts = {1: account}

        result = admin_service.unfreeze_account(admin_id=1, account_id=1)
        assert result.frozen is False
        assert result.status == AccountStatus.ACTIVE

    def test_get_audit_logs_admin_permission_error(self, admin_service):
        """Test get_audit_logs with non-admin user"""
        with pytest.raises(AdminPermissionError, match="Insufficient permissions"):
            admin_service.get_audit_logs(admin_id=200)

    def test_get_audit_logs_success(self, admin_service, mock_db):
        """Test get_audit_logs success"""
        log1 = AuditLog(
            id=1,
            actor="admin_1",
            action="test_action",
            entity="test_entity",
            metadata={},
            created_at=datetime.now(timezone.utc),
        )
        log2 = AuditLog(
            id=2,
            actor="admin_2",
            action="another_action",
            entity="another_entity",
            metadata={},
            created_at=datetime.now(timezone.utc),
        )
        mock_db.audit_logs = {1: log1, 2: log2}

        result = admin_service.get_audit_logs(admin_id=1)
        assert len(result) == 2

    def test_get_audit_logs_with_filters(self, admin_service, mock_db):
        """Test get_audit_logs with filters"""
        now = datetime.now(timezone.utc)
        log1 = AuditLog(
            id=1,
            actor="admin_1",
            action="test_action",
            entity="test_entity",
            metadata={},
            created_at=now,
        )
        log2 = AuditLog(
            id=2,
            actor="admin_2",
            action="another_action",
            entity="another_entity",
            metadata={},
            created_at=now,
        )
        mock_db.audit_logs = {1: log1, 2: log2}

        result = admin_service.get_audit_logs(
            admin_id=1,
            actor="admin_1",
            action="test_action",
            limit=1,
        )
        assert len(result) == 1
        assert result[0].actor == "admin_1"

    def test_get_account_info_admin_permission_error(self, admin_service):
        """Test get_account_info with non-admin user"""
        with pytest.raises(AdminPermissionError, match="Insufficient permissions"):
            admin_service.get_account_info(admin_id=200, account_id=1)

    def test_get_account_info_account_not_found(self, admin_service, mock_db):
        """Test get_account_info with non-existent account"""
        mock_db.accounts = {}
        with pytest.raises(EntityNotFoundError, match="Account 1 not found"):
            admin_service.get_account_info(admin_id=1, account_id=1)

    def test_get_account_info_user_not_found(self, admin_service, mock_db):
        """Test get_account_info with non-existent user"""
        account = Account(id=1, user_id=1, status=AccountStatus.ACTIVE)
        mock_db.accounts = {1: account}
        mock_db.users = {}
        with pytest.raises(EntityNotFoundError, match="User 1 not found"):
            admin_service.get_account_info(admin_id=1, account_id=1)

    def test_get_account_info_success(self, admin_service, mock_db):
        """Test get_account_info success"""
        account = Account(
            id=1, user_id=1, status=AccountStatus.ACTIVE, kyc_level=1, frozen=False
        )
        user = User(
            id=1,
            email="test@example.com",
            password_hash="hash",
            created_at=datetime.now(timezone.utc),
            last_login=datetime.now(timezone.utc),
        )
        balance = Balance(
            id=1,
            account_id=1,
            asset=Asset.USDT,
            available=Decimal("100.0"),
            locked=Decimal("50.0"),
        )
        tx = Transaction(
            id=1,
            user_id=1,
            tx_hash="tx_hash_123",
            chain="ethereum",
            type=TransactionType.DEPOSIT,
            status=TransactionStatus.CONFIRMED,
            confirmations=12,
            asset=Asset.USDT,
            amount=Decimal("100.0"),
            address="test_address",
        )
        mock_db.accounts = {1: account}
        mock_db.users = {1: user}
        mock_db.balances = {1: balance}
        mock_db.transactions = {1: tx}

        result = admin_service.get_account_info(admin_id=1, account_id=1)
        assert "account" in result
        assert "user" in result
        assert "balances" in result
        assert "recent_transactions" in result

    def test_get_market_overview_admin_permission_error(self, admin_service):
        """Test get_market_overview with non-admin user"""
        with pytest.raises(AdminPermissionError, match="Insufficient permissions"):
            admin_service.get_market_overview(admin_id=200)

    def test_get_market_overview_success(
        self, admin_service, mock_db, mock_account_service
    ):
        """Test get_market_overview success"""
        trade = MagicMock()
        trade.id = 1
        trade.price = Decimal("1.0")
        trade.amount = Decimal("10.0")
        trade.created_at = datetime.now(timezone.utc)
        mock_db.trades = {1: trade}

        result = admin_service.get_market_overview(admin_id=1)
        assert "market" in result
        assert "orderbook" in result
        assert "recent_trades" in result
        assert "stop_orders_count" in result
        assert "oco_pairs_count" in result
