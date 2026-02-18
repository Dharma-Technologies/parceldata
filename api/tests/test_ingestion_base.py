"""Tests for the provider adapter base class and RawPropertyRecord."""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import datetime

import pytest

from app.services.ingestion.base import ProviderAdapter, RawPropertyRecord


class MockAdapter(ProviderAdapter):
    """Concrete adapter for testing the abstract base."""

    name = "mock"
    source_type = "test"

    async def fetch_property(
        self, property_id: str
    ) -> RawPropertyRecord | None:
        if property_id == "missing":
            return None
        return RawPropertyRecord(
            source_system="mock",
            source_type="test",
            source_record_id=property_id,
            extraction_timestamp=datetime.utcnow(),
            raw_data={"id": property_id},
            parcel_id=f"APN-{property_id}",
        )

    async def fetch_by_address(
        self,
        street: str,
        city: str,
        state: str,
        zip_code: str | None = None,
    ) -> RawPropertyRecord | None:
        return RawPropertyRecord(
            source_system="mock",
            source_type="test",
            source_record_id="addr-1",
            extraction_timestamp=datetime.utcnow(),
            raw_data={"street": street, "city": city, "state": state},
            address_raw=f"{street}, {city}, {state}",
        )

    async def fetch_batch(
        self, property_ids: list[str]
    ) -> list[RawPropertyRecord]:
        results = []
        for pid in property_ids:
            record = await self.fetch_property(pid)
            if record:
                results.append(record)
        return results

    async def stream_region(
        self,
        state: str,
        county: str | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[RawPropertyRecord]:
        count = limit or 3
        for i in range(count):
            yield RawPropertyRecord(
                source_system="mock",
                source_type="test",
                source_record_id=f"region-{i}",
                extraction_timestamp=datetime.utcnow(),
                raw_data={"state": state, "index": i},
            )

    def get_coverage_info(self) -> dict[str, object]:
        return {
            "provider": "Mock",
            "coverage": "Test only",
            "data_types": ["test"],
        }


# --- RawPropertyRecord tests ---


def test_raw_record_required_fields() -> None:
    """Required fields are populated correctly."""
    record = RawPropertyRecord(
        source_system="test",
        source_type="parcel",
        source_record_id="123",
        extraction_timestamp=datetime(2024, 1, 1),
        raw_data={"key": "value"},
    )
    assert record.source_system == "test"
    assert record.source_type == "parcel"
    assert record.source_record_id == "123"
    assert record.raw_data == {"key": "value"}


def test_raw_record_optional_fields_default_none() -> None:
    """Optional parsed fields default to None."""
    record = RawPropertyRecord(
        source_system="test",
        source_type="parcel",
        source_record_id="123",
        extraction_timestamp=datetime(2024, 1, 1),
        raw_data={},
    )
    assert record.parcel_id is None
    assert record.address_raw is None
    assert record.latitude is None
    assert record.longitude is None


def test_raw_record_with_parsed_fields() -> None:
    """RawPropertyRecord accepts optional parsed fields."""
    record = RawPropertyRecord(
        source_system="regrid",
        source_type="parcel_data",
        source_record_id="R-456",
        extraction_timestamp=datetime(2024, 6, 15),
        raw_data={"full": "data"},
        parcel_id="TX-0001-ABC",
        address_raw="123 Main St, Austin, TX",
        latitude=30.2672,
        longitude=-97.7431,
    )
    assert record.parcel_id == "TX-0001-ABC"
    assert record.address_raw == "123 Main St, Austin, TX"
    assert record.latitude == 30.2672
    assert record.longitude == -97.7431


def test_raw_record_serialization() -> None:
    """RawPropertyRecord serializes to dict."""
    record = RawPropertyRecord(
        source_system="test",
        source_type="parcel",
        source_record_id="123",
        extraction_timestamp=datetime(2024, 1, 1, 12, 0, 0),
        raw_data={"nested": {"key": "val"}},
    )
    data = record.model_dump()
    assert data["source_system"] == "test"
    assert data["raw_data"] == {"nested": {"key": "val"}}
    assert data["parcel_id"] is None


# --- ProviderAdapter tests ---


def test_adapter_cannot_be_instantiated() -> None:
    """ProviderAdapter is abstract and cannot be instantiated directly."""
    with pytest.raises(TypeError):
        ProviderAdapter()  # type: ignore[abstract]


def test_adapter_stores_api_key() -> None:
    """Adapter stores the API key passed at construction."""
    adapter = MockAdapter(api_key="test-key-123")
    assert adapter.api_key == "test-key-123"


def test_adapter_api_key_defaults_to_none() -> None:
    """Adapter API key defaults to None."""
    adapter = MockAdapter()
    assert adapter.api_key is None


def test_adapter_name_and_source_type() -> None:
    """Concrete adapter has name and source_type."""
    adapter = MockAdapter()
    assert adapter.name == "mock"
    assert adapter.source_type == "test"


@pytest.mark.asyncio
async def test_fetch_property_found() -> None:
    """fetch_property returns a record for a valid ID."""
    adapter = MockAdapter()
    result = await adapter.fetch_property("prop-1")
    assert result is not None
    assert result.source_record_id == "prop-1"
    assert result.parcel_id == "APN-prop-1"


@pytest.mark.asyncio
async def test_fetch_property_not_found() -> None:
    """fetch_property returns None for a missing ID."""
    adapter = MockAdapter()
    result = await adapter.fetch_property("missing")
    assert result is None


@pytest.mark.asyncio
async def test_fetch_by_address() -> None:
    """fetch_by_address returns a record with address_raw set."""
    adapter = MockAdapter()
    result = await adapter.fetch_by_address(
        street="100 Congress Ave",
        city="Austin",
        state="TX",
    )
    assert result is not None
    assert result.address_raw == "100 Congress Ave, Austin, TX"


@pytest.mark.asyncio
async def test_fetch_batch() -> None:
    """fetch_batch returns records for valid IDs, skips missing."""
    adapter = MockAdapter()
    results = await adapter.fetch_batch(["a", "missing", "b"])
    assert len(results) == 2
    ids = [r.source_record_id for r in results]
    assert "a" in ids
    assert "b" in ids


@pytest.mark.asyncio
async def test_stream_region_yields_records() -> None:
    """stream_region yields RawPropertyRecords."""
    adapter = MockAdapter()
    records = []
    async for record in adapter.stream_region(state="TX", limit=2):
        records.append(record)
    assert len(records) == 2
    assert all(r.source_system == "mock" for r in records)


@pytest.mark.asyncio
async def test_stream_region_with_county() -> None:
    """stream_region accepts optional county parameter."""
    adapter = MockAdapter()
    records = []
    async for record in adapter.stream_region(
        state="TX", county="Travis", limit=1
    ):
        records.append(record)
    assert len(records) == 1


def test_get_coverage_info() -> None:
    """get_coverage_info returns provider metadata."""
    adapter = MockAdapter()
    info = adapter.get_coverage_info()
    assert info["provider"] == "Mock"
    assert "coverage" in info
    assert "data_types" in info
