"""Tests for usage tracking middleware (P10-04 S9)."""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware

from app.middleware import UsageTrackingMiddleware as ExportedMiddleware
from app.middleware.usage_tracking import UsageTrackingMiddleware


class TestUsageTrackingMiddleware:
    """UsageTrackingMiddleware class."""

    def test_class_exists(self) -> None:
        assert UsageTrackingMiddleware is not None

    def test_has_dispatch_method(self) -> None:
        assert hasattr(UsageTrackingMiddleware, "dispatch")

    def test_is_middleware(self) -> None:
        assert issubclass(UsageTrackingMiddleware, BaseHTTPMiddleware)

    def test_exported_from_init(self) -> None:
        assert ExportedMiddleware is UsageTrackingMiddleware
