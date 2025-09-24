"""
PostgreSQL database implementation using SQLAlchemy
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    create_engine,
    func,
)
from sqlalchemy.orm import Session, declarative_base, sessionmaker
from sqlalchemy.orm.exc import NoResultFound

from alt_exchange.core.enums import (
    AccountStatus,
    Asset,
    OrderStatus,
    OrderType,
    Side,
    TimeInForce,
    TransactionStatus,
    TransactionType,
)
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

logger = logging.getLogger(__name__)

Base = declarative_base()


# SQLAlchemy Models
class UserModel(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True))


class AccountModel(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    status = Column(Enum(AccountStatus), default=AccountStatus.ACTIVE)
    kyc_level = Column(Integer, default=0)


class BalanceModel(Base):
    __tablename__ = "balances"

    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)
    asset = Column(Enum(Asset), nullable=False)
    available = Column(Numeric(36, 18), default=0)
    locked = Column(Numeric(36, 18), default=0)
    updated_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = ({"extend_existing": True},)


class OrderModel(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)
    market = Column(String(20), nullable=False, index=True)
    side = Column(Enum(Side), nullable=False)
    type = Column(Enum(OrderType), nullable=False)
    time_in_force = Column(Enum(TimeInForce), nullable=False)
    price = Column(Numeric(36, 18))
    amount = Column(Numeric(36, 18), nullable=False)
    filled = Column(Numeric(36, 18), default=0)
    status = Column(Enum(OrderStatus), default=OrderStatus.OPEN)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())


class TradeModel(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True)
    buy_order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    sell_order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    maker_order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    taker_order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    taker_side = Column(Enum(Side), nullable=False)
    price = Column(Numeric(36, 18), nullable=False)
    amount = Column(Numeric(36, 18), nullable=False)
    fee = Column(Numeric(36, 18), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class TransactionModel(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    tx_hash = Column(String(255), unique=True, index=True)
    chain = Column(String(50), nullable=False)
    asset = Column(Enum(Asset), nullable=False)
    type = Column(Enum(TransactionType), nullable=False)
    status = Column(Enum(TransactionStatus), nullable=False)
    confirmations = Column(Integer, default=0)
    amount = Column(Numeric(36, 18), nullable=False)
    address = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AuditLogModel(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True)
    actor = Column(String(255), nullable=False)
    action = Column(String(100), nullable=False)
    entity = Column(String(100), nullable=False)
    metadata_json = Column(Text)  # JSON string
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class PostgreSQLDatabase(Database):
    """PostgreSQL database implementation using SQLAlchemy"""

    def __init__(self, connection_string: str) -> None:
        self.engine = create_engine(
            connection_string,
            pool_pre_ping=True,
            pool_recycle=300,
            echo=False,  # Set to True for SQL debugging
        )
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )

        # Create tables if they don't exist
        Base.metadata.create_all(bind=self.engine)

    @contextmanager
    def get_session(self):
        """Get a database session with automatic cleanup"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def next_id(self, table: str) -> int:
        """Generate next ID using database sequence"""
        with self.get_session() as session:
            # Use database sequence for ID generation
            result = session.execute(f"SELECT nextval('{table}_id_seq')")
            return result.scalar()

    # User operations
    def insert_user(self, user: User) -> User:
        with self.get_session() as session:
            db_user = UserModel(
                id=user.id,
                email=user.email,
                password_hash=user.password_hash,
                created_at=user.created_at,
                last_login=user.last_login,
            )
            session.add(db_user)
            session.flush()
            return self._user_from_model(db_user)

    def get_user(self, user_id: int) -> Optional[User]:
        with self.get_session() as session:
            try:
                db_user = session.query(UserModel).filter(UserModel.id == user_id).one()
                return self._user_from_model(db_user)
            except NoResultFound:
                return None

    def get_user_by_email(self, email: str) -> Optional[User]:
        with self.get_session() as session:
            try:
                db_user = (
                    session.query(UserModel).filter(UserModel.email == email).one()
                )
                return self._user_from_model(db_user)
            except NoResultFound:
                return None

    # Account operations
    def insert_account(self, account: Account) -> Account:
        with self.get_session() as session:
            db_account = AccountModel(
                id=account.id,
                user_id=account.user_id,
                status=account.status,
                kyc_level=account.kyc_level,
            )
            session.add(db_account)
            session.flush()
            return self._account_from_model(db_account)

    def get_account(self, account_id: int) -> Optional[Account]:
        with self.get_session() as session:
            try:
                db_account = (
                    session.query(AccountModel)
                    .filter(AccountModel.id == account_id)
                    .one()
                )
                return self._account_from_model(db_account)
            except NoResultFound:
                return None

    def get_accounts_by_user(self, user_id: int) -> List[Account]:
        with self.get_session() as session:
            db_accounts = (
                session.query(AccountModel)
                .filter(AccountModel.user_id == user_id)
                .all()
            )
            return [self._account_from_model(acc) for acc in db_accounts]

    # Balance operations
    def upsert_balance(self, balance: Balance) -> Balance:
        with self.get_session() as session:
            # Check if balance exists
            existing = (
                session.query(BalanceModel)
                .filter(
                    BalanceModel.account_id == balance.account_id,
                    BalanceModel.asset == balance.asset,
                )
                .first()
            )

            if existing:
                existing.available = balance.available
                existing.locked = balance.locked
                existing.updated_at = balance.updated_at
                session.flush()
                return self._balance_from_model(existing)
            else:
                db_balance = BalanceModel(
                    id=balance.id,
                    account_id=balance.account_id,
                    asset=balance.asset,
                    available=balance.available,
                    locked=balance.locked,
                    updated_at=balance.updated_at,
                )
                session.add(db_balance)
                session.flush()
                return self._balance_from_model(db_balance)

    def find_balance(self, account_id: int, asset: Asset) -> Optional[Balance]:
        with self.get_session() as session:
            try:
                db_balance = (
                    session.query(BalanceModel)
                    .filter(
                        BalanceModel.account_id == account_id,
                        BalanceModel.asset == asset,
                    )
                    .one()
                )
                return self._balance_from_model(db_balance)
            except NoResultFound:
                return None

    def get_balances_by_account(self, account_id: int) -> List[Balance]:
        with self.get_session() as session:
            db_balances = (
                session.query(BalanceModel)
                .filter(BalanceModel.account_id == account_id)
                .all()
            )
            return [self._balance_from_model(bal) for bal in db_balances]

    # Order operations
    def insert_order(self, order: Order) -> Order:
        with self.get_session() as session:
            db_order = OrderModel(
                id=order.id,
                user_id=order.user_id,
                account_id=order.account_id,
                market=order.market,
                side=order.side,
                type=order.type,
                time_in_force=order.time_in_force,
                price=order.price,
                amount=order.amount,
                filled=order.filled,
                status=order.status,
                created_at=order.created_at,
                updated_at=order.updated_at,
            )
            session.add(db_order)
            session.flush()
            return self._order_from_model(db_order)

    def update_order(self, order: Order) -> None:
        with self.get_session() as session:
            db_order = session.query(OrderModel).filter(OrderModel.id == order.id).one()
            db_order.user_id = order.user_id
            db_order.account_id = order.account_id
            db_order.market = order.market
            db_order.side = order.side
            db_order.type = order.type
            db_order.time_in_force = order.time_in_force
            db_order.price = order.price
            db_order.amount = order.amount
            db_order.filled = order.filled
            db_order.status = order.status
            db_order.updated_at = order.updated_at
            session.flush()

    def get_order(self, order_id: int) -> Optional[Order]:
        with self.get_session() as session:
            try:
                db_order = (
                    session.query(OrderModel).filter(OrderModel.id == order_id).one()
                )
                return self._order_from_model(db_order)
            except NoResultFound:
                return None

    def get_orders_by_user(self, user_id: int) -> List[Order]:
        with self.get_session() as session:
            db_orders = (
                session.query(OrderModel).filter(OrderModel.user_id == user_id).all()
            )
            return [self._order_from_model(order) for order in db_orders]

    def get_orders_by_account(self, account_id: int) -> List[Order]:
        with self.get_session() as session:
            db_orders = (
                session.query(OrderModel)
                .filter(OrderModel.account_id == account_id)
                .all()
            )
            return [self._order_from_model(order) for order in db_orders]

    # Trade operations
    def insert_trade(self, trade: Trade) -> Trade:
        with self.get_session() as session:
            db_trade = TradeModel(
                id=trade.id,
                buy_order_id=trade.buy_order_id,
                sell_order_id=trade.sell_order_id,
                maker_order_id=trade.maker_order_id,
                taker_order_id=trade.taker_order_id,
                taker_side=trade.taker_side,
                price=trade.price,
                amount=trade.amount,
                fee=trade.fee,
                created_at=trade.created_at,
            )
            session.add(db_trade)
            session.flush()
            return self._trade_from_model(db_trade)

    def get_trade(self, trade_id: int) -> Optional[Trade]:
        with self.get_session() as session:
            try:
                db_trade = (
                    session.query(TradeModel).filter(TradeModel.id == trade_id).one()
                )
                return self._trade_from_model(db_trade)
            except NoResultFound:
                return None

    def get_trades_by_user(self, user_id: int) -> List[Trade]:
        with self.get_session() as session:
            # Get trades where user is either buyer or seller
            db_trades = (
                session.query(TradeModel)
                .join(OrderModel, TradeModel.buy_order_id == OrderModel.id)
                .filter(OrderModel.user_id == user_id)
                .all()
            )

            db_trades.extend(
                session.query(TradeModel)
                .join(OrderModel, TradeModel.sell_order_id == OrderModel.id)
                .filter(OrderModel.user_id == user_id)
                .all()
            )

            return [self._trade_from_model(trade) for trade in db_trades]

    # Transaction operations
    def insert_transaction(self, transaction: Transaction) -> Transaction:
        with self.get_session() as session:
            db_transaction = TransactionModel(
                id=transaction.id,
                user_id=transaction.user_id,
                tx_hash=transaction.tx_hash,
                chain=transaction.chain,
                asset=transaction.asset,
                type=transaction.type,
                status=transaction.status,
                confirmations=transaction.confirmations,
                amount=transaction.amount,
                address=transaction.address,
                created_at=transaction.created_at,
            )
            session.add(db_transaction)
            session.flush()
            return self._transaction_from_model(db_transaction)

    def update_transaction(self, transaction: Transaction) -> None:
        with self.get_session() as session:
            db_transaction = (
                session.query(TransactionModel)
                .filter(TransactionModel.id == transaction.id)
                .one()
            )
            db_transaction.user_id = transaction.user_id
            db_transaction.tx_hash = transaction.tx_hash
            db_transaction.chain = transaction.chain
            db_transaction.asset = transaction.asset
            db_transaction.type = transaction.type
            db_transaction.status = transaction.status
            db_transaction.confirmations = transaction.confirmations
            db_transaction.amount = transaction.amount
            db_transaction.address = transaction.address
            session.flush()

    def get_transaction(self, transaction_id: int) -> Optional[Transaction]:
        with self.get_session() as session:
            try:
                db_transaction = (
                    session.query(TransactionModel)
                    .filter(TransactionModel.id == transaction_id)
                    .one()
                )
                return self._transaction_from_model(db_transaction)
            except NoResultFound:
                return None

    def get_transactions_by_user(self, user_id: int) -> List[Transaction]:
        with self.get_session() as session:
            db_transactions = (
                session.query(TransactionModel)
                .filter(TransactionModel.user_id == user_id)
                .all()
            )
            return [self._transaction_from_model(tx) for tx in db_transactions]

    # Audit log operations
    def insert_audit(self, audit_log: AuditLog) -> AuditLog:
        with self.get_session() as session:
            import json

            db_audit = AuditLogModel(
                id=audit_log.id,
                actor=audit_log.actor,
                action=audit_log.action,
                entity=audit_log.entity,
                metadata_json=json.dumps(audit_log.metadata),
                created_at=audit_log.created_at,
            )
            session.add(db_audit)
            session.flush()
            return self._audit_from_model(db_audit)

    def get_audit_logs(self, limit: int = 100) -> List[AuditLog]:
        with self.get_session() as session:
            db_audits = (
                session.query(AuditLogModel)
                .order_by(AuditLogModel.created_at.desc())
                .limit(limit)
                .all()
            )
            return [self._audit_from_model(audit) for audit in db_audits]

    # Model conversion methods
    def _user_from_model(self, model: UserModel) -> User:
        return User(
            id=model.id,
            email=model.email,
            password_hash=model.password_hash,
            created_at=model.created_at,
            last_login=model.last_login,
        )

    def _account_from_model(self, model: AccountModel) -> Account:
        return Account(
            id=model.id,
            user_id=model.user_id,
            status=model.status,
            kyc_level=model.kyc_level,
        )

    def _balance_from_model(self, model: BalanceModel) -> Balance:
        return Balance(
            id=model.id,
            account_id=model.account_id,
            asset=model.asset,
            available=model.available,
            locked=model.locked,
            updated_at=model.updated_at,
        )

    def _order_from_model(self, model: OrderModel) -> Order:
        return Order(
            id=model.id,
            user_id=model.user_id,
            account_id=model.account_id,
            market=model.market,
            side=model.side,
            type=model.type,
            time_in_force=model.time_in_force,
            price=model.price,
            amount=model.amount,
            filled=model.filled,
            status=model.status,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _trade_from_model(self, model: TradeModel) -> Trade:
        return Trade(
            id=model.id,
            buy_order_id=model.buy_order_id,
            sell_order_id=model.sell_order_id,
            maker_order_id=model.maker_order_id,
            taker_order_id=model.taker_order_id,
            taker_side=model.taker_side,
            price=model.price,
            amount=model.amount,
            fee=model.fee,
            created_at=model.created_at,
        )

    def _transaction_from_model(self, model: TransactionModel) -> Transaction:
        return Transaction(
            id=model.id,
            user_id=model.user_id,
            tx_hash=model.tx_hash,
            chain=model.chain,
            asset=model.asset,
            type=model.type,
            status=model.status,
            confirmations=model.confirmations,
            amount=model.amount,
            address=model.address,
            created_at=model.created_at,
        )

    def _audit_from_model(self, model: AuditLogModel) -> AuditLog:
        import json

        return AuditLog(
            id=model.id,
            actor=model.actor,
            action=model.action,
            entity=model.entity,
            metadata=json.loads(model.metadata_json) if model.metadata_json else {},
            created_at=model.created_at,
        )


class PostgreSQLUnitOfWork(UnitOfWork):
    """PostgreSQL implementation of Unit of Work"""

    def __init__(self, db: PostgreSQLDatabase) -> None:
        self.db = db
        self.session: Optional[Session] = None

    def __enter__(self) -> "PostgreSQLUnitOfWork":
        self.session = self.db.SessionLocal()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.session:
            if exc_val is not None:
                self.session.rollback()
            else:
                self.session.commit()
            self.session.close()
            self.session = None

    def commit(self) -> None:
        if self.session:
            self.session.commit()

    def rollback(self) -> None:
        if self.session:
            self.session.rollback()
