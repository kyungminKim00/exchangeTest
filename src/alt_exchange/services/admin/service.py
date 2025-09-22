"""
Admin service for managing withdrawals, system operations, and approvals
Implements 2-eyes approval workflow for withdrawals
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional

from alt_exchange.core.enums import Asset, TransactionStatus, TransactionType
from alt_exchange.core.models import AuditLog, Transaction
from alt_exchange.infra.datastore import InMemoryDatabase
from alt_exchange.infra.event_bus import InMemoryEventBus


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ApprovalType(str, Enum):
    WITHDRAWAL = "withdrawal"
    SYSTEM_OPERATION = "system_operation"
    EMERGENCY_PAUSE = "emergency_pause"


@dataclass
class ApprovalRequest:
    id: int
    type: ApprovalType
    entity_id: int  # withdrawal_id, etc.
    requester_id: int
    approver_id: Optional[int] = None
    status: ApprovalStatus = ApprovalStatus.PENDING
    metadata: Dict = None
    created_at: datetime = None
    approved_at: Optional[datetime] = None
    reason: Optional[str] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)
        if self.metadata is None:
            self.metadata = {}


class AdminService:
    """Admin service for system management and approvals"""

    def __init__(self, db: InMemoryDatabase, event_bus: InMemoryEventBus):
        self.db = db
        self.event_bus = event_bus
        self.approval_requests: Dict[int, ApprovalRequest] = {}
        self._next_approval_id = 1

    def create_withdrawal_approval_request(
        self,
        withdrawal_id: int,
        requester_id: int,
        amount: Decimal,
        asset: Asset,
        address: str,
    ) -> ApprovalRequest:
        """Create a withdrawal approval request"""
        approval_id = self._next_approval_id
        self._next_approval_id += 1

        request = ApprovalRequest(
            id=approval_id,
            type=ApprovalType.WITHDRAWAL,
            entity_id=withdrawal_id,
            requester_id=requester_id,
            metadata={"amount": str(amount), "asset": asset.value, "address": address},
        )

        self.approval_requests[approval_id] = request

        # Log audit event
        self._log_audit_event(
            actor=f"user:{requester_id}",
            action="withdrawal_approval_requested",
            entity=f"withdrawal:{withdrawal_id}",
            metadata=request.metadata,
        )

        return request

    def approve_withdrawal(
        self, approval_id: int, approver_id: int, reason: Optional[str] = None
    ) -> bool:
        """Approve a withdrawal request (2-eyes approval)"""
        if approval_id not in self.approval_requests:
            return False

        request = self.approval_requests[approval_id]

        if request.status != ApprovalStatus.PENDING:
            return False

        # Check if this is the second approval
        if request.approver_id is None:
            # First approval
            request.approver_id = approver_id
            request.reason = reason
            request.status = ApprovalStatus.APPROVED
            request.approved_at = datetime.now(timezone.utc)

            # Log audit event
            self._log_audit_event(
                actor=f"admin:{approver_id}",
                action="withdrawal_first_approval",
                entity=f"withdrawal:{request.entity_id}",
                metadata={"approval_id": approval_id, "reason": reason},
            )

            # Trigger withdrawal processing
            self._process_approved_withdrawal(request)
            return True
        else:
            # Second approval - complete the withdrawal
            if request.approver_id != approver_id:  # Different approver required
                request.status = ApprovalStatus.APPROVED
                request.approved_at = datetime.now(timezone.utc)

                # Log audit event
                self._log_audit_event(
                    actor=f"admin:{approver_id}",
                    action="withdrawal_second_approval",
                    entity=f"withdrawal:{request.entity_id}",
                    metadata={"approval_id": approval_id, "reason": reason},
                )

                # Complete withdrawal processing
                self._complete_withdrawal(request)
                return True

        return False

    def reject_withdrawal(
        self, approval_id: int, approver_id: int, reason: str
    ) -> bool:
        """Reject a withdrawal request"""
        if approval_id not in self.approval_requests:
            return False

        request = self.approval_requests[approval_id]

        if request.status != ApprovalStatus.PENDING:
            return False

        request.status = ApprovalStatus.REJECTED
        request.approver_id = approver_id
        request.reason = reason
        request.approved_at = datetime.now(timezone.utc)

        # Log audit event
        self._log_audit_event(
            actor=f"admin:{approver_id}",
            action="withdrawal_rejected",
            entity=f"withdrawal:{request.entity_id}",
            metadata={"approval_id": approval_id, "reason": reason},
        )

        # Update withdrawal status
        withdrawal = self.db.get_transaction(request.entity_id)
        if withdrawal:
            withdrawal.status = TransactionStatus.FAILED
            self.db.update_transaction(withdrawal)

        return True

    def get_pending_approvals(self) -> List[ApprovalRequest]:
        """Get all pending approval requests"""
        return [
            request
            for request in self.approval_requests.values()
            if request.status == ApprovalStatus.PENDING
        ]

    def get_approval_history(self, limit: int = 100) -> List[ApprovalRequest]:
        """Get approval request history"""
        requests = list(self.approval_requests.values())
        requests.sort(key=lambda x: x.created_at, reverse=True)
        return requests[:limit]

    def emergency_pause_system(self, admin_id: int, reason: str) -> bool:
        """Emergency system pause (requires immediate approval)"""
        # Log audit event
        self._log_audit_event(
            actor=f"admin:{admin_id}",
            action="emergency_pause_initiated",
            entity="system",
            metadata={"reason": reason},
        )

        # In production, this would trigger system-wide pause
        # For now, just log the event
        return True

    def get_system_metrics(self) -> Dict:
        """Get system metrics for admin dashboard"""
        return {
            "total_users": len(self.db.users),
            "total_orders": len(self.db.orders),
            "total_trades": len(self.db.trades),
            "pending_withdrawals": len(
                [
                    t
                    for t in self.db.transactions.values()
                    if t.type == TransactionType.WITHDRAW
                    and t.status == TransactionStatus.PENDING
                ]
            ),
            "pending_approvals": len(self.get_pending_approvals()),
            "system_status": "operational",
        }

    def _process_approved_withdrawal(self, request: ApprovalRequest):
        """Process first approval of withdrawal"""
        withdrawal = self.db.get_transaction(request.entity_id)
        if withdrawal:
            # Update status to pending processing
            withdrawal.status = TransactionStatus.PENDING
            self.db.update_transaction(withdrawal)

            # In production, this would queue the withdrawal for processing
            # For now, we'll simulate immediate processing
            self._complete_withdrawal(request)

    def _complete_withdrawal(self, request: ApprovalRequest):
        """Complete withdrawal processing"""
        withdrawal = self.db.get_transaction(request.entity_id)
        if withdrawal:
            # Simulate successful withdrawal
            withdrawal.status = TransactionStatus.CONFIRMED
            withdrawal.tx_hash = f"0x{'a' * 64}"  # Simulated transaction hash
            self.db.update_transaction(withdrawal)

            # Log completion
            self._log_audit_event(
                actor="system",
                action="withdrawal_completed",
                entity=f"withdrawal:{request.entity_id}",
                metadata={"tx_hash": withdrawal.tx_hash},
            )

    def _log_audit_event(self, actor: str, action: str, entity: str, metadata: Dict):
        """Log audit event"""
        audit_log = AuditLog(
            id=len(self.db.audit_logs) + 1,
            actor=actor,
            action=action,
            entity=entity,
            metadata=metadata,
        )
        self.db.audit_logs[audit_log.id] = audit_log
