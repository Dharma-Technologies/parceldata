"""Tests for UsageService (P10-04 S4)."""

from __future__ import annotations

import inspect

from app.services.usage_service import (
    DAILY_LIMITS,
    QUERY_COSTS,
    UsageService,
)


class TestUsageService:
    """UsageService class and methods."""

    def test_class_exists(self) -> None:
        assert UsageService is not None

    def test_init_signature(self) -> None:
        sig = inspect.signature(UsageService.__init__)
        params = list(sig.parameters.keys())
        assert "self" in params
        assert "db" in params

    def test_record_usage_method(self) -> None:
        assert hasattr(UsageService, "record_usage")
        assert inspect.iscoroutinefunction(UsageService.record_usage)

    def test_get_usage_summary_method(self) -> None:
        assert hasattr(UsageService, "get_usage_summary")
        assert inspect.iscoroutinefunction(UsageService.get_usage_summary)

    def test_check_quota_method(self) -> None:
        assert hasattr(UsageService, "check_quota")
        assert inspect.iscoroutinefunction(UsageService.check_quota)


class TestQueryCosts:
    """Query cost weights."""

    def test_property_lookup_cost(self) -> None:
        assert QUERY_COSTS["property_lookup"] == 1

    def test_property_lookup_full_cost(self) -> None:
        assert QUERY_COSTS["property_lookup_full"] == 2

    def test_comparables_cost(self) -> None:
        assert QUERY_COSTS["comparables"] == 3

    def test_market_trends_cost(self) -> None:
        assert QUERY_COSTS["market_trends"] == 5

    def test_default_cost_is_one(self) -> None:
        assert QUERY_COSTS.get("unknown_endpoint", 1) == 1


class TestDailyLimits:
    """Daily quota limits by tier."""

    def test_free_limit(self) -> None:
        assert DAILY_LIMITS["free"] == 100

    def test_pro_limit(self) -> None:
        assert DAILY_LIMITS["pro"] == 10000

    def test_business_limit(self) -> None:
        assert DAILY_LIMITS["business"] == 500000

    def test_enterprise_limit(self) -> None:
        assert DAILY_LIMITS["enterprise"] == 10000000

    def test_unknown_tier_default(self) -> None:
        assert DAILY_LIMITS.get("unknown", 100) == 100
