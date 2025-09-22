"""
FastAPI-based REST API for ALT Exchange
Implements OpenAPI 3.0 specification from the design document
"""

from __future__ import annotations

from decimal import Decimal
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from alt_exchange.core.enums import (Asset, OrderStatus, OrderType, Side,
                                     TimeInForce)
from alt_exchange.core.models import Balance, Order, Trade, Transaction
from alt_exchange.infra.bootstrap import build_application_context

# Initialize FastAPI app
app = FastAPI(
    title="ALT Exchange API",
    version="0.1.0",
    description="Cryptocurrency exchange API for ALT/USDT trading",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global application context (in production, use dependency injection)
_context = None


def get_context():
    global _context
    if _context is None:
        _context = build_application_context()
    return _context


# Pydantic models for API
class OrderRequest(BaseModel):
    market: str = Field(..., example="ALT/USDT")
    side: Side
    type: OrderType
    time_in_force: TimeInForce = TimeInForce.GTC
    price: Optional[str] = Field(None, description="Required for limit orders")
    amount: str = Field(..., description="Order amount as string")


class OrderResponse(BaseModel):
    id: int
    market: str
    side: Side
    type: OrderType
    time_in_force: TimeInForce
    price: Optional[str]
    amount: str
    filled: str
    status: OrderStatus
    created_at: str


class BalanceResponse(BaseModel):
    asset: Asset
    available: str
    locked: str


class TradeResponse(BaseModel):
    id: int
    price: str
    amount: str
    side: Side
    created_at: str


class WithdrawalRequest(BaseModel):
    asset: Asset
    amount: str
    address: str


class WithdrawalResponse(BaseModel):
    id: int
    status: str
    tx_hash: Optional[str] = None


# Authentication dependency (stub for now)
async def get_current_user_id() -> int:
    """Get current user ID from JWT token (stub implementation)"""
    # In production, decode JWT and extract user_id
    return 1


# API Endpoints


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "alt-exchange-api"}


@app.post("/orders", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_request: OrderRequest, user_id: int = Depends(get_current_user_id)
):
    """Create a new order"""
    context = get_context()
    account_service = context["account_service"]

    try:
        # Convert string amounts to Decimal
        price = Decimal(order_request.price) if order_request.price else None
        amount = Decimal(order_request.amount)

        # Place order
        order = account_service.place_limit_order(
            user_id=user_id,
            side=order_request.side,
            price=price,
            amount=amount,
            time_in_force=order_request.time_in_force,
        )

        return OrderResponse(
            id=order.id,
            market=order.market,
            side=order.side,
            type=order.type,
            time_in_force=order.time_in_force,
            price=str(order.price) if order.price else None,
            amount=str(order.amount),
            filled=str(order.filled),
            status=order.status,
            created_at=order.created_at.isoformat(),
        )

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.get("/orders", response_model=List[OrderResponse])
async def get_orders(
    status: Optional[OrderStatus] = None, user_id: int = Depends(get_current_user_id)
):
    """Get user's orders"""
    context = get_context()
    account_service = context["account_service"]

    orders = account_service.get_user_orders(user_id, status)

    return [
        OrderResponse(
            id=order.id,
            market=order.market,
            side=order.side,
            type=order.type,
            time_in_force=order.time_in_force,
            price=str(order.price) if order.price else None,
            amount=str(order.amount),
            filled=str(order.filled),
            status=order.status,
            created_at=order.created_at.isoformat(),
        )
        for order in orders
    ]


@app.get("/balances", response_model=List[BalanceResponse])
async def get_balances(user_id: int = Depends(get_current_user_id)):
    """Get user's balances"""
    context = get_context()
    account_service = context["account_service"]

    balances = []
    for asset in Asset:
        balance = account_service.get_balance(user_id, asset)
        if balance:
            balances.append(
                BalanceResponse(
                    asset=asset,
                    available=str(balance.available),
                    locked=str(balance.locked),
                )
            )

    return balances


@app.get("/trades", response_model=List[TradeResponse])
async def get_trades(limit: int = 100, user_id: int = Depends(get_current_user_id)):
    """Get user's trade history"""
    context = get_context()
    account_service = context["account_service"]

    trades = account_service.get_user_trades(user_id, limit)

    return [
        TradeResponse(
            id=trade.id,
            price=str(trade.price),
            amount=str(trade.amount),
            side=trade.taker_side,
            created_at=trade.created_at.isoformat(),
        )
        for trade in trades
    ]


@app.post(
    "/withdrawals",
    response_model=WithdrawalResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def request_withdrawal(
    withdrawal_request: WithdrawalRequest, user_id: int = Depends(get_current_user_id)
):
    """Request a withdrawal"""
    context = get_context()
    wallet_service = context["wallet_service"]

    try:
        amount = Decimal(withdrawal_request.amount)

        withdrawal = wallet_service.request_withdrawal(
            user_id=user_id,
            asset=withdrawal_request.asset,
            amount=amount,
            address=withdrawal_request.address,
        )

        return WithdrawalResponse(
            id=withdrawal.id, status=withdrawal.status.value, tx_hash=withdrawal.tx_hash
        )

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.get("/orderbook/{market}")
async def get_orderbook(market: str):
    """Get order book snapshot"""
    context = get_context()
    market_data = context["market_data"]

    bids, asks = market_data.order_book_snapshot()

    return {
        "market": market,
        "bids": [[str(price), str(size)] for price, size in bids],
        "asks": [[str(price), str(size)] for price, size in asks],
        "timestamp": "2024-01-01T00:00:00Z",  # In production, use actual timestamp
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
