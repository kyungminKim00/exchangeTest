"""
Core events 테스트
"""

from decimal import Decimal

import pytest

from alt_exchange.core.enums import Asset, OrderStatus, Side
from alt_exchange.core.events import (AccountFrozen, AccountUnfrozen,
                                      BalanceChanged, OCOOrderCancelled,
                                      OrderAccepted, OrderStatusChanged,
                                      StopOrderActivated, TradeExecuted,
                                      WithdrawalApproved, WithdrawalRejected,
                                      WithdrawalRequested)


class TestOrderAccepted:
    def test_order_accepted_creation(self):
        event = OrderAccepted(
            order_id=1, market="ALT/USDT", side=Side.BUY, remaining=Decimal("10.0")
        )
        assert event.order_id == 1
        assert event.market == "ALT/USDT"
        assert event.side == Side.BUY
        assert event.remaining == Decimal("10.0")


class TestTradeExecuted:
    def test_trade_executed_creation(self):
        event = TradeExecuted(
            trade_id=1,
            market="ALT/USDT",
            price=Decimal("100.0"),
            amount=Decimal("5.0"),
            maker_order_id=1,
            taker_order_id=2,
            taker_side=Side.BUY,
        )
        assert event.trade_id == 1
        assert event.market == "ALT/USDT"
        assert event.price == Decimal("100.0")
        assert event.amount == Decimal("5.0")
        assert event.maker_order_id == 1
        assert event.taker_order_id == 2
        assert event.taker_side == Side.BUY


class TestBalanceChanged:
    def test_balance_changed_creation(self):
        event = BalanceChanged(
            account_id=1,
            asset=Asset.ALT,
            available=Decimal("100.0"),
            locked=Decimal("10.0"),
            reason="deposit",
        )
        assert event.account_id == 1
        assert event.asset == Asset.ALT
        assert event.available == Decimal("100.0")
        assert event.locked == Decimal("10.0")
        assert event.reason == "deposit"


class TestOrderStatusChanged:
    def test_order_status_changed_creation(self):
        event = OrderStatusChanged(
            order_id=1,
            status=OrderStatus.FILLED,
            filled=Decimal("10.0"),
            remaining=Decimal("0.0"),
        )
        assert event.order_id == 1
        assert event.status == OrderStatus.FILLED
        assert event.filled == Decimal("10.0")
        assert event.remaining == Decimal("0.0")

    def test_order_status_changed_with_reason(self):
        event = OrderStatusChanged(
            order_id=1,
            status=OrderStatus.CANCELED,
            filled=Decimal("5.0"),
            remaining=Decimal("5.0"),
            reason="user_canceled",
        )
        assert event.order_id == 1
        assert event.status == OrderStatus.CANCELED
        assert event.filled == Decimal("5.0")
        assert event.remaining == Decimal("5.0")
        assert event.reason == "user_canceled"


class TestStopOrderActivated:
    def test_stop_order_activated_creation(self):
        event = StopOrderActivated(
            order_id=1,
            market="ALT/USDT",
            stop_price=Decimal("90.0"),
            activated_price=Decimal("95.0"),
        )
        assert event.order_id == 1
        assert event.market == "ALT/USDT"
        assert event.stop_price == Decimal("90.0")
        assert event.activated_price == Decimal("95.0")


class TestOCOOrderCancelled:
    def test_oco_order_cancelled_creation(self):
        event = OCOOrderCancelled(
            order_id=1, linked_order_id=2, reason="linked_order_filled"
        )
        assert event.order_id == 1
        assert event.linked_order_id == 2
        assert event.reason == "linked_order_filled"


class TestWithdrawalRequested:
    def test_withdrawal_requested_creation(self):
        event = WithdrawalRequested(
            transaction_id=1,
            user_id=1,
            asset=Asset.ALT,
            amount=Decimal("100.0"),
            address="0xabc",
        )
        assert event.transaction_id == 1
        assert event.user_id == 1
        assert event.asset == Asset.ALT
        assert event.amount == Decimal("100.0")
        assert event.address == "0xabc"


class TestWithdrawalApproved:
    def test_withdrawal_approved_creation(self):
        event = WithdrawalApproved(
            transaction_id=1, approver_id=1, approved_at="2024-01-01T00:00:00Z"
        )
        assert event.transaction_id == 1
        assert event.approver_id == 1
        assert event.approved_at == "2024-01-01T00:00:00Z"


class TestWithdrawalRejected:
    def test_withdrawal_rejected_creation(self):
        event = WithdrawalRejected(
            transaction_id=1,
            approver_id=1,
            reason="insufficient_balance",
            rejected_at="2024-01-01T00:00:00Z",
        )
        assert event.transaction_id == 1
        assert event.approver_id == 1
        assert event.reason == "insufficient_balance"
        assert event.rejected_at == "2024-01-01T00:00:00Z"


class TestAccountFrozen:
    def test_account_frozen_creation(self):
        event = AccountFrozen(
            account_id=1, user_id=1, frozen_by=1, reason="suspicious_activity"
        )
        assert event.account_id == 1
        assert event.user_id == 1
        assert event.frozen_by == 1
        assert event.reason == "suspicious_activity"


class TestAccountUnfrozen:
    def test_account_unfrozen_creation(self):
        event = AccountUnfrozen(account_id=1, user_id=1, unfrozen_by=1)
        assert event.account_id == 1
        assert event.user_id == 1
        assert event.unfrozen_by == 1
