from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from .enums import Asset, OrderStatus, Side


@dataclass
class OrderAccepted:
    order_id: int
    market: str
    side: Side
    remaining: Decimal


@dataclass
class TradeExecuted:
    trade_id: int
    market: str
    price: Decimal
    amount: Decimal
    maker_order_id: int
    taker_order_id: int
    taker_side: Side


@dataclass
class BalanceChanged:
    account_id: int
    asset: Asset
    available: Decimal
    locked: Decimal
    reason: str


@dataclass
class OrderStatusChanged:
    order_id: int
    status: OrderStatus
    filled: Decimal
    remaining: Decimal
    reason: Optional[str] = None


@dataclass
class StopOrderActivated:
    order_id: int
    market: str
    stop_price: Decimal
    activated_price: Decimal


@dataclass
class OCOOrderCancelled:
    order_id: int
    linked_order_id: int
    reason: str


@dataclass
class WithdrawalRequested:
    transaction_id: int
    user_id: int
    asset: Asset
    amount: Decimal
    address: str


@dataclass
class WithdrawalApproved:
    transaction_id: int
    approver_id: int
    approved_at: str


@dataclass
class WithdrawalRejected:
    transaction_id: int
    approver_id: int
    rejected_at: str
    reason: str


@dataclass
class AccountFrozen:
    account_id: int
    user_id: int
    frozen_by: int
    reason: str


@dataclass
class AccountUnfrozen:
    account_id: int
    user_id: int
    unfrozen_by: int
