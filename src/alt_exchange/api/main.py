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
    stop_price: Optional[str] = Field(
        None, description="Required for STOP and OCO orders"
    )


class StopOrderRequest(BaseModel):
    market: str = Field(..., example="ALT/USDT")
    side: Side
    price: str = Field(..., description="Limit price when stop is triggered")
    stop_price: str = Field(..., description="Stop price to trigger the order")
    amount: str = Field(..., description="Order amount as string")
    time_in_force: TimeInForce = TimeInForce.GTC


class OCOOrderRequest(BaseModel):
    market: str = Field(..., example="ALT/USDT")
    side: Side
    price: str = Field(..., description="Limit order price")
    stop_price: str = Field(..., description="Stop order price")
    amount: str = Field(..., description="Order amount as string")
    time_in_force: TimeInForce = TimeInForce.GTC


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
    stop_price: Optional[str] = None
    link_order_id: Optional[int] = None
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


class DepositAddressResponse(BaseModel):
    address: str
    asset: Asset


class AdminWithdrawalApprovalRequest(BaseModel):
    tx_id: int


class AdminWithdrawalRejectionRequest(BaseModel):
    tx_id: int
    reason: str


class AdminAccountFreezeRequest(BaseModel):
    account_id: int
    reason: str


class AdminAccountUnfreezeRequest(BaseModel):
    account_id: int


class AuditLogResponse(BaseModel):
    id: int
    actor: str
    action: str
    entity: str
    metadata: dict
    created_at: str


# Authentication dependency (stub for now)
async def get_current_user_id() -> int:
    """Get current user ID from JWT token (stub implementation)"""
    # In production, decode JWT and extract user_id
    return 1


async def get_current_admin_id() -> int:
    """Get current admin user ID from JWT token (stub implementation)"""
    # In production, decode JWT and verify admin role
    return 1  # Admin user ID


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
        stop_price = (
            Decimal(order_request.stop_price) if order_request.stop_price else None
        )

        # Place order based on type
        if order_request.type == OrderType.LIMIT:
            order = account_service.place_limit_order(
                user_id=user_id,
                side=order_request.side,
                price=price,
                amount=amount,
                time_in_force=order_request.time_in_force,
            )
        elif order_request.type == OrderType.STOP:
            if stop_price is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="stop_price is required for STOP orders",
                )
            order = account_service.place_stop_order(
                user_id=user_id,
                side=order_request.side,
                price=price,
                stop_price=stop_price,
                amount=amount,
                time_in_force=order_request.time_in_force,
            )
        elif order_request.type == OrderType.OCO:
            if stop_price is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="stop_price is required for OCO orders",
                )
            main_order, stop_order = account_service.place_oco_order(
                user_id=user_id,
                side=order_request.side,
                price=price,
                stop_price=stop_price,
                amount=amount,
                time_in_force=order_request.time_in_force,
            )
            order = main_order  # Return the main order
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Order type {order_request.type} not supported",
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
            stop_price=str(order.stop_price) if order.stop_price else None,
            link_order_id=order.link_order_id,
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
            stop_price=str(order.stop_price) if order.stop_price else None,
            link_order_id=order.link_order_id,
            created_at=order.created_at.isoformat(),
        )
        for order in orders
    ]


@app.delete("/orders/{order_id}")
async def cancel_order(order_id: int, user_id: int = Depends(get_current_user_id)):
    """Cancel an order"""
    context = get_context()
    account_service = context["account_service"]

    try:
        success = account_service.cancel_order(user_id, order_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found or cannot be cancelled",
            )
        return {"message": "Order cancelled successfully"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


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


@app.get("/deposit-address/{asset}", response_model=DepositAddressResponse)
async def get_deposit_address(
    asset: Asset, user_id: int = Depends(get_current_user_id)
):
    """Get deposit address for a specific asset"""
    context = get_context()
    wallet_service = context["wallet_service"]

    try:
        address = wallet_service.get_deposit_address(user_id, asset)
        return DepositAddressResponse(address=address, asset=asset)
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


# Admin Endpoints


@app.get("/admin/withdrawals/pending")
async def get_pending_withdrawals(admin_id: int = Depends(get_current_admin_id)):
    """Get pending withdrawal requests (admin only)"""
    context = get_context()
    admin_service = context["admin_service"]

    try:
        withdrawals = admin_service.list_pending_withdrawals(admin_id)
        return [
            {
                "id": tx.id,
                "user_id": tx.user_id,
                "asset": tx.asset.value,
                "amount": str(tx.amount),
                "address": tx.address,
                "created_at": tx.created_at.isoformat(),
            }
            for tx in withdrawals
        ]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@app.post("/admin/withdrawals/approve")
async def approve_withdrawal(
    request: AdminWithdrawalApprovalRequest,
    admin_id: int = Depends(get_current_admin_id),
):
    """Approve a withdrawal request (admin only)"""
    context = get_context()
    admin_service = context["admin_service"]

    try:
        tx = admin_service.approve_withdrawal(admin_id, request.tx_id)
        return {
            "id": tx.id,
            "status": tx.status.value,
            "approved_at": tx.approved_at.isoformat() if tx.approved_at else None,
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.post("/admin/withdrawals/reject")
async def reject_withdrawal(
    request: AdminWithdrawalRejectionRequest,
    admin_id: int = Depends(get_current_admin_id),
):
    """Reject a withdrawal request (admin only)"""
    context = get_context()
    admin_service = context["admin_service"]

    try:
        tx = admin_service.reject_withdrawal(admin_id, request.tx_id, request.reason)
        return {
            "id": tx.id,
            "status": tx.status.value,
            "rejected_at": tx.rejected_at.isoformat() if tx.rejected_at else None,
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.post("/admin/accounts/freeze")
async def freeze_account(
    request: AdminAccountFreezeRequest, admin_id: int = Depends(get_current_admin_id)
):
    """Freeze an account (admin only)"""
    context = get_context()
    admin_service = context["admin_service"]

    try:
        account = admin_service.freeze_account(
            admin_id, request.account_id, request.reason
        )
        return {
            "id": account.id,
            "user_id": account.user_id,
            "status": account.status.value,
            "frozen": account.frozen,
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.post("/admin/accounts/unfreeze")
async def unfreeze_account(
    request: AdminAccountUnfreezeRequest, admin_id: int = Depends(get_current_admin_id)
):
    """Unfreeze an account (admin only)"""
    context = get_context()
    admin_service = context["admin_service"]

    try:
        account = admin_service.unfreeze_account(admin_id, request.account_id)
        return {
            "id": account.id,
            "user_id": account.user_id,
            "status": account.status.value,
            "frozen": account.frozen,
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.get("/admin/accounts/{account_id}")
async def get_account_info(
    account_id: int, admin_id: int = Depends(get_current_admin_id)
):
    """Get detailed account information (admin only)"""
    context = get_context()
    admin_service = context["admin_service"]

    try:
        account_info = admin_service.get_account_info(admin_id, account_id)
        return account_info
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.get("/admin/audit-logs", response_model=List[AuditLogResponse])
async def get_audit_logs(
    limit: int = 100, admin_id: int = Depends(get_current_admin_id)
):
    """Get audit logs (admin only)"""
    context = get_context()
    admin_service = context["admin_service"]

    try:
        logs = admin_service.get_audit_logs(admin_id, limit=limit)
        return [
            AuditLogResponse(
                id=log.id,
                actor=log.actor,
                action=log.action,
                entity=log.entity,
                metadata=log.metadata,
                created_at=log.created_at.isoformat(),
            )
            for log in logs
        ]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@app.get("/admin/market-overview")
async def get_market_overview(admin_id: int = Depends(get_current_admin_id)):
    """Get market overview for monitoring (admin only)"""
    context = get_context()
    admin_service = context["admin_service"]

    try:
        overview = admin_service.get_market_overview(admin_id)
        return overview
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
