"""
Repository interfaces following Interface Segregation Principle
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from alt_exchange.core.enums import Asset
from alt_exchange.core.models import (Account, AuditLog, Balance, Order, Trade,
                                      Transaction, User)


class UserRepository(ABC):
    """Repository interface for User operations"""

    @abstractmethod
    def next_id(self) -> int:
        """Generate next ID for users"""
        pass

    @abstractmethod
    def insert(self, user: User) -> User:
        """Insert a new user"""
        pass

    @abstractmethod
    def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        pass

    @abstractmethod
    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        pass


class AccountRepository(ABC):
    """Repository interface for Account operations"""

    @abstractmethod
    def next_id(self) -> int:
        """Generate next ID for accounts"""
        pass

    @abstractmethod
    def insert(self, account: Account) -> Account:
        """Insert a new account"""
        pass

    @abstractmethod
    def update(self, account: Account) -> None:
        """Update an existing account"""
        pass

    @abstractmethod
    def get_by_id(self, account_id: int) -> Optional[Account]:
        """Get account by ID"""
        pass

    @abstractmethod
    def get_by_user_id(self, user_id: int) -> List[Account]:
        """Get all accounts for a user"""
        pass


class BalanceRepository(ABC):
    """Repository interface for Balance operations"""

    @abstractmethod
    def next_id(self) -> int:
        """Generate next ID for balances"""
        pass

    @abstractmethod
    def upsert(self, balance: Balance) -> Balance:
        """Insert or update balance"""
        pass

    @abstractmethod
    def find_by_account_and_asset(
        self, account_id: int, asset: Asset
    ) -> Optional[Balance]:
        """Find balance by account and asset"""
        pass

    @abstractmethod
    def get_by_account_id(self, account_id: int) -> List[Balance]:
        """Get all balances for an account"""
        pass


class OrderRepository(ABC):
    """Repository interface for Order operations"""

    @abstractmethod
    def next_id(self) -> int:
        """Generate next ID for orders"""
        pass

    @abstractmethod
    def insert(self, order: Order) -> Order:
        """Insert a new order"""
        pass

    @abstractmethod
    def update(self, order: Order) -> None:
        """Update an existing order"""
        pass

    @abstractmethod
    def get_by_id(self, order_id: int) -> Optional[Order]:
        """Get order by ID"""
        pass

    @abstractmethod
    def get_by_user_id(self, user_id: int) -> List[Order]:
        """Get all orders for a user"""
        pass

    @abstractmethod
    def get_by_account_id(self, account_id: int) -> List[Order]:
        """Get all orders for an account"""
        pass


class TradeRepository(ABC):
    """Repository interface for Trade operations"""

    @abstractmethod
    def next_id(self) -> int:
        """Generate next ID for trades"""
        pass

    @abstractmethod
    def insert(self, trade: Trade) -> Trade:
        """Insert a new trade"""
        pass

    @abstractmethod
    def get_by_id(self, trade_id: int) -> Optional[Trade]:
        """Get trade by ID"""
        pass

    @abstractmethod
    def get_by_user_id(self, user_id: int) -> List[Trade]:
        """Get all trades for a user"""
        pass


class TransactionRepository(ABC):
    """Repository interface for Transaction operations"""

    @abstractmethod
    def next_id(self) -> int:
        """Generate next ID for transactions"""
        pass

    @abstractmethod
    def insert(self, transaction: Transaction) -> Transaction:
        """Insert a new transaction"""
        pass

    @abstractmethod
    def update(self, transaction: Transaction) -> None:
        """Update an existing transaction"""
        pass

    @abstractmethod
    def get_by_id(self, transaction_id: int) -> Optional[Transaction]:
        """Get transaction by ID"""
        pass

    @abstractmethod
    def get_by_user_id(self, user_id: int) -> List[Transaction]:
        """Get all transactions for a user"""
        pass


class AuditLogRepository(ABC):
    """Repository interface for AuditLog operations"""

    @abstractmethod
    def next_id(self) -> int:
        """Generate next ID for audit logs"""
        pass

    @abstractmethod
    def insert(self, audit_log: AuditLog) -> AuditLog:
        """Insert a new audit log"""
        pass

    @abstractmethod
    def get_recent(self, limit: int = 100) -> List[AuditLog]:
        """Get recent audit logs"""
        pass
