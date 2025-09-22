from __future__ import annotations

from decimal import Decimal

import pytest

from alt_exchange.core.enums import (Asset, OrderStatus, Side, TimeInForce,
                                     TransactionStatus, TransactionType)
from alt_exchange.core.exceptions import (InsufficientBalanceError,
                                          InvalidOrderError)
from alt_exchange.infra.bootstrap import build_application_context
from alt_exchange.services.matching.engine import FEE_RATE


def test_limit_order_requires_sufficient_available_balance():
    context = build_application_context()
    account = context["account_service"]
    wallet = context["wallet_service"]

    user = account.create_user("insufficient@example.com", "pwd")
    wallet.simulate_deposit(user.id, Asset.USDT, Decimal("5"))

    with pytest.raises(InsufficientBalanceError):
        account.place_limit_order(
            user_id=user.id,
            side=Side.BUY,
            price=Decimal("2"),
            amount=Decimal("5"),
        )

    balance = account.get_balance(user.id, Asset.USDT)
    assert balance.available == Decimal("5")
    assert balance.locked == Decimal("0")


def test_partial_fill_retains_locked_balance_for_resting_quantity():
    context = build_application_context()
    account = context["account_service"]
    wallet = context["wallet_service"]

    maker = account.create_user("maker@example.com", "pwd")
    taker = account.create_user("taker@example.com", "pwd")

    wallet.simulate_deposit(maker.id, Asset.ALT, Decimal("10"))
    wallet.simulate_deposit(taker.id, Asset.USDT, Decimal("100"))

    maker_order = account.place_limit_order(
        user_id=maker.id,
        side=Side.SELL,
        price=Decimal("10"),
        amount=Decimal("10"),
        time_in_force=TimeInForce.GTC,
    )

    taker_order = account.place_limit_order(
        user_id=taker.id,
        side=Side.BUY,
        price=Decimal("10"),
        amount=Decimal("4"),
    )

    refreshed_maker = context["db"].orders[maker_order.id]
    refreshed_taker = context["db"].orders[taker_order.id]

    assert refreshed_maker.status is OrderStatus.PARTIAL
    assert refreshed_maker.remaining() == Decimal("6")
    assert refreshed_taker.status is OrderStatus.FILLED

    maker_balance = account.get_balance(maker.id, Asset.ALT)
    assert maker_balance.available == Decimal("0")
    assert maker_balance.locked == Decimal("6")

    taker_balance = account.get_balance(taker.id, Asset.ALT)
    assert taker_balance.available == Decimal("4")
    assert taker_balance.locked == Decimal("0")


def test_deposit_and_withdrawal_transactions_recorded():
    context = build_application_context()
    account = context["account_service"]
    wallet = context["wallet_service"]
    db = context["db"]

    user = account.create_user("wallet@example.com", "pwd")

    deposit_tx = wallet.simulate_deposit(
        user_id=user.id,
        asset=Asset.ALT,
        amount=Decimal("3.5"),
        tx_hash="0xfeed",
    )
    assert deposit_tx.type is TransactionType.DEPOSIT
    assert deposit_tx.status is TransactionStatus.CONFIRMED

    stored_deposit = db.transactions[deposit_tx.id]
    assert stored_deposit.tx_hash == "0xfeed"
    assert stored_deposit.amount == Decimal("3.5")

    withdrawal = wallet.request_withdrawal(
        user_id=user.id,
        asset=Asset.ALT,
        amount=Decimal("1.0"),
        address=wallet.allocate_deposit_address(user.id),
    )
    assert withdrawal.type is TransactionType.WITHDRAW
    assert withdrawal.status is TransactionStatus.PENDING

    balance_pending = account.get_balance(user.id, Asset.ALT)
    assert balance_pending.available == Decimal("2.5")
    assert balance_pending.locked == Decimal("1.0")

    completed = wallet.complete_withdrawal(withdrawal.id, tx_hash="0xabc")
    assert completed.status is TransactionStatus.CONFIRMED
    assert completed.tx_hash == "0xabc"

    balance_final = account.get_balance(user.id, Asset.ALT)
    assert balance_final.locked == Decimal("0")


def test_order_validation_rejects_non_positive_amounts_and_prices():
    context = build_application_context()
    account = context["account_service"]
    wallet = context["wallet_service"]

    user = account.create_user("validator@example.com", "pwd")
    wallet.simulate_deposit(user.id, Asset.USDT, Decimal("10"))

    with pytest.raises(InvalidOrderError):
        account.place_limit_order(
            user_id=user.id,
            side=Side.BUY,
            price=Decimal("0"),
            amount=Decimal("1"),
        )

    with pytest.raises(InvalidOrderError):
        account.place_limit_order(
            user_id=user.id,
            side=Side.BUY,
            price=Decimal("1"),
            amount=Decimal("0"),
        )


def test_cross_matches_consume_multiple_price_levels_and_emit_events():
    context = build_application_context()
    account = context["account_service"]
    wallet = context["wallet_service"]
    market = context["market_data"]

    seller_one = account.create_user("s1@example.com", "pwd")
    seller_two = account.create_user("s2@example.com", "pwd")
    buyer = account.create_user("buyer@example.com", "pwd")

    wallet.simulate_deposit(seller_one.id, Asset.ALT, Decimal("1"))
    wallet.simulate_deposit(seller_two.id, Asset.ALT, Decimal("2"))
    wallet.simulate_deposit(buyer.id, Asset.USDT, Decimal("100"))

    order_one = account.place_limit_order(
        user_id=seller_one.id,
        side=Side.SELL,
        price=Decimal("10"),
        amount=Decimal("1"),
    )
    order_two = account.place_limit_order(
        user_id=seller_two.id,
        side=Side.SELL,
        price=Decimal("11"),
        amount=Decimal("2"),
    )

    taker_order = account.place_limit_order(
        user_id=buyer.id,
        side=Side.BUY,
        price=Decimal("12"),
        amount=Decimal("2.5"),
    )

    refreshed_one = context["db"].orders[order_one.id]
    refreshed_two = context["db"].orders[order_two.id]
    refreshed_taker = context["db"].orders[taker_order.id]

    assert refreshed_one.status is OrderStatus.FILLED
    assert refreshed_two.status is OrderStatus.PARTIAL
    assert refreshed_two.remaining() == Decimal("0.5")
    assert refreshed_taker.status is OrderStatus.FILLED

    seller_two_balance = account.get_balance(seller_two.id, Asset.ALT)
    assert seller_two_balance.locked == Decimal("0.5")

    trades = market.latest_trades()
    assert len(trades) == 2
    assert {trade.price for trade in trades} == {Decimal("10"), Decimal("11")}

    filled_value = Decimal("10") * Decimal("1") + Decimal("11") * Decimal("1.5")
    expected_funds = filled_value * (Decimal("1") - FEE_RATE)
    buyer_spent = filled_value * (Decimal("1") + FEE_RATE)

    buyer_quote = account.get_balance(buyer.id, Asset.USDT)
    assert buyer_quote.locked == Decimal("0")
    assert buyer_quote.available == Decimal("100") - buyer_spent

    seller_one_quote = account.get_balance(seller_one.id, Asset.USDT)
    assert seller_one_quote.available == Decimal("10") * (Decimal("1") - FEE_RATE)

    seller_two_quote = account.get_balance(seller_two.id, Asset.USDT)
    assert seller_two_quote.available == expected_funds - seller_one_quote.available


def test_allocate_deposit_address_is_deterministic_per_user():
    context = build_application_context()
    wallet = context["wallet_service"]

    address_one = wallet.allocate_deposit_address(1)
    assert address_one == wallet.allocate_deposit_address(1)

    address_two = wallet.allocate_deposit_address(2)
    assert address_two != address_one
