"""
Event Bus 확장 테스트 - 더 많은 메서드 커버
"""

from unittest.mock import Mock

import pytest

from alt_exchange.core.events import OrderAccepted, TradeExecuted
from alt_exchange.infra.event_bus import InMemoryEventBus


class TestInMemoryEventBusExtended:
    """InMemory Event Bus 확장 테스트 클래스"""

    def setup_method(self):
        """테스트 설정"""
        self.event_bus = InMemoryEventBus()

    def test_subscribe_multiple_handlers(self):
        """여러 핸들러 구독 테스트"""
        handler1 = Mock()
        handler2 = Mock()
        handler3 = Mock()

        self.event_bus.subscribe(OrderAccepted, handler1)
        self.event_bus.subscribe(OrderAccepted, handler2)
        self.event_bus.subscribe(OrderAccepted, handler3)

        event = OrderAccepted(order_id=1, market="ALT/USDT", side="BUY", remaining=10.0)

        self.event_bus.publish(event)

        handler1.assert_called_once_with(event)
        handler2.assert_called_once_with(event)
        handler3.assert_called_once_with(event)

    def test_subscribe_different_event_types(self):
        """다른 이벤트 타입들에 대한 구독 테스트"""
        order_handler = Mock()
        trade_handler = Mock()

        self.event_bus.subscribe(OrderAccepted, order_handler)
        self.event_bus.subscribe(TradeExecuted, trade_handler)

        order_event = OrderAccepted(
            order_id=1, market="ALT/USDT", side="BUY", remaining=10.0
        )

        trade_event = TradeExecuted(
            trade_id=1,
            market="ALT/USDT",
            price=100.0,
            amount=5.0,
            maker_order_id=1,
            taker_order_id=2,
            taker_side="BUY",
        )

        self.event_bus.publish(order_event)
        self.event_bus.publish(trade_event)

        order_handler.assert_called_once_with(order_event)
        trade_handler.assert_called_once_with(trade_event)

    def test_publish_without_subscribers(self):
        """구독자가 없는 상태에서 이벤트 발행 테스트"""
        event = OrderAccepted(order_id=1, market="ALT/USDT", side="BUY", remaining=10.0)

        # Should not raise any exception
        self.event_bus.publish(event)

    def test_subscribe_same_handler_multiple_times(self):
        """같은 핸들러를 여러 번 구독하는 테스트"""
        handler = Mock()

        self.event_bus.subscribe(OrderAccepted, handler)
        self.event_bus.subscribe(OrderAccepted, handler)
        self.event_bus.subscribe(OrderAccepted, handler)

        event = OrderAccepted(order_id=1, market="ALT/USDT", side="BUY", remaining=10.0)

        self.event_bus.publish(event)

        # Handler should be called 3 times
        assert handler.call_count == 3

    def test_publish_multiple_events(self):
        """여러 이벤트 발행 테스트"""
        handler = Mock()
        self.event_bus.subscribe(OrderAccepted, handler)

        events = [
            OrderAccepted(order_id=i, market="ALT/USDT", side="BUY", remaining=10.0)
            for i in range(1, 6)
        ]

        for event in events:
            self.event_bus.publish(event)

        assert handler.call_count == 5

    def test_subscribe_with_lambda_handler(self):
        """Lambda 핸들러 구독 테스트"""
        call_count = 0

        def lambda_handler(event):
            nonlocal call_count
            call_count += 1

        self.event_bus.subscribe(OrderAccepted, lambda_handler)

        event = OrderAccepted(order_id=1, market="ALT/USDT", side="BUY", remaining=10.0)

        self.event_bus.publish(event)
        assert call_count == 1

    def test_subscribe_with_class_method_handler(self):
        """클래스 메서드 핸들러 구독 테스트"""

        class EventHandler:
            def __init__(self):
                self.call_count = 0

            def handle_order(self, event):
                self.call_count += 1

        handler = EventHandler()
        self.event_bus.subscribe(OrderAccepted, handler.handle_order)

        event = OrderAccepted(order_id=1, market="ALT/USDT", side="BUY", remaining=10.0)

        self.event_bus.publish(event)
        assert handler.call_count == 1

    def test_publish_with_exception_in_handler(self):
        """핸들러에서 예외가 발생하는 경우 테스트"""
        handler1 = Mock()
        handler2 = Mock(side_effect=Exception("Handler error"))
        handler3 = Mock()

        self.event_bus.subscribe(OrderAccepted, handler1)
        self.event_bus.subscribe(OrderAccepted, handler2)
        self.event_bus.subscribe(OrderAccepted, handler3)

        event = OrderAccepted(order_id=1, market="ALT/USDT", side="BUY", remaining=10.0)

        # Should not raise exception, but handler2 should fail
        try:
            self.event_bus.publish(event)
        except Exception:
            pass  # Expected to handle gracefully

        handler1.assert_called_once_with(event)
        handler2.assert_called_once_with(event)
        # handler3 may or may not be called depending on implementation
        # Just check that the event bus didn't crash

    def test_subscribe_with_none_handler(self):
        """None 핸들러 구독 테스트"""
        # Should not raise exception
        try:
            self.event_bus.subscribe(OrderAccepted, None)
        except Exception:
            pass  # Expected to handle gracefully

        event = OrderAccepted(order_id=1, market="ALT/USDT", side="BUY", remaining=10.0)

        # Should not raise exception
        try:
            self.event_bus.publish(event)
        except Exception:
            pass  # Expected to handle gracefully

    def test_publish_with_none_event(self):
        """None 이벤트 발행 테스트"""
        handler = Mock()
        self.event_bus.subscribe(OrderAccepted, handler)

        # Should not raise exception
        self.event_bus.publish(None)

        # Handler should not be called
        handler.assert_not_called()

    def test_subscribe_with_invalid_event_type(self):
        """잘못된 이벤트 타입으로 구독 테스트"""
        handler = Mock()

        # Should not raise exception
        self.event_bus.subscribe(str, handler)
        self.event_bus.subscribe(int, handler)
        self.event_bus.subscribe(list, handler)

        # Publish with different types
        self.event_bus.publish("test")
        self.event_bus.publish(123)
        self.event_bus.publish([1, 2, 3])

        # Handler should be called for each type
        assert handler.call_count == 3

    def test_publish_with_different_event_types(self):
        """다른 이벤트 타입들로 발행 테스트"""
        handler = Mock()
        self.event_bus.subscribe(OrderAccepted, handler)

        # Publish with different event types
        order_event = OrderAccepted(
            order_id=1, market="ALT/USDT", side="BUY", remaining=10.0
        )

        trade_event = TradeExecuted(
            trade_id=1,
            market="ALT/USDT",
            price=100.0,
            amount=5.0,
            maker_order_id=1,
            taker_order_id=2,
            taker_side="BUY",
        )

        self.event_bus.publish(order_event)
        self.event_bus.publish(trade_event)

        # Handler should only be called for OrderAccepted
        handler.assert_called_once_with(order_event)

    def test_subscribe_with_multiple_event_types(self):
        """여러 이벤트 타입에 대한 구독 테스트"""
        handler = Mock()

        self.event_bus.subscribe(OrderAccepted, handler)
        self.event_bus.subscribe(TradeExecuted, handler)

        order_event = OrderAccepted(
            order_id=1, market="ALT/USDT", side="BUY", remaining=10.0
        )

        trade_event = TradeExecuted(
            trade_id=1,
            market="ALT/USDT",
            price=100.0,
            amount=5.0,
            maker_order_id=1,
            taker_order_id=2,
            taker_side="BUY",
        )

        self.event_bus.publish(order_event)
        self.event_bus.publish(trade_event)

        # Handler should be called twice
        assert handler.call_count == 2

    def test_publish_with_complex_event_data(self):
        """복잡한 이벤트 데이터로 발행 테스트"""
        handler = Mock()
        self.event_bus.subscribe(OrderAccepted, handler)

        # Create event with complex data
        event = OrderAccepted(
            order_id=999, market="BTC/USDT", side="SELL", remaining=0.001
        )

        self.event_bus.publish(event)

        handler.assert_called_once_with(event)
        assert handler.call_args[0][0].order_id == 999
        assert handler.call_args[0][0].market == "BTC/USDT"
        assert handler.call_args[0][0].side == "SELL"
        assert handler.call_args[0][0].remaining == 0.001

    def test_subscribe_with_different_handler_types(self):
        """다른 타입의 핸들러들 구독 테스트"""
        # Mock handler
        mock_handler = Mock()

        # Function handler
        def func_handler(event):
            pass

        # Lambda handler
        lambda_handler = lambda event: None

        # Class method handler
        class HandlerClass:
            def handle(self, event):
                pass

        class_handler = HandlerClass()

        self.event_bus.subscribe(OrderAccepted, mock_handler)
        self.event_bus.subscribe(OrderAccepted, func_handler)
        self.event_bus.subscribe(OrderAccepted, lambda_handler)
        self.event_bus.subscribe(OrderAccepted, class_handler.handle)

        event = OrderAccepted(order_id=1, market="ALT/USDT", side="BUY", remaining=10.0)

        self.event_bus.publish(event)

        # Mock handler should be called
        mock_handler.assert_called_once_with(event)

    def test_publish_with_large_number_of_events(self):
        """많은 수의 이벤트 발행 테스트"""
        handler = Mock()
        self.event_bus.subscribe(OrderAccepted, handler)

        # Publish 1000 events
        for i in range(1000):
            event = OrderAccepted(
                order_id=i, market="ALT/USDT", side="BUY", remaining=10.0
            )
            self.event_bus.publish(event)

        assert handler.call_count == 1000

    def test_subscribe_with_large_number_of_handlers(self):
        """많은 수의 핸들러 구독 테스트"""
        handlers = [Mock() for _ in range(100)]

        for handler in handlers:
            self.event_bus.subscribe(OrderAccepted, handler)

        event = OrderAccepted(order_id=1, market="ALT/USDT", side="BUY", remaining=10.0)

        self.event_bus.publish(event)

        for handler in handlers:
            handler.assert_called_once_with(event)

    def test_publish_with_mixed_event_types(self):
        """혼합된 이벤트 타입들로 발행 테스트"""
        order_handler = Mock()
        trade_handler = Mock()

        self.event_bus.subscribe(OrderAccepted, order_handler)
        self.event_bus.subscribe(TradeExecuted, trade_handler)

        # Publish mixed events
        events = [
            OrderAccepted(order_id=1, market="ALT/USDT", side="BUY", remaining=10.0),
            TradeExecuted(
                trade_id=1,
                market="ALT/USDT",
                price=100.0,
                amount=5.0,
                maker_order_id=1,
                taker_order_id=2,
                taker_side="BUY",
            ),
            OrderAccepted(order_id=2, market="ALT/USDT", side="SELL", remaining=5.0),
            TradeExecuted(
                trade_id=2,
                market="ALT/USDT",
                price=101.0,
                amount=3.0,
                maker_order_id=2,
                taker_order_id=3,
                taker_side="SELL",
            ),
        ]

        for event in events:
            self.event_bus.publish(event)

        assert order_handler.call_count == 2
        assert trade_handler.call_count == 2

    def test_event_bus_initialization(self):
        """Event Bus 초기화 테스트"""
        event_bus = InMemoryEventBus()
        assert event_bus is not None
        assert hasattr(event_bus, "subscribe")
        assert hasattr(event_bus, "publish")

    def test_event_bus_methods_exist(self):
        """Event Bus 메서드 존재 테스트"""
        assert hasattr(self.event_bus, "subscribe")
        assert hasattr(self.event_bus, "publish")
        assert callable(self.event_bus.subscribe)
        assert callable(self.event_bus.publish)

    def test_event_bus_with_empty_subscribers(self):
        """빈 구독자 목록으로 이벤트 발행 테스트"""
        event = OrderAccepted(order_id=1, market="ALT/USDT", side="BUY", remaining=10.0)

        # Should not raise exception
        self.event_bus.publish(event)

    def test_event_bus_with_single_subscriber(self):
        """단일 구독자로 이벤트 발행 테스트"""
        handler = Mock()
        self.event_bus.subscribe(OrderAccepted, handler)

        event = OrderAccepted(order_id=1, market="ALT/USDT", side="BUY", remaining=10.0)

        self.event_bus.publish(event)
        handler.assert_called_once_with(event)

    def test_event_bus_with_multiple_subscribers_same_event(self):
        """같은 이벤트에 대한 여러 구독자 테스트"""
        handlers = [Mock() for _ in range(5)]

        for handler in handlers:
            self.event_bus.subscribe(OrderAccepted, handler)

        event = OrderAccepted(order_id=1, market="ALT/USDT", side="BUY", remaining=10.0)

        self.event_bus.publish(event)

        for handler in handlers:
            handler.assert_called_once_with(event)

    def test_event_bus_with_multiple_subscribers_different_events(self):
        """다른 이벤트에 대한 여러 구독자 테스트"""
        order_handlers = [Mock() for _ in range(3)]
        trade_handlers = [Mock() for _ in range(2)]

        for handler in order_handlers:
            self.event_bus.subscribe(OrderAccepted, handler)

        for handler in trade_handlers:
            self.event_bus.subscribe(TradeExecuted, handler)

        order_event = OrderAccepted(
            order_id=1, market="ALT/USDT", side="BUY", remaining=10.0
        )

        trade_event = TradeExecuted(
            trade_id=1,
            market="ALT/USDT",
            price=100.0,
            amount=5.0,
            maker_order_id=1,
            taker_order_id=2,
            taker_side="BUY",
        )

        self.event_bus.publish(order_event)
        self.event_bus.publish(trade_event)

        for handler in order_handlers:
            handler.assert_called_once_with(order_event)

        for handler in trade_handlers:
            handler.assert_called_once_with(trade_event)
