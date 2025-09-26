class ExchangeError(Exception):
    """Base exception for exchange domain errors."""


class InsufficientBalanceError(ExchangeError):
    """Raised when an account lacks the required available balance."""


class InvalidOrderError(ExchangeError):
    """Raised when an order fails validation checks."""


class EntityNotFoundError(ExchangeError):
    """Raised when a requested entity is missing."""


class SettlementError(ExchangeError):
    """Raised when settlement operations fail."""


class OrderLinkError(ExchangeError):
    """Raised when OCO order linking operations fail."""


class StopOrderError(ExchangeError):
    """Raised when stop order operations fail."""


class AdminPermissionError(ExchangeError):
    """Raised when admin operations lack proper permissions."""


class WithdrawalApprovalError(ExchangeError):
    """Raised when withdrawal approval operations fail."""
