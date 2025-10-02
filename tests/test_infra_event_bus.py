"""
Event bus 테스트
"""

from decimal import Decimal

import pytest

from alt_exchange.core.enums import Side
from alt_exchange.core.events import OrderAccepted, TradeExecuted
from alt_exchange.infra.event_bus import InMemoryEventBus


class TestInMemoryEventBus:
    def test_event_bus_creation(self):
        bus = InMemoryEventBus()
        assert bus is not None

    def test_subscribe_and_publish(self):
        bus = InMemoryEventBus()
        events_received = []

        def handler(event):
            events_received.append(event)

        bus.subscribe(OrderAccepted, handler)

        event = OrderAccepted(
            order_id=1, market="ALT/USDT", side=Side.BUY, remaining=Decimal("10.0")
        )

        bus.publish(event)

        assert len(events_received) == 1
        assert events_received[0] == event

    def test_multiple_subscribers(self):
        bus = InMemoryEventBus()
        events_received_1 = []
        events_received_2 = []

        def handler1(event):
            events_received_1.append(event)

        def handler2(event):
            events_received_2.append(event)

        bus.subscribe(OrderAccepted, handler1)
        bus.subscribe(OrderAccepted, handler2)

        event = OrderAccepted(
            order_id=1, market="ALT/USDT", side=Side.BUY, remaining=Decimal("10.0")
        )

        bus.publish(event)

        assert len(events_received_1) == 1
        assert len(events_received_2) == 1
        assert events_received_1[0] == event
        assert events_received_2[0] == event

    def test_different_event_types(self):
        bus = InMemoryEventBus()
        order_events = []
        trade_events = []

        def order_handler(event):
            order_events.append(event)

        def trade_handler(event):
            trade_events.append(event)

        bus.subscribe(OrderAccepted, order_handler)
        bus.subscribe(TradeExecuted, trade_handler)

        order_event = OrderAccepted(
            order_id=1, market="ALT/USDT", side=Side.BUY, remaining=Decimal("10.0")
        )

        trade_event = TradeExecuted(
            trade_id=1,
            market="ALT/USDT",
            price=Decimal("100.0"),
            amount=Decimal("5.0"),
            maker_order_id=1,
            taker_order_id=2,
            taker_side=Side.BUY,
        )

        bus.publish(order_event)
        bus.publish(trade_event)

        assert len(order_events) == 1
        assert len(trade_events) == 1
        assert order_events[0] == order_event
        assert trade_events[0] == trade_event
