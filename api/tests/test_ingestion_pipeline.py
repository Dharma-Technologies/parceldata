"""Tests for the data ingestion pipeline."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest

from app.services.address import normalize
from app.services.geocoding import GeocodingResult
from app.services.ingestion.base import RawPropertyRecord
from app.services.ingestion.pipeline import (
    IngestionPipeline,
    extract_property_data,
    generate_property_id,
)


def _raw_record(
    parcel_id: str | None = "TX-001-ABC",
    address_raw: str | None = "123 Main St, Austin, TX 78701",
    lat: float | None = 30.2672,
    lng: float | None = -97.7431,
) -> RawPropertyRecord:
    """Create a test RawPropertyRecord."""
    return RawPropertyRecord(
        source_system="test",
        source_type="parcel_data",
        source_record_id="TEST-123",
        extraction_timestamp=datetime(2024, 6, 1),
        raw_data={
            "address": "123 Main St",
            "city": "Austin",
            "state": "TX",
            "zip": "78701",
            "lat": 30.2672,
            "lng": -97.7431,
            "property_type": "single_family",
            "lot_sqft": 8000,
        },
        parcel_id=parcel_id,
        address_raw=address_raw,
        latitude=lat,
        longitude=lng,
    )


class TestGeneratePropertyId:
    """Tests for property ID generation."""

    def test_with_parcel_id(self) -> None:
        """Uses parcel ID for hash when available."""
        raw = _raw_record(parcel_id="TX-001-ABC")
        addr = normalize("123 Main St, Austin, TX")
        pid = generate_property_id(raw, addr)
        assert pid.startswith("TX-")
        assert len(pid) > 5

    def test_without_parcel_id(self) -> None:
        """Uses source system and record ID for hash."""
        raw = _raw_record(parcel_id=None)
        addr = normalize("123 Main St, Austin, TX")
        pid = generate_property_id(raw, addr)
        assert pid.startswith("TX-")

    def test_no_address_uses_xx(self) -> None:
        """Uses XX when no state available."""
        raw = _raw_record(parcel_id="SOME-APN")
        pid = generate_property_id(raw, None)
        assert pid.startswith("XX-")

    def test_deterministic(self) -> None:
        """Same input produces same ID."""
        raw = _raw_record()
        addr = normalize("123 Main St, Austin, TX")
        id1 = generate_property_id(raw, addr)
        id2 = generate_property_id(raw, addr)
        assert id1 == id2


class TestExtractPropertyData:
    """Tests for raw data extraction."""

    def test_basic_extraction(self) -> None:
        data = extract_property_data({
            "address": "123 Main",
            "city": "Austin",
            "state": "TX",
            "zip": "78701",
            "lat": 30.0,
            "lng": -97.0,
        })
        assert data["address"] == "123 Main"
        assert data["zip_code"] == "78701"
        assert data["latitude"] == 30.0

    def test_alternate_field_names(self) -> None:
        """Supports zip_code and latitude/longitude."""
        data = extract_property_data({
            "zip_code": "78702",
            "latitude": 30.5,
            "longitude": -97.5,
        })
        assert data["zip_code"] == "78702"
        assert data["latitude"] == 30.5

    def test_missing_fields(self) -> None:
        data = extract_property_data({})
        assert data["address"] is None
        assert data["city"] is None


class TestIngestionPipeline:
    """Tests for the IngestionPipeline."""

    def test_init(self) -> None:
        pipeline = IngestionPipeline()
        assert pipeline.geocoder is not None

    @pytest.mark.asyncio
    async def test_process_record_success(self) -> None:
        """Processes a complete raw record."""
        pipeline = IngestionPipeline()
        raw = _raw_record()

        result = await pipeline.process_record(raw)

        assert result is not None
        assert result.property_id.startswith("TX-")
        assert result.source_system == "test"
        assert result.latitude == 30.2672
        assert result.longitude == -97.7431
        assert result.quality.score > 0

    @pytest.mark.asyncio
    async def test_process_record_with_address_normalization(
        self,
    ) -> None:
        """Normalizes address during processing."""
        pipeline = IngestionPipeline()
        raw = _raw_record(
            address_raw="456 Oak Avenue, Dallas, TX 75201"
        )

        result = await pipeline.process_record(raw)

        assert result is not None
        assert result.address is not None
        assert result.address.city == "Dallas"
        assert result.address.state == "TX"

    @pytest.mark.asyncio
    async def test_process_record_geocodes_when_no_coords(self) -> None:
        """Geocodes when lat/lng missing."""
        pipeline = IngestionPipeline()
        raw = _raw_record(
            lat=None,
            lng=None,
            address_raw="100 Congress Ave, Austin, TX",
        )

        mock_result = GeocodingResult(
            latitude=30.26,
            longitude=-97.74,
            accuracy="rooftop",
            source="census",
            confidence=0.95,
        )

        with patch.object(
            pipeline.geocoder,
            "geocode",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            result = await pipeline.process_record(raw)

        assert result is not None
        assert result.latitude == 30.26
        assert result.longitude == -97.74

    @pytest.mark.asyncio
    async def test_process_record_with_entity_resolution(self) -> None:
        """Uses entity resolution when candidates provided."""
        pipeline = IngestionPipeline()
        raw = _raw_record()

        candidates: list[dict[str, object]] = [
            {
                "id": "existing-prop-1",
                "address": "123 Main St, Austin, TX 78701",
                "latitude": 30.2672,
                "longitude": -97.7431,
                "apn": "TX-001-ABC",
                "match_type": "parcel_id",
            }
        ]

        result = await pipeline.process_record(
            raw, existing_candidates=candidates
        )

        assert result is not None
        assert result.property_id == "existing-prop-1"
        assert result.canonical_id == "existing-prop-1"

    @pytest.mark.asyncio
    async def test_process_record_no_merge(self) -> None:
        """No merge when candidates don't match."""
        pipeline = IngestionPipeline()
        raw = _raw_record()

        candidates: list[dict[str, object]] = [
            {
                "id": "far-prop",
                "latitude": 40.0,
                "longitude": -80.0,
                "match_type": "geocode",
            }
        ]

        result = await pipeline.process_record(
            raw, existing_candidates=candidates
        )

        assert result is not None
        assert result.canonical_id is None

    @pytest.mark.asyncio
    async def test_process_record_error_returns_none(self) -> None:
        """Returns None on processing errors."""
        pipeline = IngestionPipeline()
        raw = _raw_record()

        with patch(
            "app.services.ingestion.pipeline.normalize",
            side_effect=Exception("parse error"),
        ):
            result = await pipeline.process_record(raw)

        assert result is None

    @pytest.mark.asyncio
    async def test_quality_score_computed(self) -> None:
        """Quality score is computed for the record."""
        pipeline = IngestionPipeline()
        raw = _raw_record()

        result = await pipeline.process_record(raw)

        assert result is not None
        assert result.quality.score > 0
        assert result.quality.confidence in ("low", "medium", "high")

    @pytest.mark.asyncio
    async def test_processed_record_fields(self) -> None:
        """ProcessedRecord has all expected fields."""
        pipeline = IngestionPipeline()
        raw = _raw_record()

        result = await pipeline.process_record(raw)

        assert result is not None
        assert result.source_system == "test"
        assert result.source_type == "parcel_data"
        assert result.source_record_id == "TEST-123"
        assert result.raw_data is not None
        assert result.extraction_timestamp == datetime(2024, 6, 1)
