"""
Admin Service 테스트
"""

from decimal import Decimal

import pytest

from alt_exchange.core.enums import (AccountStatus, Asset, TransactionStatus,
                                     TransactionType)
from alt_exchange.core.models import Account, Transaction
from alt_exchange.infra.database.in_memory import InMemoryDatabase
from alt_exchange.infra.event_bus import InMemoryEventBus
from alt_exchange.services.account.service import AccountService
from alt_exchange.services.admin.service import AdminService
from alt_exchange.services.matching.engine import MatchingEngine
from alt_exchange.services.wallet.service import WalletService


class TestAdminService:
    def setup_method(self):
        self.db = InMemoryDatabase()
        self.event_bus = InMemoryEventBus()
        self.matching_engine = MatchingEngine("ALT/USDT", self.db, self.event_bus)
        self.account_service = AccountService(
            self.db, self.event_bus, self.matching_engine
        )
        self.wallet_service = WalletService(self.account_service)
        self.service = AdminService(
            self.db, self.event_bus, self.account_service, self.wallet_service
        )

    def test_is_admin(self):
        # User ID < 100 should be admin
        assert self.service._is_admin(1) is True
        assert self.service._is_admin(99) is True

        # User ID >= 100 should not be admin
        assert self.service._is_admin(100) is False
        assert self.service._is_admin(200) is False

    def test_list_pending_withdrawals(self):
        # Create a user and account
        user = self.account_service.create_user("test@example.com", "password123")

        # Add some balance
        account = self.account_service.get_account(user.id)
        balance = self.account_service.get_balance(user.id, Asset.ALT)
        balance.available = Decimal("1000.0")
        self.db.upsert_balance(balance)

        # Request withdrawal
        transaction = self.wallet_service.request_withdrawal(
            user_id=user.id, asset=Asset.ALT, amount=Decimal("100.0"), address="0x456"
        )

        # List pending withdrawals as admin
        pending_withdrawals = self.service.list_pending_withdrawals(1)  # Admin user ID

        assert len(pending_withdrawals) == 1
        assert pending_withdrawals[0].id == transaction.id
        assert pending_withdrawals[0].status == TransactionStatus.PENDING

    def test_approve_withdrawal_first_approval(self):
        # Create a user and account
        user = self.account_service.create_user("test@example.com", "password123")

        # Add some balance
        account = self.account_service.get_account(user.id)
        balance = self.account_service.get_balance(user.id, Asset.ALT)
        balance.available = Decimal("1000.0")
        self.db.upsert_balance(balance)

        # Request withdrawal
        transaction = self.wallet_service.request_withdrawal(
            user_id=user.id, asset=Asset.ALT, amount=Decimal("100.0"), address="0x456"
        )

        # First approval
        approved_transaction = self.service.approve_withdrawal(1, transaction.id)

        assert approved_transaction.approver_id == 1
        assert approved_transaction.approved_at is not None
        assert (
            approved_transaction.status == TransactionStatus.PENDING
        )  # Still pending for second approval

    def test_approve_withdrawal_second_approval(self):
        # Create a user and account
        user = self.account_service.create_user("test@example.com", "password123")

        # Add some balance
        account = self.account_service.get_account(user.id)
        balance = self.account_service.get_balance(user.id, Asset.ALT)
        balance.available = Decimal("1000.0")
        self.db.upsert_balance(balance)

        # Request withdrawal
        transaction = self.wallet_service.request_withdrawal(
            user_id=user.id, asset=Asset.ALT, amount=Decimal("100.0"), address="0x456"
        )

        # First approval
        self.service.approve_withdrawal(1, transaction.id)

        # Second approval
        approved_transaction = self.service.approve_withdrawal(2, transaction.id)

        assert approved_transaction.status == TransactionStatus.CONFIRMED
        assert approved_transaction.tx_hash is not None

    def test_reject_withdrawal(self):
        # Create a user and account
        user = self.account_service.create_user("test@example.com", "password123")

        # Add some balance
        account = self.account_service.get_account(user.id)
        balance = self.account_service.get_balance(user.id, Asset.ALT)
        balance.available = Decimal("1000.0")
        self.db.upsert_balance(balance)

        # Request withdrawal
        transaction = self.wallet_service.request_withdrawal(
            user_id=user.id, asset=Asset.ALT, amount=Decimal("100.0"), address="0x456"
        )

        # Reject withdrawal
        rejected_transaction = self.service.reject_withdrawal(
            1, transaction.id, "Insufficient documentation"
        )

        assert rejected_transaction.status == TransactionStatus.FAILED
        assert rejected_transaction.rejected_at is not None

    def test_freeze_account(self):
        # Create a user and account
        user = self.account_service.create_user("test@example.com", "password123")
        account = self.account_service.get_account(user.id)

        # Freeze account
        frozen_account = self.service.freeze_account(
            1, account.id, "Suspicious activity"
        )

        assert frozen_account.frozen is True
        assert frozen_account.status == AccountStatus.FROZEN

    def test_unfreeze_account(self):
        # Create a user and account
        user = self.account_service.create_user("test@example.com", "password123")
        account = self.account_service.get_account(user.id)

        # Freeze account first
        self.service.freeze_account(1, account.id, "Suspicious activity")

        # Unfreeze account
        unfrozen_account = self.service.unfreeze_account(1, account.id)

        assert unfrozen_account.frozen is False
        assert unfrozen_account.status == AccountStatus.ACTIVE

    def test_get_account_info(self):
        # Create a user and account
        user = self.account_service.create_user("test@example.com", "password123")
        account = self.account_service.get_account(user.id)

        # Get account info
        account_info = self.service.get_account_info(1, account.id)

        assert account_info["account"]["id"] == account.id
        assert account_info["account"]["user_id"] == user.id
        assert "balances" in account_info
        assert "user" in account_info
        assert "recent_transactions" in account_info

    def test_get_audit_logs(self):
        # Create a user and account
        user = self.account_service.create_user("test@example.com", "password123")
        account = self.account_service.get_account(user.id)

        # Freeze account to generate audit log
        self.service.freeze_account(1, account.id, "Test reason")

        # Get audit logs
        logs = self.service.get_audit_logs(1, limit=10)

        assert len(logs) >= 1
        assert logs[0].action == "account_frozen"

    def test_get_market_overview(self):
        # Get market overview
        overview = self.service.get_market_overview(1)

        assert "market" in overview
        assert "orderbook" in overview
        assert "recent_trades" in overview
        assert "oco_pairs_count" in overview
