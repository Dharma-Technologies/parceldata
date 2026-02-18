"""Tests for the Census Bureau provider adapter."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.ingestion.providers.census import CensusAdapter


class TestCensusAdapterInit:
    """Tests for CensusAdapter initialization."""

    def test_name_and_source_type(self) -> None:
        adapter = CensusAdapter()
        assert adapter.name == "census"
        assert adapter.source_type == "demographics"

    def test_base_url(self) -> None:
        adapter = CensusAdapter()
        assert adapter.base_url == "https://api.census.gov/data"

    def test_api_key_optional(self) -> None:
        adapter = CensusAdapter()
        assert adapter.api_key is None

    def test_api_key_stored(self) -> None:
        adapter = CensusAdapter(api_key="census-key")
        assert adapter.api_key == "census-key"


class TestCensusFetchDemographics:
    """Tests for fetch_demographics with mocked HTTP."""

    @pytest.mark.asyncio
    async def test_state_level(self) -> None:
        """Fetch demographics at state level."""
        adapter = CensusAdapter()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = [
            ["B01003_001E", "B19013_001E", "state"],
            ["29145505", "64034", "48"],
        ]

        with patch.object(
            adapter.client,
            "get",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await adapter.fetch_demographics(state_fips="48")

        assert result["B01003_001E"] == "29145505"
        assert result["state"] == "48"

    @pytest.mark.asyncio
    async def test_county_level(self) -> None:
        """Fetch demographics at county level."""
        adapter = CensusAdapter()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = [
            ["B01003_001E", "county", "state"],
            ["1290188", "453", "48"],
        ]

        with patch.object(
            adapter.client,
            "get",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await adapter.fetch_demographics(
                state_fips="48", county_fips="453"
            )

        assert result["B01003_001E"] == "1290188"

    @pytest.mark.asyncio
    async def test_tract_level(self) -> None:
        """Fetch demographics at tract level."""
        adapter = CensusAdapter()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = [
            ["B01003_001E", "tract", "county", "state"],
            ["5432", "001800", "453", "48"],
        ]

        with patch.object(
            adapter.client,
            "get",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await adapter.fetch_demographics(
                state_fips="48", county_fips="453", tract="001800"
            )

        assert result["tract"] == "001800"

    @pytest.mark.asyncio
    async def test_empty_response(self) -> None:
        """Returns empty dict when no data rows."""
        adapter = CensusAdapter()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = [
            ["B01003_001E", "state"],
        ]

        with patch.object(
            adapter.client,
            "get",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await adapter.fetch_demographics(state_fips="99")

        assert result == {}


class TestCensusNotApplicable:
    """Tests that property-level methods return empty results."""

    @pytest.mark.asyncio
    async def test_fetch_property_returns_none(self) -> None:
        adapter = CensusAdapter()
        assert await adapter.fetch_property("any-id") is None

    @pytest.mark.asyncio
    async def test_fetch_by_address_returns_none(self) -> None:
        adapter = CensusAdapter()
        result = await adapter.fetch_by_address(
            street="123 Main", city="Austin", state="TX"
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_fetch_batch_returns_empty(self) -> None:
        adapter = CensusAdapter()
        assert await adapter.fetch_batch(["a", "b"]) == []

    @pytest.mark.asyncio
    async def test_stream_region_yields_nothing(self) -> None:
        adapter = CensusAdapter()
        records = [r async for r in adapter.stream_region(state="TX")]
        assert records == []


class TestCensusCoverageInfo:
    """Tests for coverage info."""

    def test_coverage_info(self) -> None:
        adapter = CensusAdapter()
        info = adapter.get_coverage_info()
        assert info["provider"] == "US Census Bureau"
        assert info["cost"] == "free"
        assert isinstance(info["data_types"], list)
