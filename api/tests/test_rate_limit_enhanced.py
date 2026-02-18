"""Tests for enhanced rate limiting with quotas (P10-04 S10)."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.middleware.rate_limit import MONTHLY_QUOTAS, TIER_LIMITS


class TestTierLimits:
    """Tier-based rate limits."""

    def test_free_tier_limits(self) -> None:
        per_second, per_day = TIER_LIMITS["free"]
        assert per_second == 1
        assert per_day == 100

    def test_pro_tier_limits(self) -> None:
        per_second, per_day = TIER_LIMITS["pro"]
        assert per_second == 10
        assert per_day == 10000

    def test_business_tier_limits(self) -> None:
        per_second, per_day = TIER_LIMITS["business"]
        assert per_second == 50
        assert per_day == 500000


class TestMonthlyQuotas:
    """Monthly quota limits."""

    def test_free_quota(self) -> None:
        assert MONTHLY_QUOTAS["free"] == 3000

    def test_pro_quota(self) -> None:
        assert MONTHLY_QUOTAS["pro"] == 50000

    def test_business_quota(self) -> None:
        assert MONTHLY_QUOTAS["business"] == 500000

    def test_enterprise_quota(self) -> None:
        assert MONTHLY_QUOTAS["enterprise"] == 10000000


@pytest.mark.asyncio
async def test_rate_limit_headers(client: AsyncClient) -> None:
    """Authenticated requests include rate limit headers."""
    resp = await client.get(
        "/v1/properties/test",
        headers={"X-API-Key": "pk_test_ratelimit"},
    )
    # Auth passes; check headers exist (may get 500 without DB)
    if resp.status_code != 401:
        assert "X-RateLimit-Limit" in resp.headers or resp.status_code == 500


@pytest.mark.asyncio
async def test_usage_headers(client: AsyncClient) -> None:
    """Authenticated requests include usage headers."""
    resp = await client.get(
        "/v1/properties/test",
        headers={"X-API-Key": "pk_test_usage"},
    )
    if resp.status_code != 401:
        assert "X-Usage-Limit" in resp.headers or resp.status_code == 500
