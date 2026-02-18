"""ETL pipeline for property data ingestion."""

from __future__ import annotations

import hashlib
from datetime import datetime

import structlog

from app.services.address import NormalizedAddress, normalize
from app.services.entity_resolution import resolve_from_candidates
from app.services.geocoding import GeocodingService
from app.services.ingestion.base import RawPropertyRecord
from app.services.quality import DataQualityScore, calculate_quality_score

logger = structlog.get_logger()


class IngestionPipeline:
    """ETL pipeline for property data ingestion.

    Stages:
        1. Extract — Fetch from provider (handled by adapters)
        2. Transform — Normalize, geocode, entity-resolve, score quality
        3. Load — Upsert to database (requires DB session)
    """

    def __init__(self) -> None:
        self.geocoder = GeocodingService()

    async def process_record(
        self,
        raw: RawPropertyRecord,
        existing_candidates: list[dict[str, object]] | None = None,
    ) -> ProcessedRecord | None:
        """Process a single raw record through the pipeline.

        This method handles the Transform stage. The caller is responsible
        for providing candidate matches (from DB queries) and persisting
        the result.

        Args:
            raw: Raw property record from a provider adapter.
            existing_candidates: Pre-fetched candidate matches for
                entity resolution. If None, entity resolution is skipped.

        Returns:
            ProcessedRecord ready for database upsert, or None on failure.
        """
        try:
            # 1. TRANSFORM: Normalize address
            address: NormalizedAddress | None = None
            if raw.address_raw:
                address = normalize(raw.address_raw)

            # 2. TRANSFORM: Geocode if needed
            lat, lng = raw.latitude, raw.longitude
            if (lat is None or lng is None) and address:
                formatted = address.formatted_address or ""
                if formatted:
                    geo_result = await self.geocoder.geocode(
                        address=formatted,
                    )
                    if geo_result:
                        lat = geo_result.latitude
                        lng = geo_result.longitude

            # 3. TRANSFORM: Entity resolution
            canonical_id: str | None = None
            entity_confidence = 0.0
            if existing_candidates:
                entity_result = resolve_from_candidates(
                    address=(
                        address.formatted_address if address else None
                    ),
                    lat=lat,
                    lng=lng,
                    parcel_id=raw.parcel_id,
                    candidates=existing_candidates,
                )
                if entity_result.action == "auto_merge":
                    canonical_id = entity_result.canonical_id
                entity_confidence = entity_result.confidence

            # 4. Generate property ID
            property_id = canonical_id or generate_property_id(
                raw, address
            )

            # 5. TRANSFORM: Calculate quality score
            property_data = extract_property_data(raw.raw_data)
            quality = calculate_quality_score(
                property_data,
                source_timestamp=raw.extraction_timestamp,
            )

            logger.info(
                "Processed property",
                property_id=property_id,
                source=raw.source_system,
                quality_score=quality.score,
            )

            return ProcessedRecord(
                property_id=property_id,
                source_system=raw.source_system,
                source_type=raw.source_type,
                source_record_id=raw.source_record_id,
                address=address,
                latitude=lat,
                longitude=lng,
                quality=quality,
                canonical_id=canonical_id,
                entity_confidence=entity_confidence,
                raw_data=raw.raw_data,
                extraction_timestamp=raw.extraction_timestamp,
            )

        except Exception as e:
            logger.error(
                "Failed to process record",
                source=raw.source_system,
                source_id=raw.source_record_id,
                error=str(e),
            )
            return None


class ProcessedRecord:
    """Result of processing a raw record through the pipeline."""

    def __init__(
        self,
        property_id: str,
        source_system: str,
        source_type: str,
        source_record_id: str,
        address: NormalizedAddress | None,
        latitude: float | None,
        longitude: float | None,
        quality: DataQualityScore,
        canonical_id: str | None,
        entity_confidence: float,
        raw_data: dict[str, object],
        extraction_timestamp: datetime,
    ) -> None:
        self.property_id = property_id
        self.source_system = source_system
        self.source_type = source_type
        self.source_record_id = source_record_id
        self.address = address
        self.latitude = latitude
        self.longitude = longitude
        self.quality = quality
        self.canonical_id = canonical_id
        self.entity_confidence = entity_confidence
        self.raw_data = raw_data
        self.extraction_timestamp = extraction_timestamp


def generate_property_id(
    raw: RawPropertyRecord,
    address: NormalizedAddress | None,
) -> str:
    """Generate a Dharma property ID.

    Format: {STATE}-{HASH} where HASH is derived from
    the parcel ID or source record ID.

    Args:
        raw: Raw property record.
        address: Normalized address (for state code).

    Returns:
        Property ID string.
    """
    state = "XX"
    if address and address.state:
        state = address.state

    # Create hash from parcel ID or source record
    hash_input = (
        raw.parcel_id
        or f"{raw.source_system}:{raw.source_record_id}"
    )

    hash_suffix = hashlib.md5(  # noqa: S324
        hash_input.encode()
    ).hexdigest()[:10].upper()

    return f"{state}-{hash_suffix}"


def extract_property_data(raw_data: dict[str, object]) -> dict[str, object]:
    """Extract property fields from raw provider data.

    Maps common field names from various provider formats
    to the standard quality scoring fields.

    Args:
        raw_data: Raw data dictionary from provider.

    Returns:
        Dict with standardized field names for quality scoring.
    """
    return {
        "address": raw_data.get("address"),
        "city": raw_data.get("city"),
        "state": raw_data.get("state"),
        "zip_code": raw_data.get("zip") or raw_data.get("zip_code"),
        "latitude": raw_data.get("lat") or raw_data.get("latitude"),
        "longitude": raw_data.get("lng") or raw_data.get("longitude"),
        "lot_sqft": raw_data.get("lot_sqft"),
        "property_type": raw_data.get("property_type"),
        "bedrooms": raw_data.get("bedrooms"),
        "bathrooms": raw_data.get("bathrooms"),
        "sqft": raw_data.get("sqft"),
        "year_built": raw_data.get("year_built"),
        "assessed_value": raw_data.get("assessed_value"),
    }
