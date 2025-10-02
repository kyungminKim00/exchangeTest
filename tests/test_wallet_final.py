"""Tests for wallet/service.py to improve coverage to 95%."""

from decimal import Decimal
from unittest.mock import Mock, patch

import pytest

from alt_exchange.core.enums import Asset, TransactionStatus, TransactionType
from alt_exchange.core.models import Transaction
from alt_exchange.services.wallet.service import (ExternalWalletInterface,
                                                  WalletService)


class TestWalletFinal:
    """Test class for final coverage of wallet/service.py."""

    @pytest.fixture
    def mock_account_service(self):
        """Mock AccountService."""
        return Mock()

    @pytest.fixture
    def wallet_service(self, mock_account_service):
        """WalletService instance."""
        return WalletService(mock_account_service)

    def test_wallet_service_init(self, mock_account_service):
        """Test WalletService initialization."""
        service = WalletService(mock_account_service)
        assert service.account_service is mock_account_service
        assert service.pending_withdrawals == {}
        assert service.deposit_addresses == {}
        assert isinstance(service.external_wallet_interface, ExternalWalletInterface)

    def test_generate_deposit_address_new(self, wallet_service):
        """Test generate_deposit_address for new address."""
        address = wallet_service.generate_deposit_address(1, Asset.USDT)

        assert address.startswith("0x")
        assert len(address) == 42  # 0x + 40 hex chars
        assert address in wallet_service.deposit_addresses
        assert wallet_service.deposit_addresses[address]["user_id"] == 1
        assert wallet_service.deposit_addresses[address]["asset"] == Asset.USDT

    def test_generate_deposit_address_existing(self, wallet_service):
        """Test generate_deposit_address for existing address."""
        # Generate first address
        address1 = wallet_service.generate_deposit_address(1, Asset.USDT)

        # Generate second address for same user/asset
        address2 = wallet_service.generate_deposit_address(1, Asset.USDT)

        assert address1 == address2
        assert len(wallet_service.deposit_addresses) == 1

    def test_generate_deposit_address_different_users(self, wallet_service):
        """Test generate_deposit_address for different users."""
        address1 = wallet_service.generate_deposit_address(1, Asset.USDT)
        address2 = wallet_service.generate_deposit_address(2, Asset.USDT)

        assert address1 != address2
        assert len(wallet_service.deposit_addresses) == 2

    def test_generate_deposit_address_different_assets(self, wallet_service):
        """Test generate_deposit_address for different assets."""
        address1 = wallet_service.generate_deposit_address(1, Asset.USDT)
        address2 = wallet_service.generate_deposit_address(1, Asset.ALT)

        assert address1 != address2
        assert len(wallet_service.deposit_addresses) == 2

    def test_get_deposit_address_existing(self, wallet_service):
        """Test get_deposit_address for existing address."""
        # Generate address first
        address1 = wallet_service.generate_deposit_address(1, Asset.USDT)

        # Get existing address
        address2 = wallet_service.get_deposit_address(1, Asset.USDT)

        assert address1 == address2

    def test_get_deposit_address_new(self, wallet_service):
        """Test get_deposit_address for new address."""
        address = wallet_service.get_deposit_address(1, Asset.USDT)

        assert address.startswith("0x")
        assert len(address) == 42
        assert address in wallet_service.deposit_addresses

    def test_send_withdrawal(self, wallet_service):
        """Test send_withdrawal."""
        tx_hash = wallet_service.send_withdrawal(
            1, Asset.USDT, Decimal("100.0"), "0x123"
        )

        assert tx_hash.startswith("0x")
        assert len(tx_hash) == 66  # 0x + 64 hex chars

    def test_check_transaction_status(self, wallet_service):
        """Test check_transaction_status."""
        status = wallet_service.check_transaction_status("0x123")

        assert "tx_hash" in status
        assert "status" in status
        assert "confirmations" in status
        assert status["tx_hash"] == "0x123"

    def test_simulate_deposit_with_tx_hash(self, wallet_service, mock_account_service):
        """Test simulate_deposit with provided tx_hash."""
        mock_transaction = Transaction(
            id=1,
            user_id=1,
            tx_hash="0x123",
            chain="ethereum",
            asset=Asset.USDT,
            type=TransactionType.DEPOSIT,
            status=TransactionStatus.PENDING,
            confirmations=0,
            amount=Decimal("100.0"),
            address=None,
        )
        mock_account_service.credit_deposit.return_value = mock_transaction

        result = wallet_service.simulate_deposit(
            1, Asset.USDT, Decimal("100.0"), "0x123"
        )

        assert result == mock_transaction
        mock_account_service.credit_deposit.assert_called_once_with(
            user_id=1, asset=Asset.USDT, amount=Decimal("100.0"), tx_hash="0x123"
        )

    def test_simulate_deposit_without_tx_hash(
        self, wallet_service, mock_account_service
    ):
        """Test simulate_deposit without provided tx_hash."""
        mock_transaction = Transaction(
            id=1,
            user_id=1,
            tx_hash="0x456",
            chain="ethereum",
            asset=Asset.USDT,
            type=TransactionType.DEPOSIT,
            status=TransactionStatus.PENDING,
            confirmations=0,
            amount=Decimal("100.0"),
            address=None,
        )
        mock_account_service.credit_deposit.return_value = mock_transaction

        result = wallet_service.simulate_deposit(1, Asset.USDT, Decimal("100.0"))

        assert result == mock_transaction
        mock_account_service.credit_deposit.assert_called_once()
        # Check that a tx_hash was generated
        call_args = mock_account_service.credit_deposit.call_args
        assert call_args[1]["tx_hash"].startswith("0x")

    def test_request_withdrawal(self, wallet_service, mock_account_service):
        """Test request_withdrawal."""
        mock_transaction = Transaction(
            id=1,
            user_id=1,
            tx_hash=None,
            chain="ethereum",
            asset=Asset.USDT,
            type=TransactionType.WITHDRAW,
            status=TransactionStatus.PENDING,
            confirmations=0,
            amount=Decimal("100.0"),
            address="0x123",
        )
        mock_account_service.request_withdrawal.return_value = mock_transaction

        result = wallet_service.request_withdrawal(
            1, Asset.USDT, Decimal("100.0"), "0x123"
        )

        assert result == mock_transaction
        assert 1 in wallet_service.pending_withdrawals
        assert wallet_service.pending_withdrawals[1] == mock_transaction
        mock_account_service.request_withdrawal.assert_called_once_with(
            user_id=1, asset=Asset.USDT, amount=Decimal("100.0"), address="0x123"
        )

    def test_complete_withdrawal(self, wallet_service, mock_account_service):
        """Test complete_withdrawal."""
        mock_transaction = Transaction(
            id=1,
            user_id=1,
            tx_hash="0x123",
            chain="ethereum",
            asset=Asset.USDT,
            type=TransactionType.WITHDRAW,
            status=TransactionStatus.CONFIRMED,
            confirmations=6,
            amount=Decimal("100.0"),
            address="0x456",
        )
        mock_account_service.complete_withdrawal.return_value = mock_transaction

        # Add to pending withdrawals first
        wallet_service.pending_withdrawals[1] = mock_transaction

        result = wallet_service.complete_withdrawal(1, "0x123")

        assert result == mock_transaction
        assert 1 not in wallet_service.pending_withdrawals
        mock_account_service.complete_withdrawal.assert_called_once_with(
            tx_id=1, tx_hash="0x123"
        )

    def test_complete_withdrawal_not_pending(
        self, wallet_service, mock_account_service
    ):
        """Test complete_withdrawal when not in pending withdrawals."""
        mock_transaction = Transaction(
            id=1,
            user_id=1,
            tx_hash="0x123",
            chain="ethereum",
            asset=Asset.USDT,
            type=TransactionType.WITHDRAW,
            status=TransactionStatus.CONFIRMED,
            confirmations=6,
            amount=Decimal("100.0"),
            address="0x456",
        )
        mock_account_service.complete_withdrawal.return_value = mock_transaction

        result = wallet_service.complete_withdrawal(1, "0x123")

        assert result == mock_transaction
        mock_account_service.complete_withdrawal.assert_called_once_with(
            tx_id=1, tx_hash="0x123"
        )

    def test_get_exchange_wallet_address_alt(self, wallet_service):
        """Test _get_exchange_wallet_address for ALT."""
        address = wallet_service._get_exchange_wallet_address(Asset.ALT)
        assert address == "0xEXCHANGE_ALT_WALLET"

    def test_get_exchange_wallet_address_usdt(self, wallet_service):
        """Test _get_exchange_wallet_address for USDT."""
        address = wallet_service._get_exchange_wallet_address(Asset.USDT)
        assert address == "0xEXCHANGE_USDT_WALLET"

    def test_get_exchange_wallet_address_default(self, wallet_service):
        """Test _get_exchange_wallet_address for unknown asset."""

        # Create a mock asset that's not in the exchange_addresses dict
        class MockAsset:
            def __init__(self, value):
                self.value = value

        mock_asset = MockAsset("UNKNOWN")
        address = wallet_service._get_exchange_wallet_address(mock_asset)
        assert address == "0xEXCHANGE_DEFAULT_WALLET"

    def test_generate_tx_hash(self, wallet_service):
        """Test _generate_tx_hash."""
        tx_hash = wallet_service._generate_tx_hash()

        assert tx_hash.startswith("0x")
        assert len(tx_hash) == 66  # 0x + 64 hex chars

    def test_get_current_timestamp(self, wallet_service):
        """Test _get_current_timestamp."""
        timestamp = wallet_service._get_current_timestamp()

        assert timestamp.endswith("Z")
        assert "T" in timestamp


class TestExternalWalletInterface:
    """Test class for ExternalWalletInterface."""

    @pytest.fixture
    def external_wallet(self):
        """ExternalWalletInterface instance."""
        return ExternalWalletInterface()

    def test_send_transaction(self, external_wallet):
        """Test send_transaction."""
        tx_hash = external_wallet.send_transaction(
            "0xfrom", "0xto", Decimal("100.0"), Asset.USDT
        )

        assert tx_hash.startswith("0x")
        assert len(tx_hash) == 66  # 0x + 64 hex chars

    def test_get_transaction_status(self, external_wallet):
        """Test get_transaction_status."""
        status = external_wallet.get_transaction_status("0x123")

        assert "tx_hash" in status
        assert "status" in status
        assert "confirmations" in status
        assert "block_height" in status
        assert status["tx_hash"] == "0x123"
        assert status["status"] in ["pending", "confirmed", "failed"]
