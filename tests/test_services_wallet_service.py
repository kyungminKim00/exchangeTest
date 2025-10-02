"""
Wallet Service 테스트
"""

from decimal import Decimal

import pytest

from alt_exchange.core.enums import Asset, TransactionStatus, TransactionType
from alt_exchange.core.models import Transaction
from alt_exchange.infra.database.in_memory import InMemoryDatabase
from alt_exchange.infra.event_bus import InMemoryEventBus
from alt_exchange.services.account.service import AccountService
from alt_exchange.services.matching.engine import MatchingEngine
from alt_exchange.services.wallet.service import (ExternalWalletInterface,
                                                  WalletService)


class TestExternalWalletInterface:
    def test_send_transaction(self):
        interface = ExternalWalletInterface()
        tx_hash = interface.send_transaction(
            from_address="0x123",
            to_address="0x456",
            amount=Decimal("100.0"),
            asset=Asset.ALT,
        )

        assert tx_hash is not None
        assert len(tx_hash) > 0

    def test_get_transaction_status(self):
        interface = ExternalWalletInterface()
        status = interface.get_transaction_status("0x123")

        assert status is not None
        assert "status" in status


class TestWalletService:
    def setup_method(self):
        self.db = InMemoryDatabase()
        self.event_bus = InMemoryEventBus()
        self.matching_engine = MatchingEngine("ALT/USDT", self.db, self.event_bus)
        self.account_service = AccountService(
            self.db, self.event_bus, self.matching_engine
        )
        self.service = WalletService(self.account_service)

    def test_generate_deposit_address(self):
        address = self.service.generate_deposit_address(1, Asset.ALT)

        assert address is not None
        assert address.startswith("0x")
        assert len(address) == 42  # Ethereum address length

    def test_get_deposit_address(self):
        # First call should generate new address
        address1 = self.service.get_deposit_address(1, Asset.ALT)
        assert address1 is not None

        # Second call should return same address
        address2 = self.service.get_deposit_address(1, Asset.ALT)
        assert address1 == address2

    def test_send_withdrawal(self):
        tx_hash = self.service.send_withdrawal(
            user_id=1, asset=Asset.ALT, amount=Decimal("100.0"), address="0x456"
        )

        assert tx_hash is not None
        assert len(tx_hash) > 0

    def test_check_transaction_status(self):
        status = self.service.check_transaction_status("0x123")

        assert status is not None
        assert "status" in status

    def test_simulate_deposit(self):
        user = self.account_service.create_user("test@example.com", "password123")

        transaction = self.service.simulate_deposit(
            user_id=user.id, asset=Asset.ALT, amount=Decimal("100.0"), tx_hash="0x123"
        )

        assert transaction.user_id == user.id
        assert transaction.asset == Asset.ALT
        assert transaction.amount == Decimal("100.0")
        assert transaction.tx_hash == "0x123"
        assert transaction.type == TransactionType.DEPOSIT
        assert transaction.status == TransactionStatus.CONFIRMED

    def test_request_withdrawal(self):
        user = self.account_service.create_user("test@example.com", "password123")

        # Add some balance first
        account = self.account_service.get_account(user.id)
        balance = self.account_service.get_balance(user.id, Asset.ALT)
        balance.available = Decimal("1000.0")
        self.db.upsert_balance(balance)

        transaction = self.service.request_withdrawal(
            user_id=user.id, asset=Asset.ALT, amount=Decimal("100.0"), address="0x456"
        )

        assert transaction.user_id == user.id
        assert transaction.asset == Asset.ALT
        assert transaction.amount == Decimal("100.0")
        assert transaction.address == "0x456"
        assert transaction.type == TransactionType.WITHDRAW
        assert transaction.status == TransactionStatus.PENDING

    def test_complete_withdrawal(self):
        user = self.account_service.create_user("test@example.com", "password123")

        # Add some balance first
        account = self.account_service.get_account(user.id)
        balance = self.account_service.get_balance(user.id, Asset.ALT)
        balance.available = Decimal("1000.0")
        self.db.upsert_balance(balance)

        # Request withdrawal
        transaction = self.service.request_withdrawal(
            user_id=user.id, asset=Asset.ALT, amount=Decimal("100.0"), address="0x456"
        )

        # Complete withdrawal
        completed_transaction = self.service.complete_withdrawal(
            tx_id=transaction.id, tx_hash="0x789"
        )

        assert completed_transaction.tx_hash == "0x789"
        assert completed_transaction.status == TransactionStatus.CONFIRMED
