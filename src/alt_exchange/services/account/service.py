from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from decimal import Decimal
from typing import Iterable, Optional

from alt_exchange.core.enums import (Asset, OrderStatus, OrderType, Side,
                                     TimeInForce, TransactionStatus,
                                     TransactionType)
from alt_exchange.core.events import BalanceChanged, OrderStatusChanged
from alt_exchange.core.exceptions import (EntityNotFoundError,
                                          InsufficientBalanceError,
                                          InvalidOrderError, SettlementError)
from alt_exchange.core.models import (Account, Balance, Order, Trade,
                                      Transaction, User)
from alt_exchange.infra.datastore import (InMemoryDatabase, UnitOfWork,
                                          copy_balance)
from alt_exchange.infra.event_bus import InMemoryEventBus
from alt_exchange.services.matching.engine import FEE_RATE, MatchingEngine


class AccountService:
    def __init__(
        self,
        db: InMemoryDatabase,
        event_bus: InMemoryEventBus,
        matching_engine: MatchingEngine,
    ) -> None:
        self.db = db
        self.event_bus = event_bus
        self.matching = matching_engine
        self.market = matching_engine.market

    # ------------------------------------------------------------------
    # User & account lifecycle
    def create_user(self, email: str, password: str) -> User:
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        with UnitOfWork(self.db) as uow:
            user = User(
                id=self.db.next_id("users"), email=email, password_hash=password_hash
            )
            self.db.insert_user(user)

            account = Account(id=self.db.next_id("accounts"), user_id=user.id)
            self.db.insert_account(account)

            for asset in Asset:
                balance = Balance(
                    id=self.db.next_id("balances"),
                    account_id=account.id,
                    asset=asset,
                    available=Decimal("0"),
                    locked=Decimal("0"),
                )
                self.db.upsert_balance(balance)
            uow.commit()
        return user

    # ------------------------------------------------------------------
    def get_account(self, user_id: int) -> Account:
        for account in self.db.accounts.values():
            if account.user_id == user_id:
                return account
        raise EntityNotFoundError(f"Account for user {user_id} not found")

    def get_balance(self, user_id: int, asset: Asset) -> Balance:
        account = self.get_account(user_id)
        balance = self.db.find_balance(account.id, asset)
        if balance is None:
            raise EntityNotFoundError(
                f"Balance for account {account.id} {asset.value} not found"
            )
        return balance

    # ------------------------------------------------------------------
    def credit_deposit(
        self, user_id: int, asset: Asset, amount: Decimal, tx_hash: Optional[str] = None
    ) -> Transaction:
        account = self.get_account(user_id)
        now = datetime.now(timezone.utc)
        with UnitOfWork(self.db) as uow:
            balance = self._ensure_balance(account.id, asset)
            balance.available += amount
            balance.updated_at = now
            self.db.upsert_balance(balance)
            self.event_bus.publish(
                BalanceChanged(
                    account_id=account.id,
                    asset=asset,
                    available=balance.available,
                    locked=balance.locked,
                    reason="deposit",
                )
            )

            tx = Transaction(
                id=self.db.next_id("transactions"),
                user_id=user_id,
                tx_hash=tx_hash,
                chain="BSC",
                asset=asset,
                type=TransactionType.DEPOSIT,
                status=TransactionStatus.CONFIRMED,
                confirmations=12,
                amount=amount,
                address=None,
            )
            self.db.insert_transaction(tx)
            uow.commit()
        return tx

    # ------------------------------------------------------------------
    def request_withdrawal(
        self, user_id: int, asset: Asset, amount: Decimal, address: str
    ) -> Transaction:
        account = self.get_account(user_id)
        now = datetime.now(timezone.utc)
        with UnitOfWork(self.db) as uow:
            balance = self._ensure_balance(account.id, asset)
            if balance.available < amount:
                raise InsufficientBalanceError("Insufficient funds for withdrawal")

            balance.available -= amount
            balance.locked += amount
            balance.updated_at = now
            self.db.upsert_balance(balance)

            tx = Transaction(
                id=self.db.next_id("transactions"),
                user_id=user_id,
                tx_hash=None,
                chain="BSC",
                asset=asset,
                type=TransactionType.WITHDRAW,
                status=TransactionStatus.PENDING,
                confirmations=0,
                amount=amount,
                address=address,
            )
            self.db.insert_transaction(tx)
            uow.commit()

        self.event_bus.publish(
            BalanceChanged(
                account_id=account.id,
                asset=asset,
                available=balance.available,
                locked=balance.locked,
                reason="withdrawal_lock",
            )
        )
        return tx

    def complete_withdrawal(
        self, tx_id: int, tx_hash: str, confirmations: int = 12
    ) -> Transaction:
        tx = self.db.transactions.get(tx_id)
        if tx is None:
            raise EntityNotFoundError(f"Transaction {tx_id} not found")
        if tx.type is not TransactionType.WITHDRAW:
            raise InvalidOrderError("Transaction is not a withdrawal")

        account = self.get_account(tx.user_id)
        with UnitOfWork(self.db) as uow:
            balance = self._ensure_balance(account.id, tx.asset)
            if balance.locked < tx.amount:
                raise SettlementError("Locked balance lower than withdrawal amount")
            balance.locked -= tx.amount
            balance.updated_at = datetime.now(timezone.utc)
            self.db.upsert_balance(balance)

            tx.status = TransactionStatus.CONFIRMED
            tx.tx_hash = tx_hash
            tx.confirmations = confirmations
            self.db.transactions[tx.id] = tx
            uow.commit()

        self.event_bus.publish(
            BalanceChanged(
                account_id=account.id,
                asset=tx.asset,
                available=balance.available,
                locked=balance.locked,
                reason="withdrawal_release",
            )
        )
        return tx

    # ------------------------------------------------------------------
    def place_limit_order(
        self,
        user_id: int,
        side: Side,
        price: Decimal,
        amount: Decimal,
        time_in_force: TimeInForce = TimeInForce.GTC,
    ) -> Order:
        account = self.get_account(user_id)
        if amount <= 0:
            raise InvalidOrderError("Amount must be positive")
        if price <= 0:
            raise InvalidOrderError("Price must be positive")

        lock_asset = Asset.USDT if side is Side.BUY else Asset.ALT
        lock_required = self._lock_required(side, price, amount)
        now = datetime.now(timezone.utc)

        with UnitOfWork(self.db) as uow:
            balance = self._ensure_balance(account.id, lock_asset)
            if balance.available < lock_required:
                raise InsufficientBalanceError(
                    "Insufficient available balance for order"
                )

            updated_balance = copy_balance(balance)
            updated_balance.available -= lock_required
            updated_balance.locked += lock_required
            updated_balance.updated_at = now
            self.db.upsert_balance(updated_balance)

            order = Order(
                id=self.db.next_id("orders"),
                user_id=user_id,
                account_id=account.id,
                market=self.market,
                side=side,
                type=OrderType.LIMIT,
                time_in_force=time_in_force,
                price=price,
                amount=amount,
                filled=Decimal("0"),
                status=OrderStatus.OPEN,
            )
            self.db.insert_order(order)
            uow.commit()

        self.event_bus.publish(
            BalanceChanged(
                account_id=account.id,
                asset=lock_asset,
                available=self.db.find_balance(account.id, lock_asset).available,
                locked=self.db.find_balance(account.id, lock_asset).locked,
                reason="order_lock",
            )
        )

        trades = self.matching.submit(order)
        if trades:
            self._settle_trades(trades)

        self._rebalance_after_order(order)
        return order

    def get_user_orders(
        self, user_id: int, status: Optional[OrderStatus] = None
    ) -> List[Order]:
        """Get orders for a specific user"""
        orders = []
        for order in self.db.orders.values():
            if order.user_id == user_id:
                if status is None or order.status == status:
                    orders.append(order)
        return sorted(orders, key=lambda x: x.created_at, reverse=True)

    def get_user_trades(self, user_id: int, limit: int = 100) -> List[Trade]:
        """Get trades for a specific user"""
        trades = []
        for trade in self.db.trades.values():
            # Check if user is involved in this trade
            buy_order = self.db.orders.get(trade.buy_order_id)
            sell_order = self.db.orders.get(trade.sell_order_id)

            if (buy_order and buy_order.user_id == user_id) or (
                sell_order and sell_order.user_id == user_id
            ):
                trades.append(trade)

        return sorted(trades, key=lambda x: x.created_at, reverse=True)[:limit]

    def cancel_order(self, user_id: int, order_id: int) -> bool:
        """Cancel an order"""
        order = self.db.orders.get(order_id)
        if not order or order.user_id != user_id:
            return False

        if order.status not in {OrderStatus.OPEN, OrderStatus.PARTIAL}:
            return False

        # Update order status
        order.status = OrderStatus.CANCELED
        order.updated_at = datetime.now(timezone.utc)
        self.db.update_order(order)

        # Release locked funds
        self._release_locked_funds(order)

        # Publish event
        self.event_bus.publish(
            OrderStatusChanged(
                order_id=order.id,
                status=order.status,
                filled=order.filled,
                remaining=order.remaining(),
                reason="user_canceled",
            )
        )

        return True

    def _release_locked_funds(self, order: Order):
        """Release funds locked by an order"""
        if order.side is Side.BUY:
            asset = Asset.USDT
            amount = order.remaining() * order.price * (Decimal("1") + FEE_RATE)
        else:
            asset = Asset.ALT
            amount = order.remaining()

        balance = self._ensure_balance(order.account_id, asset)
        balance.locked -= amount
        balance.available += amount
        balance.updated_at = datetime.now(timezone.utc)
        self.db.upsert_balance(balance)

    # ------------------------------------------------------------------
    def _settle_trades(self, trades: Iterable[Trade]) -> None:
        now = datetime.now(timezone.utc)
        with UnitOfWork(self.db) as uow:
            for trade in trades:
                buy_order = self.db.orders[trade.buy_order_id]
                sell_order = self.db.orders[trade.sell_order_id]

                buy_account = self.db.accounts[buy_order.account_id]
                sell_account = self.db.accounts[sell_order.account_id]

                notional = trade.price * trade.amount
                quote_fee = notional * FEE_RATE

                # Buyer settlement
                buy_quote = self._ensure_balance(buy_account.id, Asset.USDT)
                buy_quote.locked -= self._lock_required(
                    Side.BUY, trade.price, trade.amount
                )
                if buy_quote.locked < Decimal("0"):
                    raise SettlementError("Negative locked balance for buyer")
                buy_quote.updated_at = now
                self.db.upsert_balance(buy_quote)

                buy_base = self._ensure_balance(buy_account.id, Asset.ALT)
                buy_base.available += trade.amount
                buy_base.updated_at = now
                self.db.upsert_balance(buy_base)

                # Seller settlement
                sell_base = self._ensure_balance(sell_account.id, Asset.ALT)
                sell_base.locked -= trade.amount
                if sell_base.locked < Decimal("0"):
                    raise SettlementError("Negative locked balance for seller")
                sell_base.updated_at = now
                self.db.upsert_balance(sell_base)

                sell_quote = self._ensure_balance(sell_account.id, Asset.USDT)
                sell_quote.available += notional * (Decimal("1") - FEE_RATE)
                sell_quote.updated_at = now
                self.db.upsert_balance(sell_quote)

                # Emit balance events
                self.event_bus.publish(
                    BalanceChanged(
                        account_id=buy_account.id,
                        asset=Asset.USDT,
                        available=buy_quote.available,
                        locked=buy_quote.locked,
                        reason="trade_settlement",
                    )
                )
                self.event_bus.publish(
                    BalanceChanged(
                        account_id=buy_account.id,
                        asset=Asset.ALT,
                        available=buy_base.available,
                        locked=buy_base.locked,
                        reason="trade_settlement",
                    )
                )
                self.event_bus.publish(
                    BalanceChanged(
                        account_id=sell_account.id,
                        asset=Asset.ALT,
                        available=sell_base.available,
                        locked=sell_base.locked,
                        reason="trade_settlement",
                    )
                )
                self.event_bus.publish(
                    BalanceChanged(
                        account_id=sell_account.id,
                        asset=Asset.USDT,
                        available=sell_quote.available,
                        locked=sell_quote.locked,
                        reason="trade_settlement",
                    )
                )

                self.event_bus.publish(
                    OrderStatusChanged(
                        order_id=buy_order.id,
                        status=buy_order.status,
                        filled=buy_order.filled,
                        remaining=buy_order.remaining(),
                    )
                )
                self.event_bus.publish(
                    OrderStatusChanged(
                        order_id=sell_order.id,
                        status=sell_order.status,
                        filled=sell_order.filled,
                        remaining=sell_order.remaining(),
                    )
                )

            uow.commit()

        # After settlement, ensure locked balances reflect unmatched quantity
        touched_orders = {trade.buy_order_id for trade in trades} | {
            trade.sell_order_id for trade in trades
        }
        for order_id in touched_orders:
            self._rebalance_after_order(self.db.orders[order_id])

    # ------------------------------------------------------------------
    def _rebalance_after_order(self, order: Order) -> None:
        account = self.db.accounts[order.account_id]
        expected_locked = self._expected_locked(order)
        asset = Asset.USDT if order.side is Side.BUY else Asset.ALT
        balance = self._ensure_balance(account.id, asset)
        delta = balance.locked - expected_locked
        if delta < Decimal("0"):
            raise SettlementError("Locked balance below expected level")
        if delta > 0:
            balance.locked -= delta
            balance.available += delta
            balance.updated_at = datetime.now(timezone.utc)
            self.db.upsert_balance(balance)
            self.event_bus.publish(
                BalanceChanged(
                    account_id=account.id,
                    asset=asset,
                    available=balance.available,
                    locked=balance.locked,
                    reason="lock_release",
                )
            )

    # ------------------------------------------------------------------
    def _ensure_balance(self, account_id: int, asset: Asset) -> Balance:
        balance = self.db.find_balance(account_id, asset)
        if balance is None:
            balance = Balance(
                id=self.db.next_id("balances"),
                account_id=account_id,
                asset=asset,
                available=Decimal("0"),
                locked=Decimal("0"),
            )
            self.db.upsert_balance(balance)
        return balance

    def _lock_required(self, side: Side, price: Decimal, amount: Decimal) -> Decimal:
        if side is Side.BUY:
            return price * amount * (Decimal("1") + FEE_RATE)
        return amount

    def _expected_locked(self, order: Order) -> Decimal:
        remaining = order.remaining()
        if order.status in {OrderStatus.CANCELED, OrderStatus.FILLED}:
            remaining = Decimal("0")
        elif (
            order.status is OrderStatus.PARTIAL
            and order.time_in_force is not TimeInForce.GTC
        ):
            remaining = Decimal("0")
        if order.side is Side.BUY:
            price = order.price or Decimal("0")
            return price * remaining * (Decimal("1") + FEE_RATE)
        return remaining
