"""Tests for agent-readable endpoints."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_llms_txt_returns_200(client: AsyncClient) -> None:
    """GET /llms.txt returns plain text."""
    resp = await client.get("/llms.txt")
    assert resp.status_code == 200
    assert "text/plain" in resp.headers["content-type"]
    text = resp.text
    assert "# ParcelData.ai API" in text
    assert "/v1/properties/{parcel_id}" in text
    assert "data_quality" in text


@pytest.mark.asyncio
async def test_llms_txt_no_auth_required(client: AsyncClient) -> None:
    """GET /llms.txt does not require authentication."""
    resp = await client.get("/llms.txt")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_llms_txt_contains_endpoints(client: AsyncClient) -> None:
    """GET /llms.txt documents key endpoints."""
    resp = await client.get("/llms.txt")
    text = resp.text
    assert "Property Lookup" in text
    assert "Property Search" in text
    assert "Comparable Properties" in text
    assert "Batch Lookup" in text
    assert "MCP Server" in text
    assert "SDK" in text


@pytest.mark.asyncio
async def test_ai_plugin_json(client: AsyncClient) -> None:
    """GET /.well-known/ai-plugin.json returns valid manifest."""
    resp = await client.get("/.well-known/ai-plugin.json")
    assert resp.status_code == 200
    body = resp.json()
    assert body["schema_version"] == "v1"
    assert body["name_for_human"] == "ParcelData.ai"
    assert body["name_for_model"] == "parceldata"
    assert "description_for_human" in body
    assert "description_for_model" in body
    assert body["auth"]["type"] == "service_http"
    assert body["api"]["type"] == "openapi"


@pytest.mark.asyncio
async def test_ai_plugin_no_auth_required(client: AsyncClient) -> None:
    """GET /.well-known/ai-plugin.json does not require authentication."""
    resp = await client.get("/.well-known/ai-plugin.json")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_openapi_spec_enhanced(client: AsyncClient) -> None:
    """OpenAPI spec includes enhanced metadata."""
    resp = await client.get("/openapi.json")
    assert resp.status_code == 200
    data = resp.json()
    info = data["info"]
    assert info["title"] == "ParcelData.ai API"
    assert info["version"] == "1.0.0"
    assert info["license"]["name"] == "MIT"
    assert info["contact"]["email"] == "hello@dharma.tech"
    assert len(data.get("tags", [])) >= 5
    assert "servers" in data
