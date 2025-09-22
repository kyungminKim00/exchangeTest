from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from .enums import (
    AccountStatus,
    Asset,
    OrderStatus,
    OrderType,
    Side,
    TimeInForce,
    TransactionStatus,
    TransactionType,
)


@dataclass(slots=True)
class User:
    id: int
    email: str
    password_hash: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_login: Optional[datetime] = None


@dataclass(slots=True)
class Account:
    id: int
    user_id: int
    status: AccountStatus = AccountStatus.ACTIVE
    kyc_level: int = 0


@dataclass(slots=True)
class Balance:
    id: int
    account_id: int
    asset: Asset
    available: Decimal = Decimal("0")
    locked: Decimal = Decimal("0")
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(slots=True)
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
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def remaining(self) -> Decimal:
        return self.amount - self.filled


@dataclass(slots=True)
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


@dataclass(slots=True)
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
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(slots=True)
class AuditLog:
    id: int
    actor: str
    action: str
    entity: str
    metadata: dict
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
