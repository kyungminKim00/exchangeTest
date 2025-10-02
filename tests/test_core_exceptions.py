"""
Core exceptions 테스트
"""

import pytest

from alt_exchange.core.exceptions import (AdminPermissionError,
                                          EntityNotFoundError, ExchangeError,
                                          InsufficientBalanceError,
                                          InvalidOrderError, OrderLinkError,
                                          SettlementError, StopOrderError,
                                          WithdrawalApprovalError)


class TestExchangeError:
    def test_exchange_error_creation(self):
        error = ExchangeError("Test error message")
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)


class TestInsufficientBalanceError:
    def test_insufficient_balance_error_creation(self):
        error = InsufficientBalanceError("Insufficient balance")
        assert str(error) == "Insufficient balance"
        assert isinstance(error, ExchangeError)


class TestInvalidOrderError:
    def test_invalid_order_error_creation(self):
        error = InvalidOrderError("Invalid order")
        assert str(error) == "Invalid order"
        assert isinstance(error, ExchangeError)


class TestEntityNotFoundError:
    def test_entity_not_found_error_creation(self):
        error = EntityNotFoundError("Entity not found")
        assert str(error) == "Entity not found"
        assert isinstance(error, ExchangeError)


class TestSettlementError:
    def test_settlement_error_creation(self):
        error = SettlementError("Settlement failed")
        assert str(error) == "Settlement failed"
        assert isinstance(error, ExchangeError)


class TestOrderLinkError:
    def test_order_link_error_creation(self):
        error = OrderLinkError("Order link error")
        assert str(error) == "Order link error"
        assert isinstance(error, ExchangeError)


class TestStopOrderError:
    def test_stop_order_error_creation(self):
        error = StopOrderError("Stop order error")
        assert str(error) == "Stop order error"
        assert isinstance(error, ExchangeError)


class TestAdminPermissionError:
    def test_admin_permission_error_creation(self):
        error = AdminPermissionError("Admin permission denied")
        assert str(error) == "Admin permission denied"
        assert isinstance(error, ExchangeError)


class TestWithdrawalApprovalError:
    def test_withdrawal_approval_error_creation(self):
        error = WithdrawalApprovalError("Withdrawal approval failed")
        assert str(error) == "Withdrawal approval failed"
        assert isinstance(error, ExchangeError)
