"""
Core enums 테스트
"""

import pytest

from alt_exchange.core.enums import (AccountStatus, Asset, OrderStatus,
                                     OrderType, Side, TimeInForce,
                                     TransactionStatus, TransactionType)


class TestAccountStatus:
    def test_account_status_values(self):
        assert AccountStatus.ACTIVE == "active"
        assert AccountStatus.FROZEN == "frozen"


class TestAsset:
    def test_asset_values(self):
        assert Asset.ALT == "ALT"
        assert Asset.USDT == "USDT"


class TestSide:
    def test_side_values(self):
        assert Side.BUY == "buy"
        assert Side.SELL == "sell"


class TestOrderType:
    def test_order_type_values(self):
        assert OrderType.LIMIT == "limit"
        assert OrderType.MARKET == "market"
        assert OrderType.OCO == "oco"
        assert OrderType.STOP == "stop"


class TestOrderStatus:
    def test_order_status_values(self):
        assert OrderStatus.OPEN == "open"
        assert OrderStatus.PARTIAL == "partial"
        assert OrderStatus.FILLED == "filled"
        assert OrderStatus.CANCELED == "canceled"


class TestTimeInForce:
    def test_time_in_force_values(self):
        assert TimeInForce.GTC == "GTC"
        assert TimeInForce.IOC == "IOC"
        assert TimeInForce.FOK == "FOK"


class TestTransactionType:
    def test_transaction_type_values(self):
        assert TransactionType.DEPOSIT == "deposit"
        assert TransactionType.WITHDRAW == "withdraw"


class TestTransactionStatus:
    def test_transaction_status_values(self):
        assert TransactionStatus.PENDING == "pending"
        assert TransactionStatus.CONFIRMED == "confirmed"
        assert TransactionStatus.FAILED == "failed"
