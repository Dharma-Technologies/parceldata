"""Tests for the ATTOM provider adapter."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.ingestion.providers.attom import ATTOMAdapter


class TestATTOMAdapterInit:
    """Tests for ATTOMAdapter initialization."""

    def test_name_and_source_type(self) -> None:
        adapter = ATTOMAdapter(api_key="test-key")
        assert adapter.name == "attom"
        assert adapter.source_type == "property_records"

    def test_base_url(self) -> None:
        adapter = ATTOMAdapter(api_key="test-key")
        assert adapter.base_url == "https://api.gateway.attomdata.com"

    def test_api_key_stored(self) -> None:
        adapter = ATTOMAdapter(api_key="my-attom-key")
        assert adapter.api_key == "my-attom-key"

    def test_httpx_client_created(self) -> None:
        adapter = ATTOMAdapter(api_key="test-key")
        assert adapter.client is not None


class TestATTOMToRawRecord:
    """Tests for the _to_raw_record conversion method."""

    def test_basic_conversion(self) -> None:
        adapter = ATTOMAdapter(api_key="test-key")
        data: dict[str, object] = {
            "identifier": {"attomId": 12345, "apn": "001-002-003"},
            "address": {
                "line1": "123 Main St",
                "line2": "Austin, TX 78701",
            },
            "location": {"latitude": 30.2672, "longitude": -97.7431},
        }
        record = adapter._to_raw_record(data)
        assert record.source_system == "attom"
        assert record.source_record_id == "12345"
        assert record.parcel_id == "001-002-003"
        assert record.address_raw == "123 Main St Austin, TX 78701"
        assert record.latitude == 30.2672
        assert record.longitude == -97.7431

    def test_missing_identifier(self) -> None:
        adapter = ATTOMAdapter(api_key="test-key")
        data: dict[str, object] = {
            "address": {"line1": "456 Oak Ave"},
        }
        record = adapter._to_raw_record(data)
        assert record.source_record_id == ""
        assert record.parcel_id is None

    def test_missing_location(self) -> None:
        adapter = ATTOMAdapter(api_key="test-key")
        data: dict[str, object] = {
            "identifier": {"attomId": 99},
        }
        record = adapter._to_raw_record(data)
        assert record.latitude is None
        assert record.longitude is None

    def test_empty_address(self) -> None:
        adapter = ATTOMAdapter(api_key="test-key")
        data: dict[str, object] = {
            "identifier": {"attomId": 1},
            "address": {"line1": "", "line2": ""},
        }
        record = adapter._to_raw_record(data)
        assert record.address_raw is None

    def test_non_dict_data(self) -> None:
        adapter = ATTOMAdapter(api_key="test-key")
        record = adapter._to_raw_record("not-a-dict")
        assert record.source_system == "attom"
        assert record.source_record_id == ""


class TestATTOMFetchProperty:
    """Tests for fetch_property with mocked HTTP."""

    @pytest.mark.asyncio
    async def test_fetch_property_success(self) -> None:
        adapter = ATTOMAdapter(api_key="test-key")
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "property": [
                {
                    "identifier": {"attomId": 555, "apn": "APN-X"},
                    "location": {"latitude": 30.0, "longitude": -97.0},
                }
            ]
        }

        with patch.object(
            adapter.client,
            "get",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await adapter.fetch_property("555")

        assert result is not None
        assert result.source_record_id == "555"
        assert result.parcel_id == "APN-X"

    @pytest.mark.asyncio
    async def test_fetch_property_no_results(self) -> None:
        adapter = ATTOMAdapter(api_key="test-key")
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"property": []}

        with patch.object(
            adapter.client,
            "get",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await adapter.fetch_property("999")

        assert result is None

    @pytest.mark.asyncio
    async def test_fetch_by_address_success(self) -> None:
        adapter = ATTOMAdapter(api_key="test-key")
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "property": [
                {
                    "identifier": {"attomId": 777},
                    "address": {
                        "line1": "100 Congress Ave",
                        "line2": "Austin, TX",
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
                street="100 Congress Ave",
                city="Austin",
                state="TX",
            )

        assert result is not None
        assert result.source_record_id == "777"


class TestATTOMCoverageInfo:
    """Tests for coverage info."""

    def test_coverage_info(self) -> None:
        adapter = ATTOMAdapter(api_key="test-key")
        info = adapter.get_coverage_info()
        assert info["provider"] == "ATTOM"
        assert "155M" in str(info["coverage"])
        assert isinstance(info["data_types"], list)
