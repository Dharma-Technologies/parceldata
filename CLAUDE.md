# CLAUDE.md — ParcelData Build

## Project
You are building **ParcelData** — an open source real estate data platform for AI agents.
The platform provides clean, normalized property data via REST API, GraphQL, and MCP server.

## Working Directory
`/home/numen/dharma/parceldata/`

## Project Structure
```
parceldata/
├── api/                    # FastAPI Python app
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── models/         # SQLAlchemy + Pydantic models
│   │   ├── routes/         # API route handlers
│   │   ├── services/       # Business logic
│   │   └── database/       # DB connections, queries
│   ├── tests/
│   ├── requirements.txt
│   ├── Dockerfile
│   └── alembic/            # Database migrations
├── mcp/                    # TypeScript MCP server
│   ├── src/
│   ├── package.json
│   ├── tsconfig.json
│   └── Dockerfile
├── sdk/                    # Python SDK (pip install parceldata)
│   ├── parceldata/
│   └── setup.py
├── site/                   # Landing page
├── docs/                   # Documentation
├── scripts/                # Utility scripts
├── docker-compose.yml      # Local dev
├── .github/workflows/      # CI/CD
├── LICENSE                 # MIT
└── README.md
```

## Tech Stack

### Python API
- **Framework:** FastAPI (Python 3.12)
- **ORM:** SQLAlchemy 2.0 (async)
- **Migrations:** Alembic
- **Database:** PostgreSQL 16 + PostGIS + pgvector
- **Cache:** Redis
- **Testing:** pytest, pytest-asyncio
- **Linting:** ruff
- **Type checking:** mypy (strict)

### MCP Server
- **Runtime:** Node.js 20+
- **Framework:** @modelcontextprotocol/sdk
- **Language:** TypeScript (strict mode)
- **Testing:** vitest
- **Linting:** eslint + prettier

### Database
- **Primary:** PostgreSQL 16
- **Extensions:** PostGIS (spatial), pgvector (embeddings), pg_trgm (fuzzy search)
- **Schemas:** `parcel` (main), `analytics` (derived), `audit` (logs)

## API Design Principles

### REST API
- **Base URL:** `/v1/` prefix for all endpoints
- **Versioning:** Path-based (`/v1/`, `/v2/`)
- **Auth:** API key via `Authorization: Bearer <key>` or `X-API-Key: <key>`
- **Pagination:** Cursor-based for lists (`?cursor=abc&limit=25`)
- **Rate limiting:** Per-key limits via Redis

### Endpoints
```
GET  /v1/properties/{parcel_id}
GET  /v1/properties/address?street=...&city=...&state=...
GET  /v1/properties/coordinates?lat=...&lng=...
POST /v1/properties/search
GET  /v1/analytics/comparables?property_id=...
GET  /v1/analytics/market-trends?zip=...
POST /v1/webhooks
```

### Token-Optimized Response Tiers
- **Micro** (500-1000 tokens): ID, price, basic stats only
- **Standard** (2000-4000 tokens): Full property details
- **Extended** (8000-16000 tokens): Property + market context
- **Full** (32000+ tokens): Everything + documents

API parameter: `?detail=micro|standard|extended|full`

### Data Quality Score (REQUIRED in every response)
```json
{
  "data_quality": {
    "score": 0.87,
    "components": {
      "completeness": 0.92,
      "accuracy": 0.95,
      "consistency": 0.88,
      "timeliness": 0.80,
      "validity": 0.99,
      "uniqueness": 0.98
    },
    "freshness_hours": 12,
    "sources": ["travis_cad", "actris_mls"],
    "confidence": "high"
  }
}
```

**Formula:**
```
score = (completeness × 0.25) + (accuracy × 0.25) + 
        (consistency × 0.20) + (timeliness × 0.15) + 
        (validity × 0.10) + (uniqueness × 0.05)
```

## Entity Resolution Pipeline
Cross-source property deduplication is critical. The pipeline:
1. **Blocking** — Geohash-based (within 100m), address normalization, parcel ID match
2. **Pairwise Comparison** — Jaro-Winkler (>0.85), geolocation (<10m), characteristics
3. **Classification** — Rule-based for exact, ML for fuzzy, human queue for uncertain
4. **Clustering** — Transitive closure, canonical record selection, persistent entity ID

**Confidence thresholds:**
- ≥0.99: Auto-merge (exact match)
- ≥0.90: Auto-merge (normalized address + geocode <10m)
- ≥0.85: Auto-merge with flag
- ≥0.70: Human review queue
- <0.50: Keep separate

## MCP Tools
```json
{
  "name": "parceldata",
  "tools": [
    "property_lookup",
    "property_search",
    "get_comparables",
    "get_market_trends",
    "check_zoning",
    "get_permits",
    "get_owner_portfolio",
    "estimate_value",
    "check_development_feasibility"
  ]
}
```

## Agent-Readable Endpoints
- `/llms.txt` — Plain text summary for LLM crawlers
- `/.well-known/ai-plugin.json` — OpenAI plugin manifest
- `/openapi.json` — Full OpenAPI spec
- JSON-LD structured data in HTML pages

## Open Source
- **License:** MIT
- **Code is open:** SDKs, API, adapters, normalization layer
- **Data is the business:** Hosted service monetizes licensed data + operations

## Coding Standards

### Python
```python
# Imports: standard lib, third-party, local (separated by blank lines)
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.property import Property

# Type annotations: REQUIRED on all functions
async def get_property(
    property_id: str,
    db: AsyncSession = Depends(get_db),
) -> Property:
    ...

# Docstrings: Google style
def calculate_quality_score(
    completeness: float,
    accuracy: float,
    consistency: float,
    timeliness: float,
    validity: float,
    uniqueness: float,
) -> float:
    """Calculate weighted data quality score.
    
    Args:
        completeness: Fraction of required fields present (0-1)
        accuracy: Confidence in data correctness (0-1)
        consistency: Internal consistency score (0-1)
        timeliness: Freshness score based on last update (0-1)
        validity: Schema/format validity score (0-1)
        uniqueness: Deduplication confidence (0-1)
        
    Returns:
        Weighted quality score (0-1)
    """
    return (
        completeness * 0.25 +
        accuracy * 0.25 +
        consistency * 0.20 +
        timeliness * 0.15 +
        validity * 0.10 +
        uniqueness * 0.05
    )
```

### TypeScript
```typescript
// Strict mode, no any
interface PropertyLookupParams {
  address?: string;
  parcelId?: string;
  lat?: number;
  lng?: number;
  include?: string[];
}

async function propertyLookup(params: PropertyLookupParams): Promise<Property> {
  // ...
}
```

## File Naming
- Python: `snake_case.py` (e.g., `property_service.py`)
- TypeScript: `kebab-case.ts` (e.g., `property-lookup.ts`)
- Models: Singular (`Property`, not `Properties`)
- Routes: Plural (`/properties`, not `/property`)

## Git
```bash
cd /home/numen/dharma/parceldata
git add -A
git commit -m "feat: <description>"
git push origin main
```

## Build & Test

### Python
```bash
cd /home/numen/dharma/parceldata/api
pip install -r requirements.txt
ruff check .
mypy app/
pytest tests/ -v
```

### TypeScript
```bash
cd /home/numen/dharma/parceldata/mcp
npm install
npm run lint
npm run typecheck
npm test
```

### Docker
```bash
cd /home/numen/dharma/parceldata
docker-compose build
docker-compose up -d
```

## CRITICAL RULES
1. Every story must result in working, testable code
2. Run linters (ruff, eslint) after EVERY story
3. Run type checkers (mypy, tsc) after EVERY story
4. All API responses MUST include `data_quality` object
5. All endpoints MUST be documented with OpenAPI annotations
6. All database models MUST have proper indexes
7. Commit after each completed story
8. Use environment variables for ALL configuration (no hardcoded values)
9. MIT license — code is open source

## Current Stage: P10-02-data-models

# PRD: P10-02 — Data Models

## Overview
Define all SQLAlchemy models for the ParcelData database schema, including Property, Address, Building, Valuation, Ownership, Zoning, Listing, Transaction, Permit, Environmental, School, and supporting models. Includes PostGIS spatial columns and pgvector embeddings.

---

## Stories

### S1: Base Model and Mixins
Create `api/app/models/base.py` with common model mixins.

```python
# api/app/models/base.py
from datetime import datetime
from sqlalchemy import DateTime, String, Float
from sqlalchemy.orm import Mapped, mapped_column
from app.database.connection import Base

class TimestampMixin:
    """Adds created_at and updated_at columns."""
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class DataQualityMixin:
    """Adds data quality score columns."""
    quality_score: Mapped[float] = mapped_column(Float, default=0.0)
    quality_completeness: Mapped[float] = mapped_column(Float, default=0.0)
    quality_accuracy: Mapped[float] = mapped_column(Float, default=0.0)
    quality_consistency: Mapped[float] = mapped_column(Float, default=0.0)
    quality_timeliness: Mapped[float] = mapped_column(Float, default=0.0)
    quality_validity: Mapped[float] = mapped_column(Float, default=0.0)
    quality_uniqueness: Mapped[float] = mapped_column(Float, default=0.0)
    freshness_hours: Mapped[int] = mapped_column(default=0)

class ProvenanceMixin:
    """Adds source tracking columns."""
    source_system: Mapped[str | None] = mapped_column(String(100), nullable=True)
    source_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    source_record_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    extraction_timestamp: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    raw_data_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    transformation_version: Mapped[str | None] = mapped_column(String(20), nullable=True)
```

### S2: Property Model
Create `api/app/models/property.py` — the core property entity.

```python
# api/app/models/property.py
from sqlalchemy import String, Integer, Float, Boolean, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from geoalchemy2 import Geometry
from pgvector.sqlalchemy import Vector
from app.models.base import Base, TimestampMixin, DataQualityMixin, ProvenanceMixin

class Property(Base, TimestampMixin, DataQualityMixin, ProvenanceMixin):
    __tablename__ = "properties"
    __table_args__ = {"schema": "parcel"}
    
    # Primary key - Dharma Parcel ID format: {STATE}-{COUNTY}-{APN_HASH}
    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    
    # County parcel info
    state_fips: Mapped[str] = mapped_column(String(2), index=True)
    county_fips: Mapped[str] = mapped_column(String(3), index=True)
    county_name: Mapped[str] = mapped_column(String(100))
    county_apn: Mapped[str] = mapped_column(String(50), index=True)
    
    # Legal description
    legal_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    subdivision_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    lot_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    block_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    
    # Lot dimensions
    lot_sqft: Mapped[int | None] = mapped_column(Integer, nullable=True)
    lot_acres: Mapped[float | None] = mapped_column(Float, nullable=True)
    lot_depth_ft: Mapped[float | None] = mapped_column(Float, nullable=True)
    lot_width_ft: Mapped[float | None] = mapped_column(Float, nullable=True)
    lot_dimensions: Mapped[str | None] = mapped_column(String(50), nullable=True)
    
    # Property type
    property_type: Mapped[str | None] = mapped_column(String(50), index=True)
    property_use: Mapped[str | None] = mapped_column(String(100))
    
    # Spatial
    location: Mapped[Geometry] = mapped_column(Geometry("POINT", srid=4326), nullable=True)
    boundary: Mapped[Geometry] = mapped_column(Geometry("POLYGON", srid=4326), nullable=True)
    
    # Census geography
    census_tract: Mapped[str | None] = mapped_column(String(20), index=True)
    census_block_group: Mapped[str | None] = mapped_column(String(20))
    
    # Embedding for semantic search
    embedding: Mapped[Vector] = mapped_column(Vector(1536), nullable=True)
    
    # Entity resolution
    canonical_id: Mapped[str | None] = mapped_column(String(50), index=True)
    entity_confidence: Mapped[float] = mapped_column(Float, default=1.0)
    
    # Relationships
    address = relationship("Address", back_populates="property", uselist=False)
    buildings = relationship("Building", back_populates="property")
    valuation = relationship("Valuation", back_populates="property", uselist=False)
    ownership = relationship("Ownership", back_populates="property", uselist=False)
    zoning = relationship("Zoning", back_populates="property", uselist=False)
    listing = relationship("Listing", back_populates="property", uselist=False)
    transactions = relationship("Transaction", back_populates="property")
    permits = relationship("Permit", back_populates="property")
    environmental = relationship("Environmental", back_populates="property", uselist=False)
    school = relationship("School", back_populates="property", uselist=False)
    hoa = relationship("HOA", back_populates="property", uselist=False)
    tax = relationship("Tax", back_populates="property", uselist=False)

# Indexes
Index("ix_properties_location", Property.location, postgresql_using="gist")
Index("ix_properties_state_county", Property.state_fips, Property.county_fips)
Index("ix_properties_property_type", Property.property_type)
```

### S3: Address Model
Create `api/app/models/address.py` for normalized addresses.

```python
# api/app/models/address.py
from sqlalchemy import String, Float, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin

class Address(Base, TimestampMixin):
    __tablename__ = "addresses"
    __table_args__ = {"schema": "parcel"}
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    property_id: Mapped[str] = mapped_column(String(50), ForeignKey("parcel.properties.id"), unique=True)
    
    # Raw input
    raw_address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    
    # Normalized components
    street_number: Mapped[str | None] = mapped_column(String(20))
    street_name: Mapped[str | None] = mapped_column(String(200))
    street_suffix: Mapped[str | None] = mapped_column(String(20))  # St, Ave, Blvd
    street_direction: Mapped[str | None] = mapped_column(String(10))  # N, S, E, W
    unit_type: Mapped[str | None] = mapped_column(String(20))  # Apt, Suite, Unit
    unit_number: Mapped[str | None] = mapped_column(String(20))
    city: Mapped[str | None] = mapped_column(String(100), index=True)
    state: Mapped[str | None] = mapped_column(String(2), index=True)
    zip_code: Mapped[str | None] = mapped_column(String(5), index=True)
    zip4: Mapped[str | None] = mapped_column(String(4))
    county: Mapped[str | None] = mapped_column(String(100))
    
    # Formatted versions
    street_address: Mapped[str | None] = mapped_column(String(300))  # Full street line
    formatted_address: Mapped[str | None] = mapped_column(String(500))  # Full address
    
    # Geocoding
    latitude: Mapped[float | None] = mapped_column(Float, index=True)
    longitude: Mapped[float | None] = mapped_column(Float, index=True)
    geocode_accuracy: Mapped[str | None] = mapped_column(String(20))  # rooftop, parcel, street
    geocode_source: Mapped[str | None] = mapped_column(String(50))
    
    # Normalization
    usps_validated: Mapped[bool] = mapped_column(default=False)
    normalization_score: Mapped[float] = mapped_column(Float, default=0.0)
    
    property = relationship("Property", back_populates="address")

Index("ix_addresses_city_state", Address.city, Address.state)
Index("ix_addresses_zip", Address.zip_code)
Index("ix_addresses_lat_lng", Address.latitude, Address.longitude)
```

### S4: Building Model
Create `api/app/models/building.py` for structures on a property.

```python
# api/app/models/building.py
from sqlalchemy import String, Integer, Float, Boolean, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin

class Building(Base, TimestampMixin):
    __tablename__ = "buildings"
    __table_args__ = {"schema": "parcel"}
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    property_id: Mapped[str] = mapped_column(String(50), ForeignKey("parcel.properties.id"), index=True)
    building_number: Mapped[int] = mapped_column(Integer, default=1)  # For multi-building parcels
    
    # Size
    sqft: Mapped[int | None] = mapped_column(Integer)
    sqft_finished: Mapped[int | None] = mapped_column(Integer)
    sqft_unfinished: Mapped[int | None] = mapped_column(Integer)
    
    # Structure
    stories: Mapped[int | None] = mapped_column(Integer)
    bedrooms: Mapped[int | None] = mapped_column(Integer, index=True)
    bathrooms: Mapped[float | None] = mapped_column(Float)  # 2.5 for 2 full + 1 half
    bathrooms_full: Mapped[int | None] = mapped_column(Integer)
    bathrooms_half: Mapped[int | None] = mapped_column(Integer)
    
    # Age
    year_built: Mapped[int | None] = mapped_column(Integer, index=True)
    year_renovated: Mapped[int | None] = mapped_column(Integer)
    effective_year_built: Mapped[int | None] = mapped_column(Integer)
    
    # Construction
    construction_type: Mapped[str | None] = mapped_column(String(50))  # frame, masonry, steel
    exterior_wall: Mapped[str | None] = mapped_column(String(50))
    roof_type: Mapped[str | None] = mapped_column(String(50))
    roof_material: Mapped[str | None] = mapped_column(String(50))
    foundation_type: Mapped[str | None] = mapped_column(String(50))
    heating_type: Mapped[str | None] = mapped_column(String(50))
    cooling_type: Mapped[str | None] = mapped_column(String(50))
    
    # Features
    garage_type: Mapped[str | None] = mapped_column(String(50))  # attached, detached, none
    garage_spaces: Mapped[int | None] = mapped_column(Integer)
    parking_spaces: Mapped[int | None] = mapped_column(Integer)
    pool: Mapped[bool] = mapped_column(Boolean, default=False)
    pool_type: Mapped[str | None] = mapped_column(String(50))
    fireplace: Mapped[bool] = mapped_column(Boolean, default=False)
    fireplace_count: Mapped[int | None] = mapped_column(Integer)
    basement: Mapped[bool] = mapped_column(Boolean, default=False)
    basement_type: Mapped[str | None] = mapped_column(String(50))  # full, partial, crawl
    attic: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Quality
    quality_grade: Mapped[str | None] = mapped_column(String(20))  # A+, A, B+, B, C+, C, D
    condition: Mapped[str | None] = mapped_column(String(20))  # excellent, good, fair, poor
    
    property = relationship("Property", back_populates="buildings")

Index("ix_buildings_property_id", Building.property_id)
Index("ix_buildings_beds_baths", Building.bedrooms, Building.bathrooms)
```

### S5: Valuation Model
Create `api/app/models/valuation.py` for property values.

```python
# api/app/models/valuation.py
from datetime import date
from sqlalchemy import String, Integer, Float, Date, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin

class Valuation(Base, TimestampMixin):
    __tablename__ = "valuations"
    __table_args__ = {"schema": "parcel"}
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    property_id: Mapped[str] = mapped_column(String(50), ForeignKey("parcel.properties.id"), unique=True)
    
    # Assessed values (from county assessor)
    assessed_total: Mapped[int | None] = mapped_column(Integer)
    assessed_land: Mapped[int | None] = mapped_column(Integer)
    assessed_improvements: Mapped[int | None] = mapped_column(Integer)
    assessed_year: Mapped[int | None] = mapped_column(Integer)
    assessment_date: Mapped[date | None] = mapped_column(Date)
    
    # Market values (computed AVM)
    estimated_value: Mapped[int | None] = mapped_column(Integer, index=True)
    estimated_value_low: Mapped[int | None] = mapped_column(Integer)
    estimated_value_high: Mapped[int | None] = mapped_column(Integer)
    estimate_confidence: Mapped[float | None] = mapped_column(Float)  # 0-1
    estimate_date: Mapped[date | None] = mapped_column(Date)
    estimate_model: Mapped[str | None] = mapped_column(String(50))  # Model version
    
    # Per-unit metrics
    price_per_sqft: Mapped[float | None] = mapped_column(Float)
    price_per_acre: Mapped[float | None] = mapped_column(Float)
    
    # Historical
    value_change_1yr: Mapped[float | None] = mapped_column(Float)  # % change
    value_change_5yr: Mapped[float | None] = mapped_column(Float)
    
    property = relationship("Property", back_populates="valuation")
```

### S6: Ownership Model
Create `api/app/models/ownership.py` for owner information.

```python
# api/app/models/ownership.py
from datetime import date
from sqlalchemy import String, Integer, Float, Date, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin

class Ownership(Base, TimestampMixin):
    __tablename__ = "ownerships"
    __table_args__ = {"schema": "parcel"}
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    property_id: Mapped[str] = mapped_column(String(50), ForeignKey("parcel.properties.id"), unique=True)
    
    # Current owner
    owner_name: Mapped[str | None] = mapped_column(String(200), index=True)
    owner_name_2: Mapped[str | None] = mapped_column(String(200))  # Co-owner
    owner_type: Mapped[str | None] = mapped_column(String(50))  # individual, corporation, trust, llc, government
    
    # Entity resolution
    owner_entity_id: Mapped[str | None] = mapped_column(String(50), index=True)  # Resolved entity ID
    
    # Mailing address (may differ from property)
    mailing_street: Mapped[str | None] = mapped_column(String(200))
    mailing_city: Mapped[str | None] = mapped_column(String(100))
    mailing_state: Mapped[str | None] = mapped_column(String(2))
    mailing_zip: Mapped[str | None] = mapped_column(String(10))
    
    # Occupancy
    owner_occupied: Mapped[bool | None] = mapped_column(Boolean)
    
    # Acquisition
    acquisition_date: Mapped[date | None] = mapped_column(Date, index=True)
    acquisition_price: Mapped[int | None] = mapped_column(Integer)
    acquisition_type: Mapped[str | None] = mapped_column(String(50))  # sale, inheritance, gift, foreclosure
    
    # Duration
    ownership_length_years: Mapped[float | None] = mapped_column(Float)
    
    property = relationship("Property", back_populates="ownership")
```

### S7: Zoning Model
Create `api/app/models/zoning.py` for zoning restrictions.

```python
# api/app/models/zoning.py
from sqlalchemy import String, Float, Boolean, ForeignKey, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB
from app.models.base import Base, TimestampMixin

class Zoning(Base, TimestampMixin):
    __tablename__ = "zonings"
    __table_args__ = {"schema": "parcel"}
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    property_id: Mapped[str] = mapped_column(String(50), ForeignKey("parcel.properties.id"), unique=True)
    
    # Zone classification
    zone_code: Mapped[str | None] = mapped_column(String(20), index=True)
    zone_description: Mapped[str | None] = mapped_column(String(200))
    zone_category: Mapped[str | None] = mapped_column(String(50))  # residential, commercial, industrial, mixed
    
    # Overlay districts
    overlay_districts: Mapped[list] = mapped_column(ARRAY(String), default=[])
    historic_district: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Permitted uses
    permitted_uses: Mapped[list] = mapped_column(ARRAY(String), default=[])
    conditional_uses: Mapped[list] = mapped_column(ARRAY(String), default=[])
    prohibited_uses: Mapped[list] = mapped_column(ARRAY(String), default=[])
    
    # Dimensional requirements
    setback_front_ft: Mapped[float | None] = mapped_column(Float)
    setback_rear_ft: Mapped[float | None] = mapped_column(Float)
    setback_side_ft: Mapped[float | None] = mapped_column(Float)
    max_height_ft: Mapped[float | None] = mapped_column(Float)
    max_stories: Mapped[int | None] = mapped_column()
    max_far: Mapped[float | None] = mapped_column(Float)  # Floor Area Ratio
    max_lot_coverage: Mapped[float | None] = mapped_column(Float)  # % impervious
    min_lot_size_sqft: Mapped[int | None] = mapped_column()
    min_lot_width_ft: Mapped[float | None] = mapped_column(Float)
    
    # Density
    max_units_per_acre: Mapped[float | None] = mapped_column(Float)
    
    # Parking requirements
    parking_spaces_required: Mapped[int | None] = mapped_column()
    
    # ADU rules
    adu_permitted: Mapped[bool | None] = mapped_column(Boolean)
    adu_rules: Mapped[dict] = mapped_column(JSONB, default={})
    
    # Source
    jurisdiction: Mapped[str | None] = mapped_column(String(100))
    ordinance_reference: Mapped[str | None] = mapped_column(String(200))
    
    property = relationship("Property", back_populates="zoning")
```

### S8: Listing Model
Create `api/app/models/listing.py` for MLS listings.

```python
# api/app/models/listing.py
from datetime import date, datetime
from sqlalchemy import String, Integer, Float, Date, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin

class Listing(Base, TimestampMixin):
    __tablename__ = "listings"
    __table_args__ = {"schema": "parcel"}
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    property_id: Mapped[str] = mapped_column(String(50), ForeignKey("parcel.properties.id"), index=True)
    mls_number: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    mls_source: Mapped[str | None] = mapped_column(String(50))  # Which MLS system
    
    # Status
    status: Mapped[str] = mapped_column(String(20), index=True)  # active, pending, sold, expired, withdrawn
    
    # Dates
    list_date: Mapped[date | None] = mapped_column(Date, index=True)
    pending_date: Mapped[date | None] = mapped_column(Date)
    sold_date: Mapped[date | None] = mapped_column(Date, index=True)
    expiration_date: Mapped[date | None] = mapped_column(Date)
    days_on_market: Mapped[int | None] = mapped_column(Integer)
    cumulative_dom: Mapped[int | None] = mapped_column(Integer)
    
    # Pricing
    list_price: Mapped[int | None] = mapped_column(Integer, index=True)
    original_list_price: Mapped[int | None] = mapped_column(Integer)
    sold_price: Mapped[int | None] = mapped_column(Integer)
    price_per_sqft: Mapped[float | None] = mapped_column(Float)
    
    # Description
    public_remarks: Mapped[str | None] = mapped_column(Text)
    private_remarks: Mapped[str | None] = mapped_column(Text)
    
    # Features
    features: Mapped[list] = mapped_column(ARRAY(String), default=[])
    appliances: Mapped[list] = mapped_column(ARRAY(String), default=[])
    
    # Photos
    photo_count: Mapped[int] = mapped_column(Integer, default=0)
    photo_urls: Mapped[list] = mapped_column(ARRAY(String), default=[])
    virtual_tour_url: Mapped[str | None] = mapped_column(String(500))
    
    # Showing
    showing_instructions: Mapped[str | None] = mapped_column(Text)
    lockbox_type: Mapped[str | None] = mapped_column(String(50))
    
    # Agent
    listing_agent_name: Mapped[str | None] = mapped_column(String(100))
    listing_agent_phone: Mapped[str | None] = mapped_column(String(20))
    listing_agent_email: Mapped[str | None] = mapped_column(String(100))
    listing_agent_license: Mapped[str | None] = mapped_column(String(50))
    listing_office_name: Mapped[str | None] = mapped_column(String(100))
    listing_office_phone: Mapped[str | None] = mapped_column(String(20))
    
    # Buyer agent (if sold)
    buyer_agent_name: Mapped[str | None] = mapped_column(String(100))
    buyer_office_name: Mapped[str | None] = mapped_column(String(100))
    
    property = relationship("Property", back_populates="listing")
```

### S9: Transaction Model
Create `api/app/models/transaction.py` for deed transfers and sales.

```python
# api/app/models/transaction.py
from datetime import date
from sqlalchemy import String, Integer, Float, Date, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, ProvenanceMixin

class Transaction(Base, TimestampMixin, ProvenanceMixin):
    __tablename__ = "transactions"
    __table_args__ = {"schema": "parcel"}
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    property_id: Mapped[str] = mapped_column(String(50), ForeignKey("parcel.properties.id"), index=True)
    
    # Recording
    document_number: Mapped[str | None] = mapped_column(String(50), index=True)
    recording_date: Mapped[date | None] = mapped_column(Date, index=True)
    book: Mapped[str | None] = mapped_column(String(20))
    page: Mapped[str | None] = mapped_column(String(20))
    
    # Transaction details
    transaction_date: Mapped[date | None] = mapped_column(Date)
    deed_type: Mapped[str | None] = mapped_column(String(50))  # warranty, quitclaim, grant, trustee
    transaction_type: Mapped[str | None] = mapped_column(String(50))  # sale, refinance, transfer
    
    # Parties
    grantor: Mapped[str | None] = mapped_column(String(200))
    grantee: Mapped[str | None] = mapped_column(String(200))
    
    # Financial
    sale_price: Mapped[int | None] = mapped_column(Integer)
    price_per_sqft: Mapped[float | None] = mapped_column(Float)
    loan_amount: Mapped[int | None] = mapped_column(Integer)
    lender_name: Mapped[str | None] = mapped_column(String(200))
    
    # Flags
    arms_length: Mapped[bool | None] = mapped_column()  # True if fair market sale
    distressed: Mapped[bool | None] = mapped_column()  # Foreclosure, short sale
    
    property = relationship("Property", back_populates="transactions")
```

### S10: Permit Model
Create `api/app/models/permit.py` for building permits.

```python
# api/app/models/permit.py
from datetime import date
from sqlalchemy import String, Integer, Float, Date, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, ProvenanceMixin

class Permit(Base, TimestampMixin, ProvenanceMixin):
    __tablename__ = "permits"
    __table_args__ = {"schema": "parcel"}
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    property_id: Mapped[str] = mapped_column(String(50), ForeignKey("parcel.properties.id"), index=True)
    
    # Permit info
    permit_number: Mapped[str] = mapped_column(String(50), index=True)
    permit_type: Mapped[str | None] = mapped_column(String(50), index=True)  # building, electrical, plumbing, mechanical
    permit_subtype: Mapped[str | None] = mapped_column(String(100))
    
    # Status
    status: Mapped[str | None] = mapped_column(String(50), index=True)  # issued, in_review, approved, inspection, finaled, expired
    
    # Dates
    application_date: Mapped[date | None] = mapped_column(Date)
    issue_date: Mapped[date | None] = mapped_column(Date, index=True)
    expiration_date: Mapped[date | None] = mapped_column(Date)
    final_date: Mapped[date | None] = mapped_column(Date)
    
    # Description
    description: Mapped[str | None] = mapped_column(Text)
    work_class: Mapped[str | None] = mapped_column(String(50))  # new, addition, alteration, repair, demolition
    
    # Financial
    valuation: Mapped[int | None] = mapped_column(Integer)
    fee_paid: Mapped[float | None] = mapped_column(Float)
    
    # Contractor
    contractor_name: Mapped[str | None] = mapped_column(String(200))
    contractor_license: Mapped[str | None] = mapped_column(String(50))
    contractor_phone: Mapped[str | None] = mapped_column(String(20))
    
    # Inspection
    last_inspection_date: Mapped[date | None] = mapped_column(Date)
    last_inspection_result: Mapped[str | None] = mapped_column(String(50))
    inspections_passed: Mapped[int] = mapped_column(Integer, default=0)
    inspections_failed: Mapped[int] = mapped_column(Integer, default=0)
    
    # Jurisdiction
    jurisdiction: Mapped[str | None] = mapped_column(String(100))
    
    property = relationship("Property", back_populates="permits")
```

### S11: Environmental Model
Create `api/app/models/environmental.py` for hazards and risk.

```python
# api/app/models/environmental.py
from sqlalchemy import String, Float, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin

class Environmental(Base, TimestampMixin):
    __tablename__ = "environmentals"
    __table_args__ = {"schema": "parcel"}
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    property_id: Mapped[str] = mapped_column(String(50), ForeignKey("parcel.properties.id"), unique=True)
    
    # Flood
    flood_zone: Mapped[str | None] = mapped_column(String(10))  # A, AE, X, V, VE
    flood_zone_description: Mapped[str | None] = mapped_column(String(200))
    in_100yr_floodplain: Mapped[bool | None] = mapped_column(Boolean)
    in_500yr_floodplain: Mapped[bool | None] = mapped_column(Boolean)
    flood_insurance_required: Mapped[bool | None] = mapped_column(Boolean)
    flood_map_date: Mapped[str | None] = mapped_column(String(20))
    flood_panel_number: Mapped[str | None] = mapped_column(String(20))
    base_flood_elevation: Mapped[float | None] = mapped_column(Float)
    
    # Wildfire
    wildfire_risk: Mapped[str | None] = mapped_column(String(20))  # very_low, low, moderate, high, very_high
    wildfire_score: Mapped[float | None] = mapped_column(Float)  # 0-100
    in_wui: Mapped[bool | None] = mapped_column(Boolean)  # Wildland-Urban Interface
    
    # Earthquake
    earthquake_risk: Mapped[str | None] = mapped_column(String(20))
    earthquake_score: Mapped[float | None] = mapped_column(Float)
    near_fault_line: Mapped[bool | None] = mapped_column(Boolean)
    fault_distance_miles: Mapped[float | None] = mapped_column(Float)
    liquefaction_risk: Mapped[bool | None] = mapped_column(Boolean)
    
    # Environmental contamination
    superfund_site: Mapped[bool | None] = mapped_column(Boolean)
    superfund_distance_miles: Mapped[float | None] = mapped_column(Float)
    brownfield_site: Mapped[bool | None] = mapped_column(Boolean)
    underground_storage_tanks: Mapped[bool | None] = mapped_column(Boolean)
    
    # Other hazards
    radon_zone: Mapped[str | None] = mapped_column(String(10))
    tornado_risk: Mapped[str | None] = mapped_column(String(20))
    hurricane_risk: Mapped[str | None] = mapped_column(String(20))
    hail_risk: Mapped[str | None] = mapped_column(String(20))
    
    # Composite score
    overall_risk_score: Mapped[float | None] = mapped_column(Float)  # 0-100
    
    property = relationship("Property", back_populates="environmental")
```

### S12: School Model
Create `api/app/models/school.py` for school assignments.

```python
# api/app/models/school.py
from sqlalchemy import String, Integer, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin

class School(Base, TimestampMixin):
    __tablename__ = "schools"
    __table_args__ = {"schema": "parcel"}
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    property_id: Mapped[str] = mapped_column(String(50), ForeignKey("parcel.properties.id"), unique=True)
    
    # District
    district_name: Mapped[str | None] = mapped_column(String(100))
    district_id: Mapped[str | None] = mapped_column(String(20))
    district_rating: Mapped[int | None] = mapped_column(Integer)  # 1-10
    
    # Elementary
    elementary_name: Mapped[str | None] = mapped_column(String(100))
    elementary_id: Mapped[str | None] = mapped_column(String(20))
    elementary_rating: Mapped[int | None] = mapped_column(Integer)
    elementary_distance_miles: Mapped[float | None] = mapped_column(Float)
    
    # Middle
    middle_name: Mapped[str | None] = mapped_column(String(100))
    middle_id: Mapped[str | None] = mapped_column(String(20))
    middle_rating: Mapped[int | None] = mapped_column(Integer)
    middle_distance_miles: Mapped[float | None] = mapped_column(Float)
    
    # High
    high_name: Mapped[str | None] = mapped_column(String(100))
    high_id: Mapped[str | None] = mapped_column(String(20))
    high_rating: Mapped[int | None] = mapped_column(Integer)
    high_distance_miles: Mapped[float | None] = mapped_column(Float)
    
    property = relationship("Property", back_populates="school")
```

### S13: Tax and HOA Models
Create `api/app/models/tax.py` and `api/app/models/hoa.py`.

```python
# api/app/models/tax.py
from datetime import date
from sqlalchemy import String, Integer, Float, Date, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin

class Tax(Base, TimestampMixin):
    __tablename__ = "taxes"
    __table_args__ = {"schema": "parcel"}
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    property_id: Mapped[str] = mapped_column(String(50), ForeignKey("parcel.properties.id"), unique=True)
    
    # Annual tax
    annual_amount: Mapped[float | None] = mapped_column(Float)
    tax_year: Mapped[int | None] = mapped_column(Integer)
    tax_rate: Mapped[float | None] = mapped_column(Float)  # millage rate
    
    # Exemptions
    exemptions: Mapped[list] = mapped_column(ARRAY(String), default=[])  # homestead, senior, veteran, disability
    exemption_amount: Mapped[float | None] = mapped_column(Float)
    
    # Payment
    last_paid_date: Mapped[date | None] = mapped_column(Date)
    last_paid_amount: Mapped[float | None] = mapped_column(Float)
    delinquent: Mapped[bool] = mapped_column(Boolean, default=False)
    delinquent_amount: Mapped[float | None] = mapped_column(Float)
    
    # Tax sale
    tax_lien: Mapped[bool] = mapped_column(Boolean, default=False)
    tax_sale_scheduled: Mapped[bool] = mapped_column(Boolean, default=False)
    
    property = relationship("Property", back_populates="tax")


# api/app/models/hoa.py
class HOA(Base, TimestampMixin):
    __tablename__ = "hoas"
    __table_args__ = {"schema": "parcel"}
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    property_id: Mapped[str] = mapped_column(String(50), ForeignKey("parcel.properties.id"), unique=True)
    
    # HOA info
    hoa_name: Mapped[str | None] = mapped_column(String(200))
    hoa_exists: Mapped[bool | None] = mapped_column(Boolean)
    
    # Fees
    fee_monthly: Mapped[float | None] = mapped_column(Float)
    fee_annual: Mapped[float | None] = mapped_column(Float)
    fee_includes: Mapped[list] = mapped_column(ARRAY(String), default=[])  # landscaping, pool, insurance
    
    # Special assessments
    special_assessment: Mapped[bool] = mapped_column(Boolean, default=False)
    special_assessment_amount: Mapped[float | None] = mapped_column(Float)
    
    # Rules
    rental_allowed: Mapped[bool | None] = mapped_column(Boolean)
    rental_restrictions: Mapped[str | None] = mapped_column(String(500))
    pet_policy: Mapped[str | None] = mapped_column(String(200))
    
    # Contact
    contact_name: Mapped[str | None] = mapped_column(String(100))
    contact_phone: Mapped[str | None] = mapped_column(String(20))
    contact_email: Mapped[str | None] = mapped_column(String(100))
    management_company: Mapped[str | None] = mapped_column(String(200))
    
    property = relationship("Property", back_populates="hoa")
```

### S14: Models Package Export
Create `api/app/models/__init__.py` to export all models.

```python
# api/app/models/__init__.py
from .base import Base, TimestampMixin, DataQualityMixin, ProvenanceMixin
from .property import Property
from .address import Address
from .building import Building
from .valuation import Valuation
from .ownership import Ownership
from .zoning import Zoning
from .listing import Listing
from .transaction import Transaction
from .permit import Permit
from .environmental import Environmental
from .school import School
from .tax import Tax
from .hoa import HOA

__all__ = [
    "Base",
    "TimestampMixin",
    "DataQualityMixin",
    "ProvenanceMixin",
    "Property",
    "Address",
    "Building",
    "Valuation",
    "Ownership",
    "Zoning",
    "Listing",
    "Transaction",
    "Permit",
    "Environmental",
    "School",
    "Tax",
    "HOA",
]
```

### S15: Alembic Migration
Create the initial Alembic migration for all models.

```bash
cd /home/numen/dharma/parceldata/api
alembic revision --autogenerate -m "Initial schema with all property models"
alembic upgrade head
```

Verify all tables created with proper indexes and constraints.

---

## Acceptance Criteria
- All 14 SQLAlchemy models defined and validated
- PostGIS geometry columns work (`location`, `boundary`)
- pgvector column works (`embedding`)
- All relationships defined correctly
- Alembic migration runs without errors
- Tables created in `parcel` schema
- Proper indexes on query columns (property_id, state_fips, city, zip, etc.)
- All new code passes `ruff check` and `mypy --strict`
