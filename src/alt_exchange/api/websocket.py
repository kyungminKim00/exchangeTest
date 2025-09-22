"""
WebSocket server for real-time market data broadcasting
Implements order book updates, trade feeds, and user notifications
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, List, Set

import websockets
from websockets.server import WebSocketServerProtocol

from alt_exchange.core.enums import Asset, OrderStatus, Side
from alt_exchange.core.events import OrderStatusChanged, TradeExecuted
from alt_exchange.core.models import Trade
from alt_exchange.infra.bootstrap import build_application_context
from alt_exchange.infra.event_bus import InMemoryEventBus


class WebSocketManager:
    """Manages WebSocket connections and subscriptions"""

    def __init__(self):
        self.connections: Set[WebSocketServerProtocol] = set()
        self.user_connections: Dict[int, Set[WebSocketServerProtocol]] = {}
        self.market_subscriptions: Dict[str, Set[WebSocketServerProtocol]] = {}
        self.context = build_application_context()
        self.event_bus = self.context["event_bus"]

    async def register(self, websocket: WebSocketServerProtocol):
        """Register a new WebSocket connection"""
        self.connections.add(websocket)
        print(f"WebSocket connected. Total connections: {len(self.connections)}")

    async def unregister(self, websocket: WebSocketServerProtocol):
        """Unregister a WebSocket connection"""
        self.connections.discard(websocket)

        # Remove from user connections - use list() to avoid RuntimeError
        user_ids_to_remove = []
        for user_id, connections in self.user_connections.items():
            connections.discard(websocket)
            if not connections:
                user_ids_to_remove.append(user_id)

        for user_id in user_ids_to_remove:
            del self.user_connections[user_id]

        # Remove from market subscriptions - use list() to avoid RuntimeError
        markets_to_remove = []
        for market, connections in self.market_subscriptions.items():
            connections.discard(websocket)
            if not connections:
                markets_to_remove.append(market)

        for market in markets_to_remove:
            del self.market_subscriptions[market]

        print(f"WebSocket disconnected. Total connections: {len(self.connections)}")

    async def subscribe_to_market(
        self, websocket: WebSocketServerProtocol, market: str
    ):
        """Subscribe to market data updates"""
        if market not in self.market_subscriptions:
            self.market_subscriptions[market] = set()
        self.market_subscriptions[market].add(websocket)

        # Send initial order book snapshot
        await self.send_orderbook_snapshot(websocket, market)

    async def subscribe_to_user(self, websocket: WebSocketServerProtocol, user_id: int):
        """Subscribe to user-specific updates"""
        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()
        self.user_connections[user_id].add(websocket)

    async def send_orderbook_snapshot(
        self, websocket: WebSocketServerProtocol, market: str
    ):
        """Send order book snapshot to a specific connection"""
        try:
            market_data = self.context["market_data"]
            bids, asks = market_data.order_book_snapshot()

            message = {
                "type": "orderbook_snapshot",
                "market": market,
                "bids": [[str(price), str(size)] for price, size in bids],
                "asks": [[str(price), str(size)] for price, size in asks],
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            await websocket.send(json.dumps(message))
        except Exception as e:
            print(f"Error sending orderbook snapshot: {e}")

    async def broadcast_orderbook_update(self, market: str):
        """Broadcast order book update to all subscribers"""
        if market not in self.market_subscriptions:
            return

        try:
            market_data = self.context["market_data"]
            bids, asks = market_data.order_book_snapshot()

            message = {
                "type": "orderbook_update",
                "market": market,
                "bids": [[str(price), str(size)] for price, size in bids],
                "asks": [[str(price), str(size)] for price, size in asks],
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            # Send to all subscribers
            disconnected = set()
            for websocket in self.market_subscriptions[market]:
                try:
                    await websocket.send(json.dumps(message))
                except websockets.exceptions.ConnectionClosed:
                    disconnected.add(websocket)

            # Clean up disconnected connections
            for websocket in disconnected:
                await self.unregister(websocket)

        except Exception as e:
            print(f"Error broadcasting orderbook update: {e}")

    async def broadcast_trade(self, trade: Trade):
        """Broadcast trade to market subscribers"""
        market = "ALT/USDT"  # In production, derive from trade data

        if market not in self.market_subscriptions:
            return

        message = {
            "type": "trade",
            "market": market,
            "price": str(trade.price),
            "amount": str(trade.amount),
            "side": trade.taker_side.value,
            "timestamp": trade.created_at.isoformat(),
        }

        # Send to all market subscribers
        disconnected = set()
        for websocket in self.market_subscriptions[market]:
            try:
                await websocket.send(json.dumps(message))
            except websockets.exceptions.ConnectionClosed:
                disconnected.add(websocket)
            except Exception as e:
                print(f"Error broadcasting trade to websocket: {e}")
                disconnected.add(websocket)

        # Clean up disconnected connections
        for websocket in disconnected:
            await self.unregister(websocket)

    async def send_order_update(self, user_id: int, order_update: dict):
        """Send order update to specific user"""
        if user_id not in self.user_connections:
            return

        message = {
            "type": "order_update",
            "data": order_update,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Send to all user connections
        disconnected = set()
        for websocket in self.user_connections[user_id]:
            try:
                await websocket.send(json.dumps(message))
            except websockets.exceptions.ConnectionClosed:
                disconnected.add(websocket)

        # Clean up disconnected connections
        for websocket in disconnected:
            await self.unregister(websocket)


# Global WebSocket manager instance
ws_manager = WebSocketManager()


async def websocket_handler(websocket: WebSocketServerProtocol, path: str):
    """Handle WebSocket connections"""
    await ws_manager.register(websocket)

    try:
        # Send welcome message
        welcome = {
            "type": "welcome",
            "message": "Connected to ALT Exchange WebSocket",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        await websocket.send(json.dumps(welcome))

        async for message in websocket:
            try:
                data = json.loads(message)
                await handle_websocket_message(websocket, data)
            except json.JSONDecodeError:
                error = {
                    "type": "error",
                    "message": "Invalid JSON format",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                await websocket.send(json.dumps(error))
            except Exception as e:
                error = {
                    "type": "error",
                    "message": str(e),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                await websocket.send(json.dumps(error))

    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        await ws_manager.unregister(websocket)


async def handle_websocket_message(websocket: WebSocketServerProtocol, data: dict):
    """Handle incoming WebSocket messages"""
    message_type = data.get("type")

    if message_type == "subscribe_market":
        market = data.get("market", "ALT/USDT")
        await ws_manager.subscribe_to_market(websocket, market)

        response = {
            "type": "subscription_confirmed",
            "market": market,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        await websocket.send(json.dumps(response))

    elif message_type == "subscribe_user":
        user_id = data.get("user_id")
        if user_id:
            await ws_manager.subscribe_to_user(websocket, user_id)

            response = {
                "type": "user_subscription_confirmed",
                "user_id": user_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            await websocket.send(json.dumps(response))

    elif message_type == "ping":
        response = {"type": "pong", "timestamp": datetime.now(timezone.utc).isoformat()}
        await websocket.send(json.dumps(response))

    else:
        error = {
            "type": "error",
            "message": f"Unknown message type: {message_type}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        await websocket.send(json.dumps(error))


async def start_websocket_server(host: str = "localhost", port: int = 8765):
    """Start the WebSocket server"""
    print(f"Starting WebSocket server on {host}:{port}")

    async with websockets.serve(websocket_handler, host, port):
        print(f"WebSocket server running on ws://{host}:{port}")
        await asyncio.Future()  # Run forever


if __name__ == "__main__":
    asyncio.run(start_websocket_server())
