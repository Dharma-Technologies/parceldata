"""Tests for account routes (P10-04 S6)."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.routes.account import MONTHLY_LIMITS


class TestMonthlyLimits:
    """Monthly quota limits by tier."""

    def test_free_limit(self) -> None:
        assert MONTHLY_LIMITS["free"] == 3000

    def test_pro_limit(self) -> None:
        assert MONTHLY_LIMITS["pro"] == 50000

    def test_business_limit(self) -> None:
        assert MONTHLY_LIMITS["business"] == 500000

    def test_enterprise_limit(self) -> None:
        assert MONTHLY_LIMITS["enterprise"] == 10000000


@pytest.mark.asyncio
async def test_usage_requires_auth(client: AsyncClient) -> None:
    """GET /v1/account/usage without auth returns 401."""
    resp = await client.get("/v1/account/usage")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_billing_requires_auth(client: AsyncClient) -> None:
    """GET /v1/account/billing without auth returns 401."""
    resp = await client.get("/v1/account/billing")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_upgrade_requires_auth(client: AsyncClient) -> None:
    """POST /v1/account/upgrade without auth returns 401."""
    resp = await client.post("/v1/account/upgrade?target_tier=pro")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_billing_with_auth(client: AsyncClient) -> None:
    """GET /v1/account/billing with auth returns billing info."""
    resp = await client.get(
        "/v1/account/billing",
        headers={"X-API-Key": "pk_test_billing"},
    )
    # Auth passes, billing returns 200 with stub data
    assert resp.status_code == 200
    body = resp.json()
    assert body["tier"] == "free"
    assert body["status"] == "active"
    assert "current_period" in body


@pytest.mark.asyncio
async def test_upgrade_invalid_tier(client: AsyncClient) -> None:
    """POST /v1/account/upgrade with invalid tier returns 400."""
    resp = await client.post(
        "/v1/account/upgrade?target_tier=invalid",
        headers={"X-API-Key": "pk_test_upgrade"},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_upgrade_returns_501(client: AsyncClient) -> None:
    """POST /v1/account/upgrade returns 501 (not yet implemented)."""
    resp = await client.post(
        "/v1/account/upgrade?target_tier=pro",
        headers={"X-API-Key": "pk_test_upgrade"},
    )
    assert resp.status_code == 501
