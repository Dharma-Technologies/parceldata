"""Tests for auth routes (P10-04 S5)."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_signup_requires_email(client: AsyncClient) -> None:
    """POST /v1/auth/signup without email returns 422."""
    resp = await client.post("/v1/auth/signup", json={})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_signup_invalid_email(client: AsyncClient) -> None:
    """POST /v1/auth/signup with bad email returns 422."""
    resp = await client.post(
        "/v1/auth/signup", json={"email": "not-an-email"}
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_signup_no_auth_needed(client: AsyncClient) -> None:
    """POST /v1/auth/signup is public (not 401)."""
    resp = await client.post(
        "/v1/auth/signup", json={"email": "test@example.com"}
    )
    # Should not be 401 (auth not required for signup)
    assert resp.status_code != 401


@pytest.mark.asyncio
async def test_signup_endpoint_exists(client: AsyncClient) -> None:
    """POST /v1/auth/signup is routed (not 404/405)."""
    resp = await client.post(
        "/v1/auth/signup", json={"email": "test@example.com"}
    )
    # Acceptable: 200 (success) or 500 (no DB)
    assert resp.status_code in (200, 400, 500)


@pytest.mark.asyncio
async def test_create_key_requires_auth(client: AsyncClient) -> None:
    """POST /v1/auth/keys without auth returns 401."""
    resp = await client.post("/v1/auth/keys", json={"name": "test"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_list_keys_requires_auth(client: AsyncClient) -> None:
    """GET /v1/auth/keys without auth returns 401."""
    resp = await client.get("/v1/auth/keys")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_revoke_key_requires_auth(client: AsyncClient) -> None:
    """DELETE /v1/auth/keys/1 without auth returns 401."""
    resp = await client.delete("/v1/auth/keys/1")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_create_key_with_auth_requires_admin(
    client: AsyncClient,
) -> None:
    """POST /v1/auth/keys with non-admin key returns 403."""
    resp = await client.post(
        "/v1/auth/keys",
        json={"name": "test"},
        headers={"X-API-Key": "pk_test_regular"},
    )
    # Dev fallback gives tier=free with no admin scope → 403
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_list_keys_with_auth(client: AsyncClient) -> None:
    """GET /v1/auth/keys with auth passes (may error on DB)."""
    resp = await client.get(
        "/v1/auth/keys",
        headers={"X-API-Key": "pk_test_listkeys"},
    )
    # Auth passes (not 401/403); may 500 without DB
    assert resp.status_code in (200, 500)
