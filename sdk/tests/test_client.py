"""Tests for ParcelDataClient."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from parceldata.client import ParcelDataClient
from parceldata.exceptions import (
    AuthenticationError,
    NotFoundError,
)
from parceldata.models import BatchResults, Property, SearchResults


class TestClientInit:
    def test_default_init(self, api_key: str) -> None:
        client = ParcelDataClient(api_key)
        assert client.api_key == api_key
        assert client.base_url == "https://api.parceldata.ai/v1"
        assert client.timeout == 30.0
        assert client.max_retries == 3

    def test_custom_init(self, api_key: str) -> None:
        client = ParcelDataClient(
            api_key,
            base_url="http://localhost:8000/v1/",
            timeout=60.0,
            max_retries=5,
        )
        assert client.base_url == "http://localhost:8000/v1"
        assert client.timeout == 60.0
        assert client.max_retries == 5


class TestPropertyLookup:
    @pytest.mark.asyncio()
    async def test_property_lookup(
        self,
        api_key: str,
        sample_property_data: dict[str, object],
    ) -> None:
        client = ParcelDataClient(api_key)
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_property_data

        mock_http = AsyncMock()
        mock_http.request = AsyncMock(return_value=mock_response)
        mock_http.is_closed = False
        client._client = mock_http

        result = await client.property_lookup("TX-TRAVIS-12345")
        assert isinstance(result, Property)
        assert result.property_id == "TX-TRAVIS-12345"
        await client.close()

    @pytest.mark.asyncio()
    async def test_property_lookup_with_tier(
        self,
        api_key: str,
        sample_property_data: dict[str, object],
    ) -> None:
        client = ParcelDataClient(api_key)
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_property_data

        mock_http = AsyncMock()
        mock_http.request = AsyncMock(return_value=mock_response)
        mock_http.is_closed = False
        client._client = mock_http

        await client.property_lookup("TX-TRAVIS-12345", tier="micro")
        mock_http.request.assert_called_once_with(
            "GET",
            "/properties/TX-TRAVIS-12345",
            params={"detail": "micro"},
            json=None,
        )
        await client.close()


class TestPropertySearch:
    @pytest.mark.asyncio()
    async def test_property_search(
        self,
        api_key: str,
        sample_search_data: dict[str, object],
    ) -> None:
        client = ParcelDataClient(api_key)
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_search_data

        mock_http = AsyncMock()
        mock_http.request = AsyncMock(return_value=mock_response)
        mock_http.is_closed = False
        client._client = mock_http

        result = await client.property_search({"city": "Austin", "state": "TX"})
        assert isinstance(result, SearchResults)
        assert result.total == 1
        await client.close()


class TestBatchLookup:
    @pytest.mark.asyncio()
    async def test_batch_lookup(
        self,
        api_key: str,
        sample_batch_data: dict[str, object],
    ) -> None:
        client = ParcelDataClient(api_key)
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_batch_data

        mock_http = AsyncMock()
        mock_http.request = AsyncMock(return_value=mock_response)
        mock_http.is_closed = False
        client._client = mock_http

        result = await client.batch_lookup(["TX-001", "TX-002"])
        assert isinstance(result, BatchResults)
        assert result.found == 1
        await client.close()


class TestErrorHandling:
    @pytest.mark.asyncio()
    async def test_authentication_error(self, api_key: str) -> None:
        client = ParcelDataClient(api_key, max_retries=1)
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"detail": "Invalid API key"}

        mock_http = AsyncMock()
        mock_http.request = AsyncMock(return_value=mock_response)
        mock_http.is_closed = False
        client._client = mock_http

        with pytest.raises(AuthenticationError, match="Invalid API key"):
            await client.property_lookup("TX-001")
        await client.close()

    @pytest.mark.asyncio()
    async def test_not_found_error(self, api_key: str) -> None:
        client = ParcelDataClient(api_key, max_retries=1)
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.json.return_value = {"detail": "Property not found"}

        mock_http = AsyncMock()
        mock_http.request = AsyncMock(return_value=mock_response)
        mock_http.is_closed = False
        client._client = mock_http

        with pytest.raises(NotFoundError, match="Property not found"):
            await client.property_lookup("NONEXISTENT")
        await client.close()

    @pytest.mark.asyncio()
    async def test_rate_limit_retry(
        self,
        api_key: str,
        sample_property_data: dict[str, object],
    ) -> None:
        client = ParcelDataClient(api_key, max_retries=3)
        rate_limited = MagicMock()
        rate_limited.status_code = 429
        rate_limited.headers = {"Retry-After": "0.01"}
        rate_limited.json.return_value = {"detail": "Rate limited"}

        success = MagicMock()
        success.status_code = 200
        success.json.return_value = sample_property_data

        mock_http = AsyncMock()
        mock_http.request = AsyncMock(side_effect=[rate_limited, success])
        mock_http.is_closed = False
        client._client = mock_http

        result = await client.property_lookup("TX-001")
        assert isinstance(result, Property)
        assert mock_http.request.call_count == 2
        await client.close()


class TestContextManager:
    @pytest.mark.asyncio()
    async def test_async_context_manager(self, api_key: str) -> None:
        async with ParcelDataClient(api_key) as client:
            assert client.api_key == api_key
