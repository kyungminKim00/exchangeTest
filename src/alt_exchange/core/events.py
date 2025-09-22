from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from .enums import Asset, OrderStatus, Side


@dataclass(slots=True)
class OrderAccepted:
    order_id: int
    market: str
    side: Side
    remaining: Decimal


@dataclass(slots=True)
class TradeExecuted:
    trade_id: int
    market: str
    price: Decimal
    amount: Decimal
    maker_order_id: int
    taker_order_id: int
    taker_side: Side


@dataclass(slots=True)
class BalanceChanged:
    account_id: int
    asset: Asset
    available: Decimal
    locked: Decimal
    reason: str


@dataclass(slots=True)
class OrderStatusChanged:
    order_id: int
    status: OrderStatus
    filled: Decimal
    remaining: Decimal
    reason: Optional[str] = None
