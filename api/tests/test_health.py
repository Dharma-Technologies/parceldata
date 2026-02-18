"""Tests for health and version endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_version(client: AsyncClient) -> None:
    """GET /version returns app info without auth."""
    resp = await client.get("/version")
    assert resp.status_code == 200
    body = resp.json()
    assert body["name"] == "ParcelData"
    assert body["api_version"] == "v1"


@pytest.mark.asyncio
async def test_health_returns_200(client: AsyncClient) -> None:
    """GET /health returns 200 (may be degraded without real DB/Redis)."""
    resp = await client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] in ("healthy", "degraded")
    assert "checks" in body


@pytest.mark.asyncio
async def test_unauthenticated_v1_returns_401(client: AsyncClient) -> None:
    """Requests to /v1/* without API key get 401."""
    resp = await client.get("/v1/properties/123")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_authenticated_v1_passes_auth(client: AsyncClient) -> None:
    """Requests to /v1/* with pk_ key pass auth (may get 404 without DB)."""
    resp = await client.get(
        "/v1/properties/NONEXISTENT",
        headers={"X-API-Key": "pk_test123"},
    )
    # Auth passes (not 401), but property doesn't exist without DB
    assert resp.status_code != 401
