"""Tests for Stripe webhook handler (P10-04 S8)."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_webhook_no_auth_needed(client: AsyncClient) -> None:
    """POST /webhooks/stripe is public (not 401)."""
    resp = await client.post(
        "/webhooks/stripe",
        content=b"{}",
        headers={"Content-Type": "application/json"},
    )
    # Should not be 401 — webhooks are public
    assert resp.status_code != 401


@pytest.mark.asyncio
async def test_webhook_requires_config(client: AsyncClient) -> None:
    """POST /webhooks/stripe returns 503 when webhook secret not configured."""
    resp = await client.post(
        "/webhooks/stripe",
        content=b'{"type": "test"}',
        headers={"Content-Type": "application/json"},
    )
    # Without stripe_webhook_secret configured, returns 503
    assert resp.status_code == 503


@pytest.mark.asyncio
async def test_webhook_endpoint_exists(client: AsyncClient) -> None:
    """POST /webhooks/stripe is routed (not 404/405)."""
    resp = await client.post(
        "/webhooks/stripe",
        content=b"{}",
        headers={"Content-Type": "application/json"},
    )
    assert resp.status_code not in (404, 405)


@pytest.mark.asyncio
async def test_webhook_get_not_allowed(client: AsyncClient) -> None:
    """GET /webhooks/stripe is not allowed (POST only)."""
    resp = await client.get("/webhooks/stripe")
    assert resp.status_code == 405
