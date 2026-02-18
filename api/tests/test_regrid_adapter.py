"""Tests for the Regrid provider adapter."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.ingestion.providers.regrid import RegridAdapter


class TestRegridAdapterInit:
    """Tests for RegridAdapter initialization."""

    def test_name_and_source_type(self) -> None:
        """Adapter has correct name and source_type."""
        adapter = RegridAdapter(api_key="test-key")
        assert adapter.name == "regrid"
        assert adapter.source_type == "parcel_data"

    def test_base_url(self) -> None:
        """Adapter uses the correct Regrid API base URL."""
        adapter = RegridAdapter(api_key="test-key")
        assert adapter.base_url == "https://app.regrid.com/api/v1"

    def test_api_key_stored(self) -> None:
        """API key is stored on the adapter."""
        adapter = RegridAdapter(api_key="my-regrid-key")
        assert adapter.api_key == "my-regrid-key"

    def test_httpx_client_created(self) -> None:
        """An httpx.AsyncClient is created at init."""
        adapter = RegridAdapter(api_key="test-key")
        assert adapter.client is not None


class TestRegridCoverageInfo:
    """Tests for coverage info."""

    def test_coverage_info_structure(self) -> None:
        """get_coverage_info returns expected keys."""
        adapter = RegridAdapter(api_key="test-key")
        info = adapter.get_coverage_info()
        assert info["provider"] == "Regrid"
        assert info["coverage"] == "Nationwide (US)"
        assert "data_types" in info
        assert "update_frequency" in info

    def test_coverage_data_types(self) -> None:
        """Coverage info includes parcel-related data types."""
        adapter = RegridAdapter(api_key="test-key")
        info = adapter.get_coverage_info()
        data_types = info["data_types"]
        assert isinstance(data_types, list)
        assert "parcel_boundaries" in data_types
        assert "ownership" in data_types


class TestRegridToRawRecord:
    """Tests for the _to_raw_record conversion method."""

    def test_basic_conversion(self) -> None:
        """Converts Regrid JSON to RawPropertyRecord."""
        adapter = RegridAdapter(api_key="test-key")
        data: dict[str, object] = {
            "id": "regrid-123",
            "properties": {
                "parcelnumb": "TX-001-ABC",
                "address": "123 Main St",
            },
            "geometry": {
                "type": "Point",
                "coordinates": [-97.7431, 30.2672],
            },
        }
        record = adapter._to_raw_record(data)
        assert record.source_system == "regrid"
        assert record.source_type == "parcel_data"
        assert record.source_record_id == "regrid-123"
        assert record.parcel_id == "TX-001-ABC"
        assert record.address_raw == "123 Main St"
        assert record.latitude == 30.2672
        assert record.longitude == -97.7431

    def test_missing_geometry(self) -> None:
        """Handles missing geometry gracefully."""
        adapter = RegridAdapter(api_key="test-key")
        data: dict[str, object] = {
            "id": "regrid-456",
            "properties": {"parcelnumb": "CA-002"},
        }
        record = adapter._to_raw_record(data)
        assert record.latitude is None
        assert record.longitude is None

    def test_missing_properties(self) -> None:
        """Handles missing properties gracefully."""
        adapter = RegridAdapter(api_key="test-key")
        data: dict[str, object] = {"id": "regrid-789"}
        record = adapter._to_raw_record(data)
        assert record.parcel_id is None
        assert record.address_raw is None

    def test_polygon_geometry_no_coords(self) -> None:
        """Polygon geometry does not extract lat/lng."""
        adapter = RegridAdapter(api_key="test-key")
        data: dict[str, object] = {
            "id": "regrid-poly",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]],
            },
        }
        record = adapter._to_raw_record(data)
        assert record.latitude is None
        assert record.longitude is None

    def test_empty_parcelnumb(self) -> None:
        """Empty parcelnumb maps to None."""
        adapter = RegridAdapter(api_key="test-key")
        data: dict[str, object] = {
            "id": "regrid-empty",
            "properties": {"parcelnumb": "", "address": ""},
        }
        record = adapter._to_raw_record(data)
        assert record.parcel_id is None
        assert record.address_raw is None


class TestRegridFetchProperty:
    """Tests for fetch_property with mocked HTTP."""

    @pytest.mark.asyncio
    async def test_fetch_property_success(self) -> None:
        """fetch_property returns a record on success."""
        adapter = RegridAdapter(api_key="test-key")
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "id": "123",
            "properties": {"parcelnumb": "APN-1"},
            "geometry": {
                "type": "Point",
                "coordinates": [-97.0, 30.0],
            },
        }

        with patch.object(
            adapter.client,
            "get",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await adapter.fetch_property("123")

        assert result is not None
        assert result.source_record_id == "123"
        assert result.parcel_id == "APN-1"

    @pytest.mark.asyncio
    async def test_fetch_by_address_success(self) -> None:
        """fetch_by_address returns a record on success."""
        adapter = RegridAdapter(api_key="test-key")
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "results": [
                {
                    "id": "addr-1",
                    "properties": {
                        "parcelnumb": "APN-A",
                        "address": "100 Main St",
                    },
                }
            ]
        }

        with patch.object(
            adapter.client,
            "get",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await adapter.fetch_by_address(
                street="100 Main St",
                city="Austin",
                state="TX",
            )

        assert result is not None
        assert result.parcel_id == "APN-A"

    @pytest.mark.asyncio
    async def test_fetch_by_address_no_results(self) -> None:
        """fetch_by_address returns None when no results."""
        adapter = RegridAdapter(api_key="test-key")
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"results": []}

        with patch.object(
            adapter.client,
            "get",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await adapter.fetch_by_address(
                street="Fake St",
                city="Nowhere",
                state="XX",
            )

        assert result is None

    @pytest.mark.asyncio
    async def test_fetch_batch_returns_list(self) -> None:
        """fetch_batch returns list of records."""
        adapter = RegridAdapter(api_key="test-key")

        async def mock_fetch(pid: str) -> object:
            if pid == "bad":
                return None
            mock_resp = AsyncMock()
            mock_resp.status_code = 200
            mock_resp.raise_for_status = lambda: None
            mock_resp.json.return_value = {
                "id": pid,
                "properties": {"parcelnumb": f"APN-{pid}"},
            }
            return adapter._to_raw_record(mock_resp.json.return_value)

        with patch.object(
            adapter, "fetch_property", side_effect=mock_fetch
        ):
            results = await adapter.fetch_batch(["a", "bad", "b"])

        assert len(results) == 2
