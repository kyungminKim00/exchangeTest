"""
In-memory database implementation for testing
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import replace
from itertools import count
from typing import List, Optional

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
from alt_exchange.infra.database.base import Database, UnitOfWork


class InMemoryDatabase(Database):
    """In-memory database implementation for testing"""

    def __init__(self) -> None:
        self.users: dict[int, User] = {}
        self.accounts: dict[int, Account] = {}
        self.balances: dict[int, Balance] = {}
        self.orders: dict[int, Order] = {}
        self.trades: dict[int, Trade] = {}
        self.transactions: dict[int, Transaction] = {}
        self.audit_logs: dict[int, AuditLog] = {}
        self._balance_index: dict[tuple[int, Asset], int] = {}
        self._counters = defaultdict(lambda: count(1))

    def next_id(self, table: str) -> int:
        return next(self._counters[table])

    # User operations
    def insert_user(self, user: User) -> User:
        self.users[user.id] = user
        return user

    def get_user(self, user_id: int) -> Optional[User]:
        return self.users.get(user_id)

    def get_user_by_email(self, email: str) -> Optional[User]:
        for user in self.users.values():
            if user.email == email:
                return user
        return None

    # Account operations
    def insert_account(self, account: Account) -> Account:
        self.accounts[account.id] = account
        return account

    def get_account(self, account_id: int) -> Optional[Account]:
        return self.accounts.get(account_id)

    def get_accounts_by_user(self, user_id: int) -> List[Account]:
        return [acc for acc in self.accounts.values() if acc.user_id == user_id]

    # Balance operations
    def upsert_balance(self, balance: Balance) -> Balance:
        key = (balance.account_id, balance.asset)
        self._balance_index[key] = balance.id
        self.balances[balance.id] = balance
        return balance

    def find_balance(self, account_id: int, asset: Asset) -> Optional[Balance]:
        balance_id = self._balance_index.get((account_id, asset))
        if balance_id is None:
            return None
        return self.balances.get(balance_id)

    def get_balances_by_account(self, account_id: int) -> List[Balance]:
        return [bal for bal in self.balances.values() if bal.account_id == account_id]

    # Order operations
    def insert_order(self, order: Order) -> Order:
        self.orders[order.id] = order
        return order

    def update_order(self, order: Order) -> None:
        self.orders[order.id] = order

    def get_order(self, order_id: int) -> Optional[Order]:
        return self.orders.get(order_id)

    def get_orders_by_user(self, user_id: int) -> List[Order]:
        return [order for order in self.orders.values() if order.user_id == user_id]

    def get_orders_by_account(self, account_id: int) -> List[Order]:
        return [
            order for order in self.orders.values() if order.account_id == account_id
        ]

    # Trade operations
    def insert_trade(self, trade: Trade) -> Trade:
        self.trades[trade.id] = trade
        return trade

    def get_trade(self, trade_id: int) -> Optional[Trade]:
        return self.trades.get(trade_id)

    def get_trades_by_user(self, user_id: int) -> List[Trade]:
        # Get trades where user is either buyer or seller
        user_orders = {
            order.id for order in self.orders.values() if order.user_id == user_id
        }
        return [
            trade
            for trade in self.trades.values()
            if trade.buy_order_id in user_orders or trade.sell_order_id in user_orders
        ]

    # Transaction operations
    def insert_transaction(self, transaction: Transaction) -> Transaction:
        self.transactions[transaction.id] = transaction
        return transaction

    def update_transaction(self, transaction: Transaction) -> None:
        self.transactions[transaction.id] = transaction

    def get_transaction(self, transaction_id: int) -> Optional[Transaction]:
        return self.transactions.get(transaction_id)

    def get_transactions_by_user(self, user_id: int) -> List[Transaction]:
        return [tx for tx in self.transactions.values() if tx.user_id == user_id]

    # Audit log operations
    def insert_audit(self, audit_log: AuditLog) -> AuditLog:
        self.audit_logs[audit_log.id] = audit_log
        return audit_log

    def get_audit_logs(self, limit: int = 100) -> List[AuditLog]:
        sorted_logs = sorted(
            self.audit_logs.values(), key=lambda x: x.created_at, reverse=True
        )
        return sorted_logs[:limit]

    # Snapshot management for testing
    def clone(self) -> "InMemoryDatabase":
        """Create a shallow copy for testing"""
        new_db = InMemoryDatabase()
        new_db.users = self.users.copy()
        new_db.accounts = self.accounts.copy()
        new_db.balances = self.balances.copy()
        new_db.orders = self.orders.copy()
        new_db.trades = self.trades.copy()
        new_db.transactions = self.transactions.copy()
        new_db.audit_logs = self.audit_logs.copy()
        new_db._balance_index = self._balance_index.copy()
        new_db._counters = defaultdict(lambda: count(1))
        return new_db

    def restore(self, snapshot: "InMemoryDatabase") -> None:
        """Restore from snapshot"""
        self.users = snapshot.users
        self.accounts = snapshot.accounts
        self.balances = snapshot.balances
        self.orders = snapshot.orders
        self.trades = snapshot.trades
        self.transactions = snapshot.transactions
        self.audit_logs = snapshot.audit_logs
        self._balance_index = snapshot._balance_index
        self._counters = snapshot._counters


class InMemoryUnitOfWork(UnitOfWork):
    """In-memory implementation of Unit of Work"""

    def __init__(self, db: InMemoryDatabase) -> None:
        self.db = db
        self._snapshot: Optional[InMemoryDatabase] = None
        self._committed = False

    def __enter__(self) -> "InMemoryUnitOfWork":
        self._snapshot = self.db.clone()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_val is not None or not self._committed:
            # Rollback to snapshot
            assert self._snapshot is not None
            self.db.restore(self._snapshot)
        self._snapshot = None
        self._committed = False

    def commit(self) -> None:
        self._committed = True

    def rollback(self) -> None:
        if self._snapshot is not None:
            self.db.restore(self._snapshot)
        self._committed = True


def copy_order(order: Order, **changes) -> Order:
    """Helper function to create a copy of an order with changes"""
    return replace(order, **changes)
