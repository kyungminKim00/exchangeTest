from __future__ import annotations

import copy
from collections import defaultdict
from dataclasses import replace
from itertools import count
from typing import Dict, Iterable, Optional

from alt_exchange.core.enums import Asset
from alt_exchange.core.models import Account, AuditLog, Balance, Order, Trade, Transaction, User


class InMemoryDatabase:
    """Naive in-memory datastore with copy-on-write semantics for testing."""

    def __init__(self) -> None:
        self.users: Dict[int, User] = {}
        self.accounts: Dict[int, Account] = {}
        self.balances: Dict[int, Balance] = {}
        self.orders: Dict[int, Order] = {}
        self.trades: Dict[int, Trade] = {}
        self.transactions: Dict[int, Transaction] = {}
        self.audit_logs: Dict[int, AuditLog] = {}
        self._balance_index: Dict[tuple[int, Asset], int] = {}
        self._counters = defaultdict(lambda: count(1))

    def next_id(self, table: str) -> int:
        return next(self._counters[table])

    # --- CRUD helpers -----------------------------------------------------
    def insert_user(self, user: User) -> User:
        self.users[user.id] = user
        return user

    def insert_account(self, account: Account) -> Account:
        self.accounts[account.id] = account
        return account

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

    def insert_order(self, order: Order) -> Order:
        self.orders[order.id] = order
        return order

    def update_order(self, order: Order) -> None:
        self.orders[order.id] = order

    def insert_trade(self, trade: Trade) -> Trade:
        self.trades[trade.id] = trade
        return trade

    def insert_transaction(self, tx: Transaction) -> Transaction:
        self.transactions[tx.id] = tx
        return tx

    def insert_audit(self, log: AuditLog) -> AuditLog:
        self.audit_logs[log.id] = log
        return log

    # --- snapshot management ----------------------------------------------
    def clone(self) -> "InMemoryDatabase":
        new_db = InMemoryDatabase()
        new_db.users = copy.deepcopy(self.users)
        new_db.accounts = copy.deepcopy(self.accounts)
        new_db.balances = copy.deepcopy(self.balances)
        new_db.orders = copy.deepcopy(self.orders)
        new_db.trades = copy.deepcopy(self.trades)
        new_db.transactions = copy.deepcopy(self.transactions)
        new_db.audit_logs = copy.deepcopy(self.audit_logs)
        new_db._balance_index = copy.deepcopy(self._balance_index)
        new_db._counters = copy.deepcopy(self._counters)
        return new_db

    def restore(self, snapshot: "InMemoryDatabase") -> None:
        self.users = snapshot.users
        self.accounts = snapshot.accounts
        self.balances = snapshot.balances
        self.orders = snapshot.orders
        self.trades = snapshot.trades
        self.transactions = snapshot.transactions
        self.audit_logs = snapshot.audit_logs
        self._balance_index = snapshot._balance_index
        self._counters = snapshot._counters


class UnitOfWork:
    """Context manager that provides transactional semantics on top of the datastore."""

    def __init__(self, db: InMemoryDatabase) -> None:
        self.db = db
        self._snapshot: Optional[InMemoryDatabase] = None
        self._committed = False

    def __enter__(self) -> "UnitOfWork":
        self._snapshot = self.db.clone()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if exc is not None or not self._committed:
            # rollback to snapshot
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
    return replace(order, **changes)


def copy_balance(balance: Balance, **changes) -> Balance:
    return replace(balance, **changes)


def copy_user(user: User, **changes) -> User:
    return replace(user, **changes)
