class ExchangeError(Exception):
    """Base exception for exchange domain errors."""

    def __init__(self, message: str, error_code: str = None, details: dict = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}


class InsufficientBalanceError(ExchangeError):
    """Raised when an account lacks the required available balance."""

    def __init__(
        self,
        message: str,
        account_id: int = None,
        asset: str = None,
        required: float = None,
        available: float = None,
    ):
        super().__init__(
            message,
            "INSUFFICIENT_BALANCE",
            {
                "account_id": account_id,
                "asset": asset,
                "required": required,
                "available": available,
            },
        )


class InvalidOrderError(ExchangeError):
    """Raised when an order fails validation checks."""

    def __init__(
        self, message: str, order_id: int = None, validation_errors: list = None
    ):
        super().__init__(
            message,
            "INVALID_ORDER",
            {"order_id": order_id, "validation_errors": validation_errors or []},
        )


class EntityNotFoundError(ExchangeError):
    """Raised when a requested entity is missing."""

    def __init__(self, message: str, entity_type: str = None, entity_id: int = None):
        super().__init__(
            message,
            "ENTITY_NOT_FOUND",
            {"entity_type": entity_type, "entity_id": entity_id},
        )


class SettlementError(ExchangeError):
    """Raised when settlement operations fail."""

    def __init__(self, message: str, trade_id: int = None, account_id: int = None):
        super().__init__(
            message,
            "SETTLEMENT_ERROR",
            {"trade_id": trade_id, "account_id": account_id},
        )


class OrderLinkError(ExchangeError):
    """Raised when OCO order linking operations fail."""

    def __init__(self, message: str, order_id: int = None, linked_order_id: int = None):
        super().__init__(
            message,
            "ORDER_LINK_ERROR",
            {"order_id": order_id, "linked_order_id": linked_order_id},
        )


class StopOrderError(ExchangeError):
    """Raised when stop order operations fail."""

    def __init__(self, message: str, order_id: int = None, stop_price: float = None):
        super().__init__(
            message,
            "STOP_ORDER_ERROR",
            {"order_id": order_id, "stop_price": stop_price},
        )


class AdminPermissionError(ExchangeError):
    """Raised when admin operations lack proper permissions."""

    def __init__(self, message: str, admin_id: int = None, operation: str = None):
        super().__init__(
            message,
            "ADMIN_PERMISSION_ERROR",
            {"admin_id": admin_id, "operation": operation},
        )


class WithdrawalApprovalError(ExchangeError):
    """Raised when withdrawal approval operations fail."""

    def __init__(self, message: str, transaction_id: int = None, admin_id: int = None):
        super().__init__(
            message,
            "WITHDRAWAL_APPROVAL_ERROR",
            {"transaction_id": transaction_id, "admin_id": admin_id},
        )
