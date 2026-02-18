"""Custom exception classes for the ParcelData SDK."""

from __future__ import annotations


class ParcelDataError(Exception):
    """Base exception for all ParcelData SDK errors."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class AuthenticationError(ParcelDataError):
    """Raised when API key is invalid or missing."""

    def __init__(self, message: str = "Invalid or missing API key") -> None:
        super().__init__(message, status_code=401)


class RateLimitError(ParcelDataError):
    """Raised when rate limit is exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: float | None = None,
    ) -> None:
        self.retry_after = retry_after
        super().__init__(message, status_code=429)


class NotFoundError(ParcelDataError):
    """Raised when a requested resource is not found."""

    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(message, status_code=404)


class ValidationError(ParcelDataError):
    """Raised when request parameters are invalid."""

    def __init__(self, message: str = "Validation error") -> None:
        super().__init__(message, status_code=422)


class QuotaExceededError(ParcelDataError):
    """Raised when monthly API quota is exceeded."""

    def __init__(self, message: str = "Monthly API quota exceeded") -> None:
        super().__init__(message, status_code=429)
