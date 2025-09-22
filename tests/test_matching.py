from __future__ import annotations

from decimal import Decimal

from alt_exchange.core.enums import Asset, OrderStatus, Side, TimeInForce
from alt_exchange.infra.bootstrap import build_application_context


def test_fok_cancels_when_insufficient_liquidity():
    context = build_application_context()
    account = context["account_service"]
    wallet = context["wallet_service"]

    seller = account.create_user("seller@example.com", "pwd")
    buyer = account.create_user("buyer@example.com", "pwd")

    wallet.simulate_deposit(seller.id, Asset.ALT, Decimal("1"))
    wallet.simulate_deposit(buyer.id, Asset.USDT, Decimal("50"))

    account.place_limit_order(
        user_id=seller.id,
        side=Side.SELL,
        price=Decimal("10"),
        amount=Decimal("1"),
    )

    fok_order = account.place_limit_order(
        user_id=buyer.id,
        side=Side.BUY,
        price=Decimal("10"),
        amount=Decimal("2"),
        time_in_force=TimeInForce.FOK,
    )

    refreshed_order = context["db"].orders[fok_order.id]
    assert refreshed_order.status is OrderStatus.CANCELED

    buyer_usdt = account.get_balance(buyer.id, Asset.USDT)
    assert buyer_usdt.locked == Decimal("0")


def test_order_book_snapshot_tracks_levels():
    context = build_application_context()
    account = context["account_service"]
    wallet = context["wallet_service"]
    market_data = context["market_data"]

    maker = account.create_user("maker@example.com", "pwd")
    wallet.simulate_deposit(maker.id, Asset.ALT, Decimal("5"))

    account.place_limit_order(
        user_id=maker.id,
        side=Side.SELL,
        price=Decimal("3"),
        amount=Decimal("2"),
    )
    account.place_limit_order(
        user_id=maker.id,
        side=Side.SELL,
        price=Decimal("4"),
        amount=Decimal("1"),
    )

    bids, asks = market_data.order_book_snapshot()
    assert asks[0][0] == Decimal("3")
    assert asks[0][1] == Decimal("2")
    assert asks[1][0] == Decimal("4")
    assert asks[1][1] == Decimal("1")
