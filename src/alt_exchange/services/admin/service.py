from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, List, Optional

from alt_exchange.core.enums import (AccountStatus, Asset, TransactionStatus,
                                     TransactionType)
from alt_exchange.core.events import (AccountFrozen, AccountUnfrozen,
                                      WithdrawalApproved, WithdrawalRejected)
from alt_exchange.core.exceptions import (AdminPermissionError,
                                          EntityNotFoundError,
                                          WithdrawalApprovalError)
from alt_exchange.core.models import Account, AuditLog, Transaction, User
from alt_exchange.infra.database.base import Database
from alt_exchange.infra.database.in_memory import InMemoryUnitOfWork
from alt_exchange.infra.event_bus import InMemoryEventBus
from alt_exchange.services.account.service import AccountService
from alt_exchange.services.wallet.service import WalletService


class AdminService:
    """Service for administrative operations including withdrawal approval and account management."""

    def __init__(
        self,
        db: Database,
        event_bus: InMemoryEventBus,
        account_service: AccountService,
        wallet_service: WalletService,
    ) -> None:
        self.db = db
        self.event_bus = event_bus
        self.account_service = account_service
        self.wallet_service = wallet_service
        # Track approval status for 2-eyes approval process
        self.withdrawal_approvals: Dict[int, List[int]] = {}  # tx_id -> [approver_ids]

    def _is_admin(self, user_id: int) -> bool:
        """Check if user has admin privileges."""
        # In a real system, this would check user roles/permissions
        # For now, we'll use a simple check (e.g., user_id < 100 for admins)
        return user_id < 100

    def _log_admin_action(
        self,
        admin_id: int,
        action: str,
        entity_type: str,
        entity_id: int,
        metadata: Dict,
    ) -> None:
        """Log administrative actions for audit purposes."""
        audit_log = AuditLog(
            id=self.db.next_id("audit_logs"),
            actor=f"admin_{admin_id}",
            action=action,
            entity=entity_type,
            metadata=metadata,
        )
        self.db.insert_audit_log(audit_log)

    def list_pending_withdrawals(self, admin_id: int) -> List[Transaction]:
        """List all pending withdrawal requests."""
        if not self._is_admin(admin_id):
            raise AdminPermissionError("Insufficient permissions")

        pending_withdrawals = []
        for tx in self.db.transactions.values():
            if (
                tx.type == TransactionType.WITHDRAW
                and tx.status == TransactionStatus.PENDING
            ):
                pending_withdrawals.append(tx)

        return sorted(pending_withdrawals, key=lambda x: x.created_at)

    def approve_withdrawal(self, admin_id: int, tx_id: int) -> Transaction:
        """Approve a withdrawal request (2-eyes approval process)."""
        if not self._is_admin(admin_id):
            raise AdminPermissionError("Insufficient permissions")

        tx = self.db.transactions.get(tx_id)
        if not tx:
            raise EntityNotFoundError(f"Transaction {tx_id} not found")

        if tx.type != TransactionType.WITHDRAW:
            raise WithdrawalApprovalError("Transaction is not a withdrawal")

        if tx.status != TransactionStatus.PENDING:
            raise WithdrawalApprovalError("Transaction is not pending")

        # Check if this admin has already approved
        if tx_id in self.withdrawal_approvals:
            if admin_id in self.withdrawal_approvals[tx_id]:
                raise WithdrawalApprovalError(
                    "Admin has already approved this withdrawal"
                )

        # Add approval
        if tx_id not in self.withdrawal_approvals:
            self.withdrawal_approvals[tx_id] = []
        self.withdrawal_approvals[tx_id].append(admin_id)

        # Check if we have 2 approvals
        if len(self.withdrawal_approvals[tx_id]) >= 2:
            # Complete the withdrawal
            now = datetime.now(timezone.utc)
            tx.status = TransactionStatus.CONFIRMED
            tx.approver_id = admin_id
            tx.approved_at = now
            self.db.update_transaction(tx)

            # Execute the withdrawal via wallet service
            tx_hash = self.wallet_service.send_withdrawal(
                tx.user_id, tx.asset, tx.amount, tx.address or ""
            )
            tx.tx_hash = tx_hash

            # Complete the withdrawal in account service
            self.account_service.complete_withdrawal(tx_id, tx_hash)

            # Clean up approval tracking
            del self.withdrawal_approvals[tx_id]

            self.event_bus.publish(
                WithdrawalApproved(
                    transaction_id=tx_id,
                    approver_id=admin_id,
                    approved_at=now.isoformat(),
                )
            )

            self._log_admin_action(
                admin_id,
                "withdrawal_approved",
                "transaction",
                tx_id,
                {"amount": str(tx.amount), "asset": tx.asset.value, "tx_hash": tx_hash},
            )
        else:
            # First approval - just update the transaction
            now = datetime.now(timezone.utc)
            tx.approver_id = admin_id
            tx.approved_at = now
            self.db.update_transaction(tx)

            self._log_admin_action(
                admin_id,
                "withdrawal_first_approval",
                "transaction",
                tx_id,
                {"amount": str(tx.amount), "asset": tx.asset.value},
            )

        return tx

    def reject_withdrawal(self, admin_id: int, tx_id: int, reason: str) -> Transaction:
        """Reject a withdrawal request."""
        if not self._is_admin(admin_id):
            raise AdminPermissionError("Insufficient permissions")

        tx = self.db.transactions.get(tx_id)
        if not tx:
            raise EntityNotFoundError(f"Transaction {tx_id} not found")

        if tx.type != TransactionType.WITHDRAW:
            raise WithdrawalApprovalError("Transaction is not a withdrawal")

        if tx.status != TransactionStatus.PENDING:
            raise WithdrawalApprovalError("Transaction is not pending")

        # Reject the withdrawal
        now = datetime.now(timezone.utc)
        tx.status = TransactionStatus.FAILED
        tx.approver_id = admin_id
        tx.rejected_at = now
        self.db.update_transaction(tx)

        # Release locked funds
        account = self.account_service.get_account(tx.user_id)
        balance = self.account_service._ensure_balance(account.id, tx.asset)
        balance.locked -= tx.amount
        balance.available += tx.amount
        balance.updated_at = now
        self.db.upsert_balance(balance)

        # Clean up approval tracking
        if tx_id in self.withdrawal_approvals:
            del self.withdrawal_approvals[tx_id]

        self.event_bus.publish(
            WithdrawalRejected(
                transaction_id=tx_id,
                approver_id=admin_id,
                rejected_at=now.isoformat(),
                reason=reason,
            )
        )

        self._log_admin_action(
            admin_id,
            "withdrawal_rejected",
            "transaction",
            tx_id,
            {"amount": str(tx.amount), "asset": tx.asset.value, "reason": reason},
        )

        return tx

    def freeze_account(self, admin_id: int, account_id: int, reason: str) -> Account:
        """Freeze an account to prevent trading and withdrawals."""
        if not self._is_admin(admin_id):
            raise AdminPermissionError("Insufficient permissions")

        account = self.db.accounts.get(account_id)
        if not account:
            raise EntityNotFoundError(f"Account {account_id} not found")

        if account.frozen:
            raise AdminPermissionError("Account is already frozen")

        # Freeze the account
        account.frozen = True
        account.status = AccountStatus.FROZEN
        self.db.update_account(account)

        self.event_bus.publish(
            AccountFrozen(
                account_id=account_id,
                user_id=account.user_id,
                frozen_by=admin_id,
                reason=reason,
            )
        )

        self._log_admin_action(
            admin_id,
            "account_frozen",
            "account",
            account_id,
            {"user_id": account.user_id, "reason": reason},
        )

        return account

    def unfreeze_account(self, admin_id: int, account_id: int) -> Account:
        """Unfreeze an account to allow trading and withdrawals."""
        if not self._is_admin(admin_id):
            raise AdminPermissionError("Insufficient permissions")

        account = self.db.accounts.get(account_id)
        if not account:
            raise EntityNotFoundError(f"Account {account_id} not found")

        if not account.frozen:
            raise AdminPermissionError("Account is not frozen")

        # Unfreeze the account
        account.frozen = False
        account.status = AccountStatus.ACTIVE
        self.db.update_account(account)

        self.event_bus.publish(
            AccountUnfrozen(
                account_id=account_id,
                user_id=account.user_id,
                unfrozen_by=admin_id,
            )
        )

        self._log_admin_action(
            admin_id,
            "account_unfrozen",
            "account",
            account_id,
            {"user_id": account.user_id},
        )

        return account

    def get_audit_logs(
        self,
        admin_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        actor: Optional[str] = None,
        action: Optional[str] = None,
        limit: int = 100,
    ) -> List[AuditLog]:
        """Get audit logs with optional filtering."""
        if not self._is_admin(admin_id):
            raise AdminPermissionError("Insufficient permissions")

        logs = list(self.db.audit_logs.values())

        # Apply filters
        if start_date:
            logs = [log for log in logs if log.created_at >= start_date]
        if end_date:
            logs = [log for log in logs if log.created_at <= end_date]
        if actor:
            logs = [log for log in logs if actor in log.actor]
        if action:
            logs = [log for log in logs if log.action == action]

        # Sort by creation date (newest first) and limit
        logs.sort(key=lambda x: x.created_at, reverse=True)
        return logs[:limit]

    def get_account_info(self, admin_id: int, account_id: int) -> Dict:
        """Get detailed account information for admin review."""
        if not self._is_admin(admin_id):
            raise AdminPermissionError("Insufficient permissions")

        account = self.db.accounts.get(account_id)
        if not account:
            raise EntityNotFoundError(f"Account {account_id} not found")

        user = self.db.users.get(account.user_id)
        if not user:
            raise EntityNotFoundError(f"User {account.user_id} not found")

        # Get balances
        balances = []
        for balance in self.db.balances.values():
            if balance.account_id == account_id:
                balances.append(
                    {
                        "asset": balance.asset.value,
                        "available": str(balance.available),
                        "locked": str(balance.locked),
                    }
                )

        # Get recent transactions
        recent_transactions = []
        for tx in self.db.transactions.values():
            if tx.user_id == account.user_id:
                recent_transactions.append(
                    {
                        "id": tx.id,
                        "type": tx.type.value,
                        "status": tx.status.value,
                        "asset": tx.asset.value,
                        "amount": str(tx.amount),
                        "created_at": tx.created_at.isoformat(),
                    }
                )

        # Sort by creation date (newest first) and limit to 10
        recent_transactions.sort(key=lambda x: x["created_at"], reverse=True)
        recent_transactions = recent_transactions[:10]

        return {
            "account": {
                "id": account.id,
                "user_id": account.user_id,
                "status": account.status.value,
                "kyc_level": account.kyc_level,
                "frozen": account.frozen,
            },
            "user": {
                "id": user.id,
                "email": user.email,
                "created_at": user.created_at.isoformat(),
                "last_login": user.last_login.isoformat() if user.last_login else None,
            },
            "balances": balances,
            "recent_transactions": recent_transactions,
        }

    def get_market_overview(self, admin_id: int) -> Dict:
        """Get market overview for admin monitoring."""
        if not self._is_admin(admin_id):
            raise AdminPermissionError("Insufficient permissions")

        # Get order book snapshot
        bids, asks = self.account_service.matching.order_book_snapshot()

        # Get recent trades
        recent_trades = []
        for trade in self.db.trades.values():
            recent_trades.append(
                {
                    "id": trade.id,
                    "price": str(trade.price),
                    "amount": str(trade.amount),
                    "created_at": trade.created_at.isoformat(),
                }
            )

        # Sort by creation date (newest first) and limit to 20
        recent_trades.sort(key=lambda x: x["created_at"], reverse=True)
        recent_trades = recent_trades[:20]

        return {
            "market": self.account_service.market,
            "orderbook": {
                "bids": [(str(price), str(amount)) for price, amount in bids[:10]],
                "asks": [(str(price), str(amount)) for price, amount in asks[:10]],
            },
            "recent_trades": recent_trades,
            "stop_orders_count": len(self.account_service.matching.stop_orders),
            "oco_pairs_count": len(self.account_service.matching.oco_pairs),
        }
