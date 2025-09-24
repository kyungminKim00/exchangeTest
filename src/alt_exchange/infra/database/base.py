"""
Base database interface and abstract classes
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Protocol, TypeVar

from alt_exchange.core.enums import Asset
from alt_exchange.core.models import (
    Account,
    AuditLog,
    Balance,
    Order,
    Trade,
    Transaction,
    User,
)

T = TypeVar("T")


class Database(ABC):
    """Abstract database interface"""

    @abstractmethod
    def next_id(self, table: str) -> int:
        """Generate next ID for a table"""
        pass

    # User operations
    @abstractmethod
    def insert_user(self, user: User) -> User:
        """Insert a new user"""
        pass

    @abstractmethod
    def get_user(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        pass

    @abstractmethod
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        pass

    # Account operations
    @abstractmethod
    def insert_account(self, account: Account) -> Account:
        """Insert a new account"""
        pass

    @abstractmethod
    def get_account(self, account_id: int) -> Optional[Account]:
        """Get account by ID"""
        pass

    @abstractmethod
    def get_accounts_by_user(self, user_id: int) -> List[Account]:
        """Get all accounts for a user"""
        pass

    # Balance operations
    @abstractmethod
    def upsert_balance(self, balance: Balance) -> Balance:
        """Insert or update balance"""
        pass

    @abstractmethod
    def find_balance(self, account_id: int, asset: Asset) -> Optional[Balance]:
        """Find balance by account and asset"""
        pass

    @abstractmethod
    def get_balances_by_account(self, account_id: int) -> List[Balance]:
        """Get all balances for an account"""
        pass

    # Order operations
    @abstractmethod
    def insert_order(self, order: Order) -> Order:
        """Insert a new order"""
        pass

    @abstractmethod
    def update_order(self, order: Order) -> None:
        """Update an existing order"""
        pass

    @abstractmethod
    def get_order(self, order_id: int) -> Optional[Order]:
        """Get order by ID"""
        pass

    @abstractmethod
    def get_orders_by_user(self, user_id: int) -> List[Order]:
        """Get all orders for a user"""
        pass

    @abstractmethod
    def get_orders_by_account(self, account_id: int) -> List[Order]:
        """Get all orders for an account"""
        pass

    # Trade operations
    @abstractmethod
    def insert_trade(self, trade: Trade) -> Trade:
        """Insert a new trade"""
        pass

    @abstractmethod
    def get_trade(self, trade_id: int) -> Optional[Trade]:
        """Get trade by ID"""
        pass

    @abstractmethod
    def get_trades_by_user(self, user_id: int) -> List[Trade]:
        """Get all trades for a user"""
        pass

    # Transaction operations
    @abstractmethod
    def insert_transaction(self, transaction: Transaction) -> Transaction:
        """Insert a new transaction"""
        pass

    @abstractmethod
    def update_transaction(self, transaction: Transaction) -> None:
        """Update an existing transaction"""
        pass

    @abstractmethod
    def get_transaction(self, transaction_id: int) -> Optional[Transaction]:
        """Get transaction by ID"""
        pass

    @abstractmethod
    def get_transactions_by_user(self, user_id: int) -> List[Transaction]:
        """Get all transactions for a user"""
        pass

    # Audit log operations
    @abstractmethod
    def insert_audit(self, audit_log: AuditLog) -> AuditLog:
        """Insert a new audit log"""
        pass

    @abstractmethod
    def get_audit_logs(self, limit: int = 100) -> List[AuditLog]:
        """Get recent audit logs"""
        pass


class UnitOfWork(Protocol):
    """Unit of Work pattern for transactional operations"""

    def __enter__(self) -> "UnitOfWork":
        """Start transaction"""
        pass

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """End transaction"""
        pass

    def commit(self) -> None:
        """Commit transaction"""
        pass

    def rollback(self) -> None:
        """Rollback transaction"""
        pass
