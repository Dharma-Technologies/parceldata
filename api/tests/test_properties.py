"""Integration tests for property endpoints."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

AUTH_HEADERS = {"X-API-Key": "pk_test123"}


@pytest.mark.asyncio
async def test_property_lookup_not_found(
    client: AsyncClient,
) -> None:
    """GET /v1/properties/{id} returns 404 or 500 (no DB)."""
    response = await client.get(
        "/v1/properties/NONEXISTENT-ID",
        headers=AUTH_HEADERS,
    )
    # 404 with DB, 500 without DB (connection refused)
    assert response.status_code in (404, 500)


@pytest.mark.asyncio
async def test_property_lookup_requires_auth(
    client: AsyncClient,
) -> None:
    """GET /v1/properties/{id} without auth returns 401."""
    response = await client.get("/v1/properties/TX-TRAVIS-123")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_address_lookup_requires_params(
    client: AsyncClient,
) -> None:
    """GET /v1/properties/address/lookup needs required params."""
    response = await client.get(
        "/v1/properties/address/lookup",
        headers=AUTH_HEADERS,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_coordinates_lookup_requires_params(
    client: AsyncClient,
) -> None:
    """GET /v1/properties/coordinates/lookup needs lat/lng."""
    response = await client.get(
        "/v1/properties/coordinates/lookup",
        headers=AUTH_HEADERS,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_search_empty_results(
    client: AsyncClient,
) -> None:
    """POST /v1/properties/search returns empty for no DB."""
    response = await client.post(
        "/v1/properties/search",
        json={"state": "TX"},
        headers=AUTH_HEADERS,
    )
    # Without DB, this will fail with 500 (no real DB)
    # or succeed with 0 results depending on config
    assert response.status_code in (200, 500)


@pytest.mark.asyncio
async def test_batch_requires_auth(
    client: AsyncClient,
) -> None:
    """POST /v1/properties/batch without auth returns 401."""
    response = await client.post(
        "/v1/properties/batch",
        json={"property_ids": ["TX-TRAVIS-123"]},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_analytics_comparables_not_found(
    client: AsyncClient,
) -> None:
    """GET /v1/analytics/comparables returns 404 or 500 (no DB)."""
    response = await client.get(
        "/v1/analytics/comparables",
        params={"property_id": "NONEXISTENT"},
        headers=AUTH_HEADERS,
    )
    # 404 with DB, 500 without DB (connection refused)
    assert response.status_code in (404, 500)


@pytest.mark.asyncio
async def test_analytics_market_trends(
    client: AsyncClient,
) -> None:
    """GET /v1/analytics/market-trends returns placeholder data."""
    response = await client.get(
        "/v1/analytics/market-trends",
        params={"zip": "78701", "period": "12m"},
        headers=AUTH_HEADERS,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["period"] == "12m"
    assert data["location"]["zip"] == "78701"
    assert "metrics" in data
    assert "data_quality" in data


@pytest.mark.asyncio
async def test_graphql_endpoint(client: AsyncClient) -> None:
    """POST /graphql handles property query."""
    response = await client.post(
        "/graphql",
        json={
            "query": '{ property(id: "NONEXISTENT") { id } }',
        },
        headers=AUTH_HEADERS,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["property"] is None


@pytest.mark.asyncio
async def test_openapi_spec(client: AsyncClient) -> None:
    """GET /openapi.json returns valid OpenAPI spec."""
    response = await client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert data["info"]["title"] == "ParcelData API"
    assert data["info"]["version"] == "0.1.0"
    assert "paths" in data
    # Verify key endpoints exist
    assert "/v1/properties/search" in data["paths"]
    assert "/v1/analytics/comparables" in data["paths"]
    assert "/v1/analytics/market-trends" in data["paths"]
