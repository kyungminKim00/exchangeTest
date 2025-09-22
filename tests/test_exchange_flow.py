from __future__ import annotations

from decimal import Decimal

import pytest

from alt_exchange.core.enums import Asset, OrderStatus, Side, TimeInForce
from alt_exchange.infra.bootstrap import build_application_context
from alt_exchange.services.matching.engine import FEE_RATE


@pytest.fixture
def context():
    return build_application_context()


def test_full_flow_with_withdrawal(context):
    account = context["account_service"]
    wallet = context["wallet_service"]

    buyer = account.create_user("buyer@example.com", "pwd")
    seller = account.create_user("seller@example.com", "pwd")

    wallet.simulate_deposit(buyer.id, Asset.USDT, Decimal("100"))
    wallet.simulate_deposit(seller.id, Asset.ALT, Decimal("50"))

    # Buyer places resting order first
    buy_order = account.place_limit_order(
        user_id=buyer.id,
        side=Side.BUY,
        price=Decimal("2"),
        amount=Decimal("10"),
    )

    # Seller order triggers matching
    sell_order = account.place_limit_order(
        user_id=seller.id,
        side=Side.SELL,
        price=Decimal("2"),
        amount=Decimal("10"),
    )

    buy_order = context["db"].orders[buy_order.id]
    sell_order = context["db"].orders[sell_order.id]

    assert buy_order.status is OrderStatus.FILLED
    assert sell_order.status is OrderStatus.FILLED

    buyer_alt = account.get_balance(buyer.id, Asset.ALT)
    assert buyer_alt.available == Decimal("10")
    assert buyer_alt.locked == Decimal("0")

    seller_usdt = account.get_balance(seller.id, Asset.USDT)
    expected_net = Decimal("2") * Decimal("10") * (Decimal("1") - FEE_RATE)
    assert seller_usdt.available == expected_net

    # Withdrawal flow
    withdrawal = wallet.request_withdrawal(
        user_id=seller.id,
        asset=Asset.USDT,
        amount=Decimal("5"),
        address=wallet.allocate_deposit_address(seller.id),
    )
    seller_usdt_after_request = account.get_balance(seller.id, Asset.USDT)
    assert seller_usdt_after_request.available == expected_net - Decimal("5")
    assert seller_usdt_after_request.locked >= Decimal("5")

    wallet.complete_withdrawal(withdrawal.id, tx_hash="0xabc")
    seller_usdt_final = account.get_balance(seller.id, Asset.USDT)
    assert seller_usdt_final.locked == Decimal("0")


def test_ioc_order_releases_remainder(context):
    account = context["account_service"]
    wallet = context["wallet_service"]

    seller = account.create_user("maker@example.com", "pwd")
    buyer = account.create_user("taker@example.com", "pwd")

    wallet.simulate_deposit(seller.id, Asset.ALT, Decimal("2"))
    wallet.simulate_deposit(buyer.id, Asset.USDT, Decimal("40"))

    # Resting sell order for 1 ALT @ 10
    maker_order = account.place_limit_order(
        user_id=seller.id,
        side=Side.SELL,
        price=Decimal("10"),
        amount=Decimal("1"),
        time_in_force=TimeInForce.GTC,
    )

    # IOC buy for 2 ALT should partially fill 1 and cancel remainder
    ioc_order = account.place_limit_order(
        user_id=buyer.id,
        side=Side.BUY,
        price=Decimal("10"),
        amount=Decimal("2"),
        time_in_force=TimeInForce.IOC,
    )

    taker_order = context["db"].orders[ioc_order.id]
    resting_order = context["db"].orders[maker_order.id]
    assert taker_order.status is OrderStatus.PARTIAL
    assert resting_order.status is OrderStatus.FILLED

    buyer_usdt = account.get_balance(buyer.id, Asset.USDT)
    spent = Decimal("10") * Decimal("1") * (Decimal("1") + FEE_RATE)
    assert buyer_usdt.locked == Decimal("0")
    expected_available = Decimal("40") - spent
    assert (buyer_usdt.available - expected_available).copy_abs() < Decimal("1e-12")

    buyer_alt = account.get_balance(buyer.id, Asset.ALT)
    assert buyer_alt.available == Decimal("1")


def test_price_time_priority(context):
    account = context["account_service"]
    wallet = context["wallet_service"]

    seller1 = account.create_user("s1@example.com", "pwd")
    seller2 = account.create_user("s2@example.com", "pwd")
    buyer = account.create_user("buyer@example.com", "pwd")

    wallet.simulate_deposit(seller1.id, Asset.ALT, Decimal("2"))
    wallet.simulate_deposit(seller2.id, Asset.ALT, Decimal("2"))
    wallet.simulate_deposit(buyer.id, Asset.USDT, Decimal("60"))

    order1 = account.place_limit_order(
        user_id=seller1.id,
        side=Side.SELL,
        price=Decimal("10"),
        amount=Decimal("2"),
    )
    order2 = account.place_limit_order(
        user_id=seller2.id,
        side=Side.SELL,
        price=Decimal("10"),
        amount=Decimal("2"),
    )

    account.place_limit_order(
        user_id=buyer.id,
        side=Side.BUY,
        price=Decimal("10"),
        amount=Decimal("3"),
    )

    updated_order1 = context["db"].orders[order1.id]
    updated_order2 = context["db"].orders[order2.id]

    assert updated_order1.status is OrderStatus.FILLED
    assert updated_order2.status is OrderStatus.PARTIAL

    seller2_alt = account.get_balance(seller2.id, Asset.ALT)
    assert seller2_alt.locked == Decimal("1")  # remaining resting quantity
