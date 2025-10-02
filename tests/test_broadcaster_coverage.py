from collections import deque
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from alt_exchange.core.enums import Asset, OrderStatus, OrderType, Side
from alt_exchange.core.events import (OrderAccepted, OrderStatusChanged,
                                      TradeExecuted)
from alt_exchange.infra.event_bus import InMemoryEventBus
from alt_exchange.services.market_data.broadcaster import MarketDataBroadcaster
from alt_exchange.services.matching.engine import MatchingEngine


class TestMarketDataBroadcasterCoverage:
    """Coverage tests for MarketDataBroadcaster"""

    @pytest.fixture
    def mock_matching_engine(self):
        """Mock matching engine"""
        matching = MagicMock()
        matching.order_book_snapshot.return_value = (
            [(Decimal("100"), Decimal("10"))],  # bids
            [(Decimal("101"), Decimal("5"))],  # asks
        )
        return matching

    @pytest.fixture
    def mock_event_bus(self):
        """Mock event bus"""
        return MagicMock()

    @pytest.fixture
    def broadcaster(self, mock_matching_engine, mock_event_bus):
        """MarketDataBroadcaster instance"""
        return MarketDataBroadcaster(
            matching=mock_matching_engine,
            event_bus=mock_event_bus,
            max_items=100,
        )

    @pytest.fixture
    def trade_event(self):
        """Mock trade event"""
        return TradeExecuted(
            trade_id=1,
            market="ALT/USDT",
            price=Decimal("100.0"),
            amount=Decimal("10.0"),
            maker_order_id=1,
            taker_order_id=2,
            taker_side=Side.BUY,
        )

    @pytest.fixture
    def order_status_event(self):
        """Mock order status event"""
        return OrderStatusChanged(
            order_id=1,
            status=OrderStatus.FILLED,
            filled=Decimal("10.0"),
            remaining=Decimal("0.0"),
            reason="Order filled",
        )

    @pytest.fixture
    def order_accept_event(self):
        """Mock order accept event"""
        return OrderAccepted(
            order_id=1,
            market="ALT/USDT",
            side=Side.BUY,
            remaining=Decimal("10.0"),
        )

    def test_broadcaster_initialization(
        self, broadcaster, mock_matching_engine, mock_event_bus
    ):
        """Test MarketDataBroadcaster initialization"""
        assert broadcaster is not None
        assert broadcaster.matching == mock_matching_engine
        assert isinstance(broadcaster.trades, deque)
        assert isinstance(broadcaster.order_updates, deque)
        assert isinstance(broadcaster.order_accepts, deque)
        assert broadcaster.trades.maxlen == 100
        assert broadcaster.order_updates.maxlen == 100
        assert broadcaster.order_accepts.maxlen == 100

    def test_broadcaster_initialization_custom_max_items(
        self, mock_matching_engine, mock_event_bus
    ):
        """Test MarketDataBroadcaster initialization with custom max_items"""
        broadcaster = MarketDataBroadcaster(
            matching=mock_matching_engine,
            event_bus=mock_event_bus,
            max_items=50,
        )
        assert broadcaster.trades.maxlen == 50
        assert broadcaster.order_updates.maxlen == 50
        assert broadcaster.order_accepts.maxlen == 50

    def test_broadcaster_event_subscriptions(
        self, mock_matching_engine, mock_event_bus
    ):
        """Test that broadcaster subscribes to events"""
        broadcaster = MarketDataBroadcaster(
            matching=mock_matching_engine,
            event_bus=mock_event_bus,
        )

        # Verify event subscriptions
        mock_event_bus.subscribe.assert_any_call(TradeExecuted, broadcaster._on_trade)
        mock_event_bus.subscribe.assert_any_call(
            OrderStatusChanged, broadcaster._on_order_state
        )
        mock_event_bus.subscribe.assert_any_call(
            OrderAccepted, broadcaster._on_order_accept
        )
        assert mock_event_bus.subscribe.call_count == 3

    def test_on_trade(self, broadcaster, trade_event):
        """Test _on_trade method"""
        initial_count = len(broadcaster.trades)
        broadcaster._on_trade(trade_event)
        assert len(broadcaster.trades) == initial_count + 1
        assert broadcaster.trades[-1] == trade_event

    def test_on_trade_multiple(self, broadcaster, trade_event):
        """Test _on_trade method with multiple trades"""
        # Add multiple trades
        for i in range(5):
            event = TradeExecuted(
                trade_id=i + 1,
                market="ALT/USDT",
                price=Decimal("100.0"),
                amount=Decimal("10.0"),
                maker_order_id=i + 1,
                taker_order_id=i + 2,
                taker_side=Side.BUY,
            )
            broadcaster._on_trade(event)

        assert len(broadcaster.trades) == 5
        assert broadcaster.trades[0].trade_id == 1
        assert broadcaster.trades[4].trade_id == 5

    def test_on_trade_max_items(self, mock_matching_engine, mock_event_bus):
        """Test _on_trade method with max_items limit"""
        broadcaster = MarketDataBroadcaster(
            matching=mock_matching_engine,
            event_bus=mock_event_bus,
            max_items=3,
        )

        # Add more trades than max_items
        for i in range(5):
            event = TradeExecuted(
                trade_id=i + 1,
                market="ALT/USDT",
                price=Decimal("100.0"),
                amount=Decimal("10.0"),
                maker_order_id=i + 1,
                taker_order_id=i + 2,
                taker_side=Side.BUY,
            )
            broadcaster._on_trade(event)

        assert len(broadcaster.trades) == 3
        assert broadcaster.trades[0].trade_id == 3  # First item should be the 3rd trade
        assert broadcaster.trades[2].trade_id == 5  # Last item should be the 5th trade

    def test_on_order_state(self, broadcaster, order_status_event):
        """Test _on_order_state method"""
        initial_count = len(broadcaster.order_updates)
        broadcaster._on_order_state(order_status_event)
        assert len(broadcaster.order_updates) == initial_count + 1
        assert broadcaster.order_updates[-1] == order_status_event

    def test_on_order_state_multiple(self, broadcaster, order_status_event):
        """Test _on_order_state method with multiple updates"""
        # Add multiple order updates
        for i in range(5):
            event = OrderStatusChanged(
                order_id=i + 1,
                status=OrderStatus.FILLED,
                filled=Decimal("10.0"),
                remaining=Decimal("0.0"),
                reason="Order filled",
            )
            broadcaster._on_order_state(event)

        assert len(broadcaster.order_updates) == 5
        assert broadcaster.order_updates[0].order_id == 1
        assert broadcaster.order_updates[4].order_id == 5

    def test_on_order_state_max_items(self, mock_matching_engine, mock_event_bus):
        """Test _on_order_state method with max_items limit"""
        broadcaster = MarketDataBroadcaster(
            matching=mock_matching_engine,
            event_bus=mock_event_bus,
            max_items=3,
        )

        # Add more order updates than max_items
        for i in range(5):
            event = OrderStatusChanged(
                order_id=i + 1,
                status=OrderStatus.FILLED,
                filled=Decimal("10.0"),
                remaining=Decimal("0.0"),
                reason="Order filled",
            )
            broadcaster._on_order_state(event)

        assert len(broadcaster.order_updates) == 3
        assert (
            broadcaster.order_updates[0].order_id == 3
        )  # First item should be the 3rd update
        assert (
            broadcaster.order_updates[2].order_id == 5
        )  # Last item should be the 5th update

    def test_on_order_accept(self, broadcaster, order_accept_event):
        """Test _on_order_accept method"""
        initial_count = len(broadcaster.order_accepts)
        broadcaster._on_order_accept(order_accept_event)
        assert len(broadcaster.order_accepts) == initial_count + 1
        assert broadcaster.order_accepts[-1] == order_accept_event

    def test_on_order_accept_multiple(self, broadcaster, order_accept_event):
        """Test _on_order_accept method with multiple accepts"""
        # Add multiple order accepts
        for i in range(5):
            event = OrderAccepted(
                order_id=i + 1,
                market="ALT/USDT",
                side=Side.BUY,
                remaining=Decimal("10.0"),
            )
            broadcaster._on_order_accept(event)

        assert len(broadcaster.order_accepts) == 5
        assert broadcaster.order_accepts[0].order_id == 1
        assert broadcaster.order_accepts[4].order_id == 5

    def test_on_order_accept_max_items(self, mock_matching_engine, mock_event_bus):
        """Test _on_order_accept method with max_items limit"""
        broadcaster = MarketDataBroadcaster(
            matching=mock_matching_engine,
            event_bus=mock_event_bus,
            max_items=3,
        )

        # Add more order accepts than max_items
        for i in range(5):
            event = OrderAccepted(
                order_id=i + 1,
                market="ALT/USDT",
                side=Side.BUY,
                remaining=Decimal("10.0"),
            )
            broadcaster._on_order_accept(event)

        assert len(broadcaster.order_accepts) == 3
        assert (
            broadcaster.order_accepts[0].order_id == 3
        )  # First item should be the 3rd accept
        assert (
            broadcaster.order_accepts[2].order_id == 5
        )  # Last item should be the 5th accept

    def test_latest_trades_empty(self, broadcaster):
        """Test latest_trades method with empty trades"""
        trades = broadcaster.latest_trades()
        assert isinstance(trades, list)
        assert len(trades) == 0

    def test_latest_trades_with_data(self, broadcaster, trade_event):
        """Test latest_trades method with data"""
        broadcaster._on_trade(trade_event)
        trades = broadcaster.latest_trades()
        assert isinstance(trades, list)
        assert len(trades) == 1
        assert trades[0] == trade_event

    def test_latest_trades_multiple(self, broadcaster):
        """Test latest_trades method with multiple trades"""
        # Add multiple trades
        for i in range(5):
            event = TradeExecuted(
                trade_id=i + 1,
                market="ALT/USDT",
                price=Decimal("100.0"),
                amount=Decimal("10.0"),
                maker_order_id=i + 1,
                taker_order_id=i + 2,
                taker_side=Side.BUY,
            )
            broadcaster._on_trade(event)

        trades = broadcaster.latest_trades()
        assert isinstance(trades, list)
        assert len(trades) == 5
        assert trades[0].trade_id == 1
        assert trades[4].trade_id == 5

    def test_latest_order_updates_empty(self, broadcaster):
        """Test latest_order_updates method with empty updates"""
        updates = broadcaster.latest_order_updates()
        assert isinstance(updates, list)
        assert len(updates) == 0

    def test_latest_order_updates_with_data(self, broadcaster, order_status_event):
        """Test latest_order_updates method with data"""
        broadcaster._on_order_state(order_status_event)
        updates = broadcaster.latest_order_updates()
        assert isinstance(updates, list)
        assert len(updates) == 1
        assert updates[0] == order_status_event

    def test_latest_order_updates_multiple(self, broadcaster):
        """Test latest_order_updates method with multiple updates"""
        # Add multiple order updates
        for i in range(5):
            event = OrderStatusChanged(
                order_id=i + 1,
                status=OrderStatus.FILLED,
                filled=Decimal("10.0"),
                remaining=Decimal("0.0"),
                reason="Order filled",
            )
            broadcaster._on_order_state(event)

        updates = broadcaster.latest_order_updates()
        assert isinstance(updates, list)
        assert len(updates) == 5
        assert updates[0].order_id == 1
        assert updates[4].order_id == 5

    def test_order_book_snapshot(self, broadcaster, mock_matching_engine):
        """Test order_book_snapshot method"""
        bids, asks = broadcaster.order_book_snapshot()
        assert isinstance(bids, list)
        assert isinstance(asks, list)
        assert len(bids) == 1
        assert len(asks) == 1
        assert bids[0] == (Decimal("100"), Decimal("10"))
        assert asks[0] == (Decimal("101"), Decimal("5"))
        mock_matching_engine.order_book_snapshot.assert_called_once()

    def test_order_book_snapshot_empty(self, mock_matching_engine, mock_event_bus):
        """Test order_book_snapshot method with empty order book"""
        mock_matching_engine.order_book_snapshot.return_value = ([], [])
        broadcaster = MarketDataBroadcaster(
            matching=mock_matching_engine,
            event_bus=mock_event_bus,
        )

        bids, asks = broadcaster.order_book_snapshot()
        assert isinstance(bids, list)
        assert isinstance(asks, list)
        assert len(bids) == 0
        assert len(asks) == 0

    def test_order_book_snapshot_multiple_levels(
        self, mock_matching_engine, mock_event_bus
    ):
        """Test order_book_snapshot method with multiple levels"""
        mock_matching_engine.order_book_snapshot.return_value = (
            [(Decimal("100"), Decimal("10")), (Decimal("99"), Decimal("5"))],  # bids
            [(Decimal("101"), Decimal("5")), (Decimal("102"), Decimal("10"))],  # asks
        )
        broadcaster = MarketDataBroadcaster(
            matching=mock_matching_engine,
            event_bus=mock_event_bus,
        )

        bids, asks = broadcaster.order_book_snapshot()
        assert isinstance(bids, list)
        assert isinstance(asks, list)
        assert len(bids) == 2
        assert len(asks) == 2
        assert bids[0] == (Decimal("100"), Decimal("10"))
        assert bids[1] == (Decimal("99"), Decimal("5"))
        assert asks[0] == (Decimal("101"), Decimal("5"))
        assert asks[1] == (Decimal("102"), Decimal("10"))

    def test_broadcaster_attributes(self, broadcaster):
        """Test broadcaster attributes"""
        assert hasattr(broadcaster, "matching")
        assert hasattr(broadcaster, "trades")
        assert hasattr(broadcaster, "order_updates")
        assert hasattr(broadcaster, "order_accepts")
        assert hasattr(broadcaster, "_on_trade")
        assert hasattr(broadcaster, "_on_order_state")
        assert hasattr(broadcaster, "_on_order_accept")
        assert hasattr(broadcaster, "latest_trades")
        assert hasattr(broadcaster, "latest_order_updates")
        assert hasattr(broadcaster, "order_book_snapshot")

    def test_broadcaster_methods_callable(self, broadcaster):
        """Test that broadcaster methods are callable"""
        assert callable(broadcaster._on_trade)
        assert callable(broadcaster._on_order_state)
        assert callable(broadcaster._on_order_accept)
        assert callable(broadcaster.latest_trades)
        assert callable(broadcaster.latest_order_updates)
        assert callable(broadcaster.order_book_snapshot)

    def test_broadcaster_deque_properties(self, broadcaster):
        """Test broadcaster deque properties"""
        assert broadcaster.trades.maxlen == 100
        assert broadcaster.order_updates.maxlen == 100
        assert broadcaster.order_accepts.maxlen == 100
        assert len(broadcaster.trades) == 0
        assert len(broadcaster.order_updates) == 0
        assert len(broadcaster.order_accepts) == 0

    def test_broadcaster_integration(
        self, broadcaster, trade_event, order_status_event, order_accept_event
    ):
        """Test broadcaster integration with all event types"""
        # Add one of each event type
        broadcaster._on_trade(trade_event)
        broadcaster._on_order_state(order_status_event)
        broadcaster._on_order_accept(order_accept_event)

        # Verify all events are stored
        assert len(broadcaster.trades) == 1
        assert len(broadcaster.order_updates) == 1
        assert len(broadcaster.order_accepts) == 1

        # Verify latest methods return correct data
        trades = broadcaster.latest_trades()
        updates = broadcaster.latest_order_updates()
        accepts = broadcaster.order_accepts  # Direct access to deque

        assert trades[0] == trade_event
        assert updates[0] == order_status_event
        assert accepts[0] == order_accept_event
