from __future__ import annotations

from decimal import Decimal
from typing import Dict

from alt_exchange.core.enums import Asset
from alt_exchange.core.models import Transaction
from alt_exchange.services.account.service import AccountService


class WalletService:
    """Lightweight wallet simulator that relies on the account service for balance updates."""

    def __init__(self, account_service: AccountService) -> None:
        self.account_service = account_service
        self.pending_withdrawals: Dict[int, Transaction] = {}

    def allocate_deposit_address(self, user_id: int) -> str:
        # Deterministic fake address for tests
        return f"0xDEADBEEF{user_id:04d}"

    def simulate_deposit(self, user_id: int, asset: Asset, amount: Decimal, tx_hash: str | None = None) -> Transaction:
        return self.account_service.credit_deposit(user_id=user_id, asset=asset, amount=amount, tx_hash=tx_hash)

    def request_withdrawal(self, user_id: int, asset: Asset, amount: Decimal, address: str) -> Transaction:
        tx = self.account_service.request_withdrawal(user_id=user_id, asset=asset, amount=amount, address=address)
        self.pending_withdrawals[tx.id] = tx
        return tx

    def complete_withdrawal(self, tx_id: int, tx_hash: str) -> Transaction:
        self.pending_withdrawals.pop(tx_id, None)
        return self.account_service.complete_withdrawal(tx_id=tx_id, tx_hash=tx_hash)
