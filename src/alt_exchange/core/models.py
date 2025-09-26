from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from .enums import (AccountStatus, Asset, OrderStatus, OrderType, Side,
                    TimeInForce, TransactionStatus, TransactionType)


@dataclass
class User:
    id: int
    email: str
    password_hash: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_login: Optional[datetime] = None


@dataclass
class Account:
    id: int
    user_id: int
    status: AccountStatus = AccountStatus.ACTIVE
    kyc_level: int = 0
    frozen: bool = False  # Additional freeze flag for admin control


@dataclass
class Balance:
    id: int
    account_id: int
    asset: Asset
    available: Decimal = Decimal("0")
    locked: Decimal = Decimal("0")
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class Order:
    id: int
    user_id: int
    account_id: int
    market: str
    side: Side
    type: OrderType
    time_in_force: TimeInForce
    price: Optional[Decimal]
    amount: Decimal
    filled: Decimal = Decimal("0")
    status: OrderStatus = OrderStatus.OPEN
    stop_price: Optional[Decimal] = None  # For STOP and OCO orders
    link_order_id: Optional[int] = None  # For OCO orders - links to paired order
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def remaining(self) -> Decimal:
        return self.amount - self.filled


@dataclass
class Trade:
    id: int
    buy_order_id: int
    sell_order_id: int
    maker_order_id: int
    taker_order_id: int
    taker_side: Side
    price: Decimal
    amount: Decimal
    fee: Decimal
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class Transaction:
    id: int
    user_id: int
    tx_hash: Optional[str]
    chain: str
    asset: Asset
    type: TransactionType
    status: TransactionStatus
    confirmations: int
    amount: Decimal
    address: Optional[str]
    approver_id: Optional[int] = None  # For withdrawal approval
    approved_at: Optional[datetime] = None  # When approved
    rejected_at: Optional[datetime] = None  # When rejected
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class AuditLog:
    id: int
    actor: str
    action: str
    entity: str
    metadata: dict
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
