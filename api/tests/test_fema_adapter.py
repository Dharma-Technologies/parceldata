"""Tests for the FEMA flood zone provider adapter."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.ingestion.providers.fema import FEMAAdapter


class TestFEMAAdapterInit:
    """Tests for FEMAAdapter initialization."""

    def test_name_and_source_type(self) -> None:
        adapter = FEMAAdapter()
        assert adapter.name == "fema"
        assert adapter.source_type == "flood_zones"

    def test_no_api_key_required(self) -> None:
        adapter = FEMAAdapter()
        assert adapter.api_key is None

    def test_base_url(self) -> None:
        adapter = FEMAAdapter()
        assert "hazards.fema.gov" in adapter.base_url


class TestFEMAGetFloodZone:
    """Tests for get_flood_zone with mocked HTTP."""

    @pytest.mark.asyncio
    async def test_zone_found(self) -> None:
        """Returns flood zone data when features found."""
        adapter = FEMAAdapter()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "features": [
                {
                    "attributes": {
                        "FLD_ZONE": "AE",
                        "ZONE_SUBTY": "FLOODWAY",
                        "SFHA_TF": "T",
                        "STATIC_BFE": 520.5,
                    }
                }
            ]
        }

        with patch.object(
            adapter.client,
            "get",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await adapter.get_flood_zone(30.2672, -97.7431)

        assert result.flood_zone == "AE"
        assert result.zone_subtype == "FLOODWAY"
        assert result.in_sfha is True
        assert result.base_flood_elevation == 520.5

    @pytest.mark.asyncio
    async def test_no_features_returns_default(self) -> None:
        """Returns default X zone when no features found."""
        adapter = FEMAAdapter()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"features": []}

        with patch.object(
            adapter.client,
            "get",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await adapter.get_flood_zone(30.0, -97.0)

        assert result.flood_zone == "X"
        assert result.in_sfha is False
        assert result.base_flood_elevation is None

    @pytest.mark.asyncio
    async def test_zone_x_not_sfha(self) -> None:
        """Zone X areas are not in SFHA."""
        adapter = FEMAAdapter()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "features": [
                {
                    "attributes": {
                        "FLD_ZONE": "X",
                        "ZONE_SUBTY": "",
                        "SFHA_TF": "F",
                        "STATIC_BFE": None,
                    }
                }
            ]
        }

        with patch.object(
            adapter.client,
            "get",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await adapter.get_flood_zone(35.0, -100.0)

        assert result.flood_zone == "X"
        assert result.in_sfha is False

    @pytest.mark.asyncio
    async def test_missing_attributes(self) -> None:
        """Handles features without attributes gracefully."""
        adapter = FEMAAdapter()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "features": [{"no_attributes": True}]
        }

        with patch.object(
            adapter.client,
            "get",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await adapter.get_flood_zone(30.0, -97.0)

        # Falls through to default
        assert result.flood_zone == "X"
        assert result.in_sfha is False


class TestFEMANotApplicable:
    """Tests that property-level methods return empty results."""

    @pytest.mark.asyncio
    async def test_fetch_property_returns_none(self) -> None:
        adapter = FEMAAdapter()
        assert await adapter.fetch_property("any-id") is None

    @pytest.mark.asyncio
    async def test_fetch_by_address_returns_none(self) -> None:
        adapter = FEMAAdapter()
        result = await adapter.fetch_by_address(
            street="123 Main", city="Austin", state="TX"
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_fetch_batch_returns_empty(self) -> None:
        adapter = FEMAAdapter()
        assert await adapter.fetch_batch(["a"]) == []

    @pytest.mark.asyncio
    async def test_stream_region_yields_nothing(self) -> None:
        adapter = FEMAAdapter()
        records = [r async for r in adapter.stream_region(state="TX")]
        assert records == []


class TestFEMACoverageInfo:
    """Tests for coverage info."""

    def test_coverage_info(self) -> None:
        adapter = FEMAAdapter()
        info = adapter.get_coverage_info()
        assert info["provider"] == "FEMA"
        assert info["cost"] == "free"
        assert "flood_zones" in info["data_types"]  # type: ignore[operator]
