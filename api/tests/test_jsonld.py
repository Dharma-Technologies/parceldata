"""Tests for JSON-LD structured data."""

from __future__ import annotations

import json

import pytest
from httpx import AsyncClient

from app.middleware.jsonld import (
    DATA_CATALOG_JSONLD,
    ORGANIZATION_JSONLD,
    WEB_API_JSONLD,
    get_jsonld_script,
)


class TestJsonLdSchemas:
    def test_organization_schema(self) -> None:
        assert ORGANIZATION_JSONLD["@type"] == "Organization"
        assert ORGANIZATION_JSONLD["name"] == "ParcelData.ai"
        assert "@context" in ORGANIZATION_JSONLD

    def test_web_api_schema(self) -> None:
        assert WEB_API_JSONLD["@type"] == "WebAPI"
        assert WEB_API_JSONLD["name"] == "ParcelData.ai API"
        assert "provider" in WEB_API_JSONLD

    def test_data_catalog_schema(self) -> None:
        assert DATA_CATALOG_JSONLD["@type"] == "DataCatalog"
        assert len(DATA_CATALOG_JSONLD["dataset"]) >= 3

    def test_get_jsonld_script_contains_all_schemas(self) -> None:
        script = get_jsonld_script()
        assert script.count('<script type="application/ld+json">') == 3
        assert "Organization" in script
        assert "WebAPI" in script
        assert "DataCatalog" in script

    def test_jsonld_is_valid_json(self) -> None:
        script = get_jsonld_script()
        # Extract JSON from each script tag
        parts = script.split("</script>")
        for part in parts:
            if '<script type="application/ld+json">' in part:
                json_str = part.split(
                    '<script type="application/ld+json">',
                )[1]
                data = json.loads(json_str)
                assert "@context" in data
                assert "@type" in data


@pytest.mark.asyncio
async def test_jsonld_endpoint(client: AsyncClient) -> None:
    """GET /jsonld returns HTML with JSON-LD script tags."""
    resp = await client.get("/jsonld")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert '<script type="application/ld+json">' in resp.text


@pytest.mark.asyncio
async def test_jsonld_no_auth_required(client: AsyncClient) -> None:
    """GET /jsonld does not require authentication."""
    resp = await client.get("/jsonld")
    assert resp.status_code == 200
