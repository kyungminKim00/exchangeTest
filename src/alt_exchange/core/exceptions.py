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
