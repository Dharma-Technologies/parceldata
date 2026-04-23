"""Parcel data ingest endpoint — CSV or JSON bulk ingestion."""

from __future__ import annotations

import hashlib
import io
import json
from csv import DictReader
from datetime import datetime
from typing import Any

import structlog
from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi import File as FastAPIFile
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.models import Address, Property
from app.services.address import normalize
from app.services.entity_resolution import resolve_from_candidates
from app.services.ingestion.base import RawPropertyRecord
from app.services.ingestion.pipeline import (
    IngestionPipeline,
    generate_property_id,
)
from app.services.quality import calculate_quality_score

logger = structlog.get_logger()

router = APIRouter(prefix="/v1/ingest", tags=["Ingest"])


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------


class ParcelRecord(BaseModel):
    """Single parcel record for ingestion."""

    parcel_id: str = Field(..., description="Assessor Parcel Number (APN)")
    address: str = Field(..., description="Full street address")
    state_fips: str = Field(..., description="2-digit state FIPS code, e.g. '06'")
    county_fips: str = Field(
        ..., description="3-digit county FIPS code, e.g. '037'"
    )
    county_name: str = Field(..., description="County name, e.g. 'Los Angeles'")
    county_apn: str | None = Field(
        None,
        description="County APN (defaults to parcel_id if omitted)",
    )
    latitude: float | None = None
    longitude: float | None = None
    property_type: str | None = None
    lot_sqft: int | None = None
    lot_acres: float | None = None
    legal_description: str | None = None
    extra: dict[str, Any] = Field(
        default_factory=dict,
        description="Any extra fields stored as raw_data",
    )


class IngestRequest(BaseModel):
    """Request body for JSON bulk ingestion."""

    records: list[ParcelRecord] = Field(
        ..., min_length=1, description="Parcel records to ingest"
    )
    source: str = Field(
        "direct", description="Source system identifier"
    )


class IngestResultItem(BaseModel):
    """Result for one ingested parcel."""

    parcel_id: str
    property_id: str
    action: str  # "created", "updated", "matched"
    quality_score: float
    canonical_id: str | None = None


class IngestResponse(BaseModel):
    """Summary of a bulk ingest operation."""

    ingested: int
    created: int
    updated: int
    matched: int
    errors: int
    quality_avg: float
    items: list[IngestResultItem]
    data_quality: dict[str, Any]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _naive_utcnow() -> datetime:
    """Return current UTC time as a naive datetime (no tz info) for DB compat."""
    return datetime.utcnow()  # noqa: DTZ003


def _parcel_to_raw(rec: ParcelRecord, source: str) -> RawPropertyRecord:
    raw_data: dict[str, Any] = {
        "address": rec.address,
        "parcel_id": rec.parcel_id,
        "state_fips": rec.state_fips,
        "county_fips": rec.county_fips,
        "county_name": rec.county_name,
        "county_apn": rec.county_apn or rec.parcel_id,
        "lat": rec.latitude,
        "lng": rec.longitude,
        "property_type": rec.property_type,
        "lot_sqft": rec.lot_sqft,
        "lot_acres": rec.lot_acres,
        **rec.extra,
    }
    return RawPropertyRecord(
        source_system=source,
        source_type="direct",
        source_record_id=rec.parcel_id,
        extraction_timestamp=_naive_utcnow(),
        raw_data=raw_data,
        parcel_id=rec.parcel_id,
        address_raw=rec.address,
        latitude=rec.latitude,
        longitude=rec.longitude,
    )


async def _upsert_property(
    db: AsyncSession,
    rec: ParcelRecord,
    processed: Any,
    source: str,
) -> tuple[Property, str]:
    """Upsert a processed record into the database.

    Returns:
        (Property instance, action string)
    """
    stmt = select(Property).where(Property.id == processed.property_id)
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()

    apn = rec.county_apn or rec.parcel_id

    raw_hash = hashlib.sha256(
        json.dumps(
            {"parcel_id": rec.parcel_id, "address": rec.address},
            sort_keys=True,
        ).encode()
    ).hexdigest()

    q = processed.quality

    if existing is None:
        prop = Property(
            id=processed.property_id,
            state_fips=rec.state_fips,
            county_fips=rec.county_fips,
            county_name=rec.county_name,
            county_apn=apn,
            property_type=rec.property_type,
            lot_sqft=rec.lot_sqft,
            lot_acres=rec.lot_acres,
            legal_description=rec.legal_description,
            canonical_id=processed.canonical_id,
            entity_confidence=processed.entity_confidence,
            # DataQualityMixin
            quality_score=q.score,
            quality_completeness=q.completeness,
            quality_accuracy=q.accuracy,
            quality_consistency=q.consistency,
            quality_timeliness=q.timeliness,
            quality_validity=q.validity,
            quality_uniqueness=q.uniqueness,
            freshness_hours=0,
            # ProvenanceMixin
            source_system=source,
            source_type="direct",
            source_record_id=rec.parcel_id,
            extraction_timestamp=processed.extraction_timestamp,
            raw_data_hash=raw_hash,
        )
        db.add(prop)
        action = "created"
    else:
        existing.quality_score = q.score
        existing.canonical_id = processed.canonical_id
        existing.entity_confidence = processed.entity_confidence
        action = (
            "matched"
            if processed.canonical_id and processed.canonical_id != processed.property_id
            else "updated"
        )
        prop = existing

    # Upsert address if we have one
    if processed.address:
        addr_stmt = select(Address).where(
            Address.property_id == processed.property_id
        )
        addr_result = await db.execute(addr_stmt)
        existing_addr = addr_result.scalar_one_or_none()

        a = processed.address
        if existing_addr is None:
            addr = Address(
                property_id=processed.property_id,
                raw_address=rec.address,
                street_number=a.street_number,
                street_name=a.street_name,
                street_suffix=a.street_suffix,
                street_direction=a.street_direction,
                unit_type=a.unit_type,
                unit_number=a.unit_number,
                city=a.city,
                state=a.state,
                zip_code=a.zip_code,
                zip4=a.zip4,
                county=rec.county_name,
                street_address=a.street_address,
                formatted_address=a.formatted_address,
                latitude=processed.latitude,
                longitude=processed.longitude,
                geocode_accuracy=None,
                geocode_source=None,
            )
            db.add(addr)

    return prop, action


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.post("", response_model=IngestResponse, status_code=200)
async def ingest_json(
    body: IngestRequest,
    db: AsyncSession = Depends(get_db),
) -> IngestResponse:
    """Ingest parcel records from a JSON payload.

    Runs each record through the normalize → entity-resolve → quality pipeline
    and upserts into the parcel database.
    """
    return await _run_ingest(body.records, body.source, db)


@router.post("/csv", response_model=IngestResponse, status_code=200)
async def ingest_csv(
    file: UploadFile = FastAPIFile(..., description="CSV file of parcel records"),
    source: str = "csv-upload",
    db: AsyncSession = Depends(get_db),
) -> IngestResponse:
    """Ingest parcel records from a CSV file upload.

    Required columns: parcel_id, address, state_fips, county_fips, county_name
    Optional columns: latitude, longitude, property_type, lot_sqft, lot_acres
    """
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a .csv")

    content = await file.read()
    text = content.decode("utf-8-sig")  # handle BOM
    reader = DictReader(io.StringIO(text))

    records: list[ParcelRecord] = []
    for row in reader:
        try:
            rec = ParcelRecord(
                parcel_id=row["parcel_id"],
                address=row["address"],
                state_fips=row["state_fips"],
                county_fips=row["county_fips"],
                county_name=row["county_name"],
                county_apn=row.get("county_apn"),
                latitude=float(row["latitude"]) if row.get("latitude") else None,
                longitude=float(row["longitude"]) if row.get("longitude") else None,
                property_type=row.get("property_type"),
                lot_sqft=int(row["lot_sqft"]) if row.get("lot_sqft") else None,
                lot_acres=float(row["lot_acres"]) if row.get("lot_acres") else None,
                legal_description=row.get("legal_description"),
                extra={
                    k: v
                    for k, v in row.items()
                    if k
                    not in {
                        "parcel_id", "address", "state_fips", "county_fips",
                        "county_name", "county_apn", "latitude", "longitude",
                        "property_type", "lot_sqft", "lot_acres",
                        "legal_description",
                    }
                },
            )
            records.append(rec)
        except (KeyError, ValueError) as e:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid CSV row: {e}. Row: {dict(row)}",
            ) from e

    return await _run_ingest(records, source, db)


async def _run_ingest(
    records: list[ParcelRecord],
    source: str,
    db: AsyncSession,
) -> IngestResponse:
    pipeline = IngestionPipeline()
    items: list[IngestResultItem] = []
    errors = 0
    action_counts: dict[str, int] = {"created": 0, "updated": 0, "matched": 0}

    for rec in records:
        raw = _parcel_to_raw(rec, source)
        try:
            processed = await pipeline.process_record(raw)
            if processed is None:
                errors += 1
                continue

            prop, action = await _upsert_property(db, rec, processed, source)
            action_counts[action] = action_counts.get(action, 0) + 1

            items.append(
                IngestResultItem(
                    parcel_id=rec.parcel_id,
                    property_id=processed.property_id,
                    action=action,
                    quality_score=round(processed.quality.score, 4),
                    canonical_id=processed.canonical_id,
                )
            )
            logger.info(
                "Ingested parcel",
                parcel_id=rec.parcel_id,
                property_id=processed.property_id,
                action=action,
            )
        except Exception as exc:
            logger.error(
                "Ingest error",
                parcel_id=rec.parcel_id,
                error=str(exc),
            )
            errors += 1

    await db.commit()

    quality_scores = [i.quality_score for i in items]
    quality_avg = (
        round(sum(quality_scores) / len(quality_scores), 4)
        if quality_scores
        else 0.0
    )

    return IngestResponse(
        ingested=len(items),
        created=action_counts.get("created", 0),
        updated=action_counts.get("updated", 0),
        matched=action_counts.get("matched", 0),
        errors=errors,
        quality_avg=quality_avg,
        items=items,
        data_quality={
            "score": quality_avg,
            "confidence": (
                "high" if quality_avg >= 0.85
                else "medium" if quality_avg >= 0.70
                else "low"
            ),
            "sources": [source],
        },
    )
