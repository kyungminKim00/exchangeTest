from __future__ import annotations

import hashlib
import random
from decimal import Decimal
from typing import Dict, Optional

from alt_exchange.core.enums import Asset, TransactionStatus
from alt_exchange.core.models import Transaction
from alt_exchange.services.account.service import AccountService


class WalletService:
    """Enhanced wallet service with deposit address generation and external wallet integration."""

    def __init__(self, account_service: AccountService) -> None:
        self.account_service = account_service
        self.pending_withdrawals: Dict[int, Transaction] = {}
        self.deposit_addresses: Dict[str, Dict] = (
            {}
        )  # address -> {user_id, asset, created_at}
        self.external_wallet_interface = ExternalWalletInterface()

    def generate_deposit_address(self, user_id: int, asset: Asset) -> str:
        """Generate a unique deposit address for a user and asset."""
        # Check if address already exists for this user and asset
        for address, info in self.deposit_addresses.items():
            if info["user_id"] == user_id and info["asset"] == asset:
                return address

        # Generate a deterministic but unique address
        seed = f"{user_id}_{asset.value}"
        address_hash = hashlib.sha256(seed.encode()).hexdigest()[:40]
        address = f"0x{address_hash}"

        # Store address mapping
        self.deposit_addresses[address] = {
            "user_id": user_id,
            "asset": asset,
            "created_at": self._get_current_timestamp(),
        }

        return address

    def get_deposit_address(self, user_id: int, asset: Asset) -> Optional[str]:
        """Get existing deposit address for user and asset, or generate new one."""
        for address, info in self.deposit_addresses.items():
            if info["user_id"] == user_id and info["asset"] == asset:
                return address

        # Generate new address if none exists
        return self.generate_deposit_address(user_id, asset)

    def send_withdrawal(
        self, user_id: int, asset: Asset, amount: Decimal, address: str
    ) -> str:
        """Send withdrawal to external wallet and return transaction hash."""
        # Simulate external wallet API call
        tx_hash = self.external_wallet_interface.send_transaction(
            from_address=self._get_exchange_wallet_address(asset),
            to_address=address,
            amount=amount,
            asset=asset,
        )

        return tx_hash

    def check_transaction_status(self, tx_hash: str) -> Dict:
        """Check the status of a blockchain transaction."""
        return self.external_wallet_interface.get_transaction_status(tx_hash)

    def simulate_deposit(
        self, user_id: int, asset: Asset, amount: Decimal, tx_hash: str | None = None
    ) -> Transaction:
        """Simulate a deposit from external wallet."""
        if tx_hash is None:
            tx_hash = self._generate_tx_hash()

        return self.account_service.credit_deposit(
            user_id=user_id, asset=asset, amount=amount, tx_hash=tx_hash
        )

    def request_withdrawal(
        self, user_id: int, asset: Asset, amount: Decimal, address: str
    ) -> Transaction:
        """Request a withdrawal to external wallet."""
        tx = self.account_service.request_withdrawal(
            user_id=user_id, asset=asset, amount=amount, address=address
        )
        self.pending_withdrawals[tx.id] = tx
        return tx

    def complete_withdrawal(self, tx_id: int, tx_hash: str) -> Transaction:
        """Complete a withdrawal after external wallet confirmation."""
        self.pending_withdrawals.pop(tx_id, None)
        return self.account_service.complete_withdrawal(tx_id=tx_id, tx_hash=tx_hash)

    def _get_exchange_wallet_address(self, asset: Asset) -> str:
        """Get the exchange's wallet address for a specific asset."""
        # In a real system, these would be actual wallet addresses
        exchange_addresses = {
            Asset.ALT: "0xEXCHANGE_ALT_WALLET",
            Asset.USDT: "0xEXCHANGE_USDT_WALLET",
        }
        return exchange_addresses.get(asset, "0xEXCHANGE_DEFAULT_WALLET")

    def _generate_tx_hash(self) -> str:
        """Generate a random transaction hash for simulation."""
        return f"0x{''.join(random.choices('0123456789abcdef', k=64))}"

    def _get_current_timestamp(self) -> str:
        """Get current timestamp as ISO string."""
        from datetime import datetime, timezone

        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class ExternalWalletInterface:
    """Interface for external wallet/blockchain integration."""

    def send_transaction(
        self, from_address: str, to_address: str, amount: Decimal, asset: Asset
    ) -> str:
        """Send transaction to external wallet/blockchain."""
        # Simulate external API call
        # In a real implementation, this would call actual blockchain APIs
        import hashlib
        import time

        tx_data = f"{from_address}_{to_address}_{amount}_{asset.value}_{time.time()}"
        tx_hash = hashlib.sha256(tx_data.encode()).hexdigest()
        return f"0x{tx_hash}"

    def get_transaction_status(self, tx_hash: str) -> Dict:
        """Get transaction status from blockchain."""
        # Simulate blockchain API call
        # In a real implementation, this would query actual blockchain
        import random

        statuses = ["pending", "confirmed", "failed"]
        status = random.choice(statuses)

        return {
            "tx_hash": tx_hash,
            "status": status,
            "confirmations": random.randint(0, 12) if status == "confirmed" else 0,
            "block_height": (
                random.randint(1000000, 2000000) if status == "confirmed" else None
            ),
        }
