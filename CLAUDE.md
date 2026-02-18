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

## Current Stage: P10-03-core-api

# PRD: P10-03 — Core API

## Overview
Implement the core property API endpoints: lookup by ID/address/coordinates, search with filters, comparables, market trends, batch operations, and GraphQL. Every response must include data quality scores and provenance metadata.

---

## Stories

### S1: Pydantic Response Schemas
Create `api/app/schemas/property.py` with response models.

```python
# api/app/schemas/property.py
from datetime import datetime, date
from pydantic import BaseModel, Field
from typing import Optional

class DataQualitySchema(BaseModel):
    """Data quality score for every response."""
    score: float = Field(..., ge=0, le=1, description="Overall quality score 0-1")
    components: dict = Field(default_factory=dict)
    freshness_hours: int = Field(0, description="Hours since last update")
    sources: list[str] = Field(default_factory=list)
    confidence: str = Field("medium", description="low/medium/high")

class ProvenanceSchema(BaseModel):
    """Source tracking for audit and compliance."""
    source_system: Optional[str] = None
    source_type: Optional[str] = None
    extraction_timestamp: Optional[datetime] = None
    transformation_version: Optional[str] = None
    license_type: Optional[str] = None
    attribution_required: bool = False
    last_verified: Optional[datetime] = None

class AddressSchema(BaseModel):
    street: Optional[str] = None
    unit: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip: Optional[str] = None
    zip4: Optional[str] = None
    county: Optional[str] = None
    formatted: Optional[str] = None

class LocationSchema(BaseModel):
    lat: Optional[float] = None
    lng: Optional[float] = None
    geoid: Optional[dict] = None

class ParcelSchema(BaseModel):
    apn: Optional[str] = None
    legal_description: Optional[str] = None
    lot_sqft: Optional[int] = None
    lot_acres: Optional[float] = None
    lot_dimensions: Optional[str] = None

class BuildingSchema(BaseModel):
    sqft: Optional[int] = None
    stories: Optional[int] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    year_built: Optional[int] = None
    construction: Optional[str] = None
    roof: Optional[str] = None
    foundation: Optional[str] = None
    garage: Optional[str] = None
    garage_spaces: Optional[int] = None
    pool: bool = False

class ValuationSchema(BaseModel):
    assessed_total: Optional[int] = None
    assessed_land: Optional[int] = None
    assessed_improvements: Optional[int] = None
    assessed_year: Optional[int] = None
    estimated_value: Optional[int] = None
    estimated_value_low: Optional[int] = None
    estimated_value_high: Optional[int] = None
    price_per_sqft: Optional[float] = None

class OwnershipSchema(BaseModel):
    owner_name: Optional[str] = None
    owner_type: Optional[str] = None
    owner_occupied: Optional[bool] = None
    acquisition_date: Optional[date] = None
    acquisition_price: Optional[int] = None
    ownership_length_years: Optional[float] = None

class ZoningSchema(BaseModel):
    zone_code: Optional[str] = None
    zone_description: Optional[str] = None
    permitted_uses: list[str] = Field(default_factory=list)
    conditional_uses: list[str] = Field(default_factory=list)
    setbacks: Optional[dict] = None
    max_height: Optional[float] = None
    max_far: Optional[float] = None
    max_impervious: Optional[float] = None

class ListingSchema(BaseModel):
    status: Optional[str] = None
    list_price: Optional[int] = None
    list_date: Optional[date] = None
    days_on_market: Optional[int] = None
    mls_number: Optional[str] = None
    listing_agent: Optional[dict] = None

class TaxSchema(BaseModel):
    annual_amount: Optional[float] = None
    tax_rate: Optional[float] = None
    exemptions: list[str] = Field(default_factory=list)
    last_paid_date: Optional[date] = None
    delinquent: bool = False

class EnvironmentalSchema(BaseModel):
    flood_zone: Optional[str] = None
    flood_zone_description: Optional[str] = None
    in_100yr_floodplain: bool = False
    wildfire_risk: Optional[str] = None
    earthquake_risk: Optional[str] = None

class SchoolSchema(BaseModel):
    elementary: Optional[dict] = None
    middle: Optional[dict] = None
    high: Optional[dict] = None

class HOASchema(BaseModel):
    name: Optional[str] = None
    fee_monthly: Optional[float] = None
    fee_includes: list[str] = Field(default_factory=list)
    contact_phone: Optional[str] = None

class PropertyResponse(BaseModel):
    """Full property response."""
    property_id: str
    address: AddressSchema
    location: LocationSchema
    parcel: ParcelSchema
    building: Optional[BuildingSchema] = None
    valuation: Optional[ValuationSchema] = None
    ownership: Optional[OwnershipSchema] = None
    zoning: Optional[ZoningSchema] = None
    listing: Optional[ListingSchema] = None
    tax: Optional[TaxSchema] = None
    environmental: Optional[EnvironmentalSchema] = None
    schools: Optional[SchoolSchema] = None
    hoa: Optional[HOASchema] = None
    data_quality: DataQualitySchema
    provenance: Optional[ProvenanceSchema] = None
    metadata: dict = Field(default_factory=dict)

class PropertyMicroResponse(BaseModel):
    """Minimal response for token efficiency."""
    id: str
    price: Optional[int] = None
    beds: Optional[int] = None
    baths: Optional[float] = None
    sqft: Optional[int] = None
    addr: Optional[str] = None
```

### S2: Property Lookup Service
Create `api/app/services/property_service.py` with lookup methods.

```python
# api/app/services/property_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models import Property, Address, Building, Valuation, Ownership, Zoning
from app.schemas.property import PropertyResponse, PropertyMicroResponse, DataQualitySchema
from typing import Optional

class PropertyService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_id(self, property_id: str) -> Optional[Property]:
        """Get property by Dharma Parcel ID."""
        stmt = (
            select(Property)
            .options(
                selectinload(Property.address),
                selectinload(Property.buildings),
                selectinload(Property.valuation),
                selectinload(Property.ownership),
                selectinload(Property.zoning),
                selectinload(Property.listing),
                selectinload(Property.environmental),
                selectinload(Property.school),
                selectinload(Property.tax),
                selectinload(Property.hoa),
            )
            .where(Property.id == property_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_address(
        self, 
        street: str, 
        city: str, 
        state: str,
        unit: Optional[str] = None,
        zip_code: Optional[str] = None,
    ) -> Optional[Property]:
        """Get property by address components."""
        stmt = (
            select(Property)
            .join(Address)
            .options(
                selectinload(Property.address),
                selectinload(Property.buildings),
                selectinload(Property.valuation),
                selectinload(Property.ownership),
                selectinload(Property.zoning),
            )
            .where(
                Address.street_address.ilike(f"%{street}%"),
                Address.city.ilike(city),
                Address.state == state.upper(),
            )
        )
        if zip_code:
            stmt = stmt.where(Address.zip_code == zip_code)
        
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_coordinates(
        self,
        lat: float,
        lng: float,
        radius_meters: float = 50,
    ) -> Optional[Property]:
        """Get property by lat/lng coordinates."""
        from geoalchemy2.functions import ST_DWithin, ST_MakePoint, ST_SetSRID
        
        point = ST_SetSRID(ST_MakePoint(lng, lat), 4326)
        
        stmt = (
            select(Property)
            .options(selectinload(Property.address))
            .where(ST_DWithin(Property.location, point, radius_meters))
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    def to_response(
        self, 
        prop: Property, 
        detail: str = "standard"
    ) -> PropertyResponse | PropertyMicroResponse:
        """Convert Property model to response schema."""
        if detail == "micro":
            return self._to_micro_response(prop)
        return self._to_full_response(prop)
    
    def _to_micro_response(self, prop: Property) -> PropertyMicroResponse:
        building = prop.buildings[0] if prop.buildings else None
        return PropertyMicroResponse(
            id=prop.id,
            price=prop.valuation.estimated_value if prop.valuation else None,
            beds=building.bedrooms if building else None,
            baths=building.bathrooms if building else None,
            sqft=building.sqft if building else None,
            addr=prop.address.formatted_address if prop.address else None,
        )
    
    def _to_full_response(self, prop: Property) -> PropertyResponse:
        # Build full response with all nested schemas
        # (implementation details for each nested object)
        return PropertyResponse(
            property_id=prop.id,
            address=self._address_schema(prop.address),
            location=self._location_schema(prop),
            parcel=self._parcel_schema(prop),
            building=self._building_schema(prop.buildings[0] if prop.buildings else None),
            valuation=self._valuation_schema(prop.valuation),
            ownership=self._ownership_schema(prop.ownership),
            zoning=self._zoning_schema(prop.zoning),
            listing=self._listing_schema(prop.listing),
            tax=self._tax_schema(prop.tax),
            environmental=self._environmental_schema(prop.environmental),
            schools=self._school_schema(prop.school),
            hoa=self._hoa_schema(prop.hoa),
            data_quality=self._quality_schema(prop),
            provenance=self._provenance_schema(prop),
            metadata={
                "last_updated": prop.updated_at.isoformat() if prop.updated_at else None,
                "data_sources": [prop.source_system] if prop.source_system else [],
            },
        )
    
    def _quality_schema(self, prop: Property) -> DataQualitySchema:
        return DataQualitySchema(
            score=prop.quality_score,
            components={
                "completeness": prop.quality_completeness,
                "accuracy": prop.quality_accuracy,
                "consistency": prop.quality_consistency,
                "timeliness": prop.quality_timeliness,
                "validity": prop.quality_validity,
                "uniqueness": prop.quality_uniqueness,
            },
            freshness_hours=prop.freshness_hours,
            sources=[prop.source_system] if prop.source_system else [],
            confidence="high" if prop.quality_score >= 0.85 else "medium" if prop.quality_score >= 0.7 else "low",
        )
```

### S3: Property Lookup Route
Create `api/app/routes/properties.py` with lookup endpoints.

```python
# api/app/routes/properties.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.connection import get_db
from app.services.property_service import PropertyService
from app.schemas.property import PropertyResponse, PropertyMicroResponse
from typing import Literal

router = APIRouter(prefix="/v1/properties", tags=["Properties"])

@router.get("/{property_id}", response_model=PropertyResponse)
async def get_property_by_id(
    property_id: str,
    detail: Literal["micro", "standard", "extended", "full"] = "standard",
    db: AsyncSession = Depends(get_db),
):
    """
    Get property by Dharma Parcel ID.
    
    - **property_id**: Dharma Parcel ID (e.g., TX-TRAVIS-0234567)
    - **detail**: Response detail level (micro, standard, extended, full)
    """
    service = PropertyService(db)
    prop = await service.get_by_id(property_id)
    
    if not prop:
        raise HTTPException(
            status_code=404,
            detail=f"Property not found: {property_id}",
        )
    
    return service.to_response(prop, detail)

@router.get("/address", response_model=PropertyResponse)
async def get_property_by_address(
    street: str = Query(..., description="Street address"),
    city: str = Query(..., description="City name"),
    state: str = Query(..., description="State (2-letter code)"),
    unit: str | None = Query(None, description="Unit/Apt number"),
    zip: str | None = Query(None, description="ZIP code"),
    detail: Literal["micro", "standard", "extended", "full"] = "standard",
    db: AsyncSession = Depends(get_db),
):
    """
    Get property by address components.
    
    Returns the best match for the given address.
    """
    service = PropertyService(db)
    prop = await service.get_by_address(street, city, state, unit, zip)
    
    if not prop:
        raise HTTPException(
            status_code=404,
            detail="No property found matching the provided address",
        )
    
    return service.to_response(prop, detail)

@router.get("/coordinates", response_model=PropertyResponse)
async def get_property_by_coordinates(
    lat: float = Query(..., description="Latitude"),
    lng: float = Query(..., description="Longitude"),
    detail: Literal["micro", "standard", "extended", "full"] = "standard",
    db: AsyncSession = Depends(get_db),
):
    """
    Get property by coordinates.
    
    Returns the property at or nearest to the given coordinates.
    """
    service = PropertyService(db)
    prop = await service.get_by_coordinates(lat, lng)
    
    if not prop:
        raise HTTPException(
            status_code=404,
            detail="No property found at the provided coordinates",
        )
    
    return service.to_response(prop, detail)
```

### S4: Property Search Service
Create `api/app/services/search_service.py` for search with filters.

```python
# api/app/services/search_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload
from geoalchemy2.functions import ST_MakeEnvelope, ST_Intersects
from app.models import Property, Address, Building, Listing, Zoning
from typing import Optional
from pydantic import BaseModel

class SearchFilters(BaseModel):
    # Geographic
    state: Optional[str] = None
    city: Optional[str] = None
    zip: Optional[str] = None
    county: Optional[str] = None
    bounds: Optional[dict] = None  # {north, south, east, west}
    
    # Property type
    property_type: Optional[list[str]] = None
    
    # Building
    bedrooms_min: Optional[int] = None
    bedrooms_max: Optional[int] = None
    bathrooms_min: Optional[float] = None
    sqft_min: Optional[int] = None
    sqft_max: Optional[int] = None
    year_built_min: Optional[int] = None
    year_built_max: Optional[int] = None
    
    # Lot
    lot_sqft_min: Optional[int] = None
    lot_sqft_max: Optional[int] = None
    
    # Price
    price_min: Optional[int] = None
    price_max: Optional[int] = None
    
    # Listing
    listing_status: Optional[list[str]] = None
    
    # Zoning
    zoning: Optional[list[str]] = None

class SearchService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def search(
        self,
        filters: SearchFilters,
        limit: int = 25,
        offset: int = 0,
        sort_field: str = "property_id",
        sort_order: str = "asc",
    ) -> tuple[list[Property], int]:
        """Search properties with filters."""
        
        stmt = select(Property).options(
            selectinload(Property.address),
            selectinload(Property.buildings),
            selectinload(Property.valuation),
            selectinload(Property.listing),
        )
        
        conditions = []
        
        # Geographic filters
        if filters.state:
            conditions.append(Address.state == filters.state.upper())
        if filters.city:
            conditions.append(Address.city.ilike(f"%{filters.city}%"))
        if filters.zip:
            conditions.append(Address.zip_code == filters.zip)
        
        # Bounding box
        if filters.bounds:
            envelope = ST_MakeEnvelope(
                filters.bounds["west"],
                filters.bounds["south"],
                filters.bounds["east"],
                filters.bounds["north"],
                4326,
            )
            conditions.append(ST_Intersects(Property.location, envelope))
        
        # Property type
        if filters.property_type:
            conditions.append(Property.property_type.in_(filters.property_type))
        
        # Building filters (join)
        if any([
            filters.bedrooms_min, filters.bedrooms_max,
            filters.bathrooms_min, filters.sqft_min, filters.sqft_max,
            filters.year_built_min, filters.year_built_max,
        ]):
            stmt = stmt.join(Building)
            if filters.bedrooms_min:
                conditions.append(Building.bedrooms >= filters.bedrooms_min)
            if filters.bedrooms_max:
                conditions.append(Building.bedrooms <= filters.bedrooms_max)
            if filters.bathrooms_min:
                conditions.append(Building.bathrooms >= filters.bathrooms_min)
            if filters.sqft_min:
                conditions.append(Building.sqft >= filters.sqft_min)
            if filters.sqft_max:
                conditions.append(Building.sqft <= filters.sqft_max)
            if filters.year_built_min:
                conditions.append(Building.year_built >= filters.year_built_min)
            if filters.year_built_max:
                conditions.append(Building.year_built <= filters.year_built_max)
        
        # Lot filters
        if filters.lot_sqft_min:
            conditions.append(Property.lot_sqft >= filters.lot_sqft_min)
        if filters.lot_sqft_max:
            conditions.append(Property.lot_sqft <= filters.lot_sqft_max)
        
        # Price filters (from listing or valuation)
        if filters.price_min or filters.price_max:
            stmt = stmt.join(Listing, isouter=True)
            if filters.price_min:
                conditions.append(Listing.list_price >= filters.price_min)
            if filters.price_max:
                conditions.append(Listing.list_price <= filters.price_max)
        
        # Listing status
        if filters.listing_status:
            stmt = stmt.join(Listing, isouter=True)
            conditions.append(Listing.status.in_(filters.listing_status))
        
        # Zoning
        if filters.zoning:
            stmt = stmt.join(Zoning, isouter=True)
            conditions.append(Zoning.zone_code.in_(filters.zoning))
        
        # Join Address for geographic filters
        if filters.state or filters.city or filters.zip:
            stmt = stmt.join(Address)
        
        # Apply conditions
        if conditions:
            stmt = stmt.where(and_(*conditions))
        
        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar() or 0
        
        # Sort
        sort_col = getattr(Property, sort_field, Property.id)
        if sort_order == "desc":
            stmt = stmt.order_by(sort_col.desc())
        else:
            stmt = stmt.order_by(sort_col.asc())
        
        # Paginate
        stmt = stmt.offset(offset).limit(limit)
        
        result = await self.db.execute(stmt)
        properties = result.scalars().all()
        
        return list(properties), total
```

### S5: Property Search Route
Create search endpoint in `api/app/routes/properties.py`.

```python
# Add to api/app/routes/properties.py

from app.services.search_service import SearchService, SearchFilters
from pydantic import BaseModel, Field

class SearchRequest(BaseModel):
    """Property search request body."""
    state: str | None = None
    city: str | None = None
    zip: str | None = None
    county: str | None = None
    bounds: dict | None = Field(None, description="Bounding box: {north, south, east, west}")
    property_type: list[str] | None = None
    bedrooms_min: int | None = None
    bedrooms_max: int | None = None
    bathrooms_min: float | None = None
    sqft_min: int | None = None
    sqft_max: int | None = None
    year_built_min: int | None = None
    year_built_max: int | None = None
    lot_sqft_min: int | None = None
    lot_sqft_max: int | None = None
    price_min: int | None = None
    price_max: int | None = None
    listing_status: list[str] | None = None
    zoning: list[str] | None = None
    limit: int = Field(25, ge=1, le=100)
    offset: int = Field(0, ge=0)
    sort: str = Field("property_id:asc")

class SearchResponse(BaseModel):
    results: list[PropertyResponse]
    total: int
    limit: int
    offset: int
    has_more: bool

@router.post("/search", response_model=SearchResponse)
async def search_properties(
    request: SearchRequest,
    detail: Literal["micro", "standard", "extended", "full"] = "standard",
    db: AsyncSession = Depends(get_db),
):
    """
    Search for properties matching criteria.
    
    Supports filtering by location, property characteristics, price, listing status, and zoning.
    """
    filters = SearchFilters(**request.model_dump(exclude={"limit", "offset", "sort"}))
    
    sort_parts = request.sort.split(":")
    sort_field = sort_parts[0]
    sort_order = sort_parts[1] if len(sort_parts) > 1 else "asc"
    
    search_service = SearchService(db)
    properties, total = await search_service.search(
        filters=filters,
        limit=request.limit,
        offset=request.offset,
        sort_field=sort_field,
        sort_order=sort_order,
    )
    
    prop_service = PropertyService(db)
    results = [prop_service.to_response(p, detail) for p in properties]
    
    return SearchResponse(
        results=results,
        total=total,
        limit=request.limit,
        offset=request.offset,
        has_more=(request.offset + len(results)) < total,
    )
```

### S6: Comparables Service
Create `api/app/services/comparables_service.py` for comp analysis.

```python
# api/app/services/comparables_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from geoalchemy2.functions import ST_DWithin, ST_Distance
from datetime import datetime, timedelta
from app.models import Property, Building, Transaction, Address
from typing import Optional

class ComparablesService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def find_comparables(
        self,
        subject_property: Property,
        radius_miles: float = 1.0,
        months: int = 6,
        limit: int = 10,
    ) -> list[dict]:
        """Find comparable sales for a property."""
        
        if not subject_property.location:
            return []
        
        # Get subject characteristics
        subject_building = subject_property.buildings[0] if subject_property.buildings else None
        subject_sqft = subject_building.sqft if subject_building else 0
        subject_beds = subject_building.bedrooms if subject_building else 0
        subject_year = subject_building.year_built if subject_building else 2000
        
        # Convert miles to meters
        radius_meters = radius_miles * 1609.34
        
        # Date cutoff
        cutoff_date = datetime.utcnow() - timedelta(days=months * 30)
        
        # Find nearby sold properties
        stmt = (
            select(Property, Transaction, Building)
            .join(Transaction)
            .join(Building)
            .where(
                and_(
                    ST_DWithin(Property.location, subject_property.location, radius_meters),
                    Property.id != subject_property.id,
                    Transaction.sale_price.isnot(None),
                    Transaction.transaction_date >= cutoff_date,
                    Property.property_type == subject_property.property_type,
                )
            )
            .order_by(ST_Distance(Property.location, subject_property.location))
            .limit(limit * 3)  # Fetch extra for filtering
        )
        
        result = await self.db.execute(stmt)
        candidates = result.all()
        
        # Score and rank comparables
        scored_comps = []
        for prop, txn, building in candidates:
            score = self._calculate_similarity(
                subject_sqft, subject_beds, subject_year,
                building.sqft or 0, building.bedrooms or 0, building.year_built or 2000,
            )
            
            scored_comps.append({
                "property": prop,
                "transaction": txn,
                "building": building,
                "similarity_score": score,
            })
        
        # Sort by similarity and take top N
        scored_comps.sort(key=lambda x: x["similarity_score"], reverse=True)
        return scored_comps[:limit]
    
    def _calculate_similarity(
        self,
        subj_sqft: int, subj_beds: int, subj_year: int,
        comp_sqft: int, comp_beds: int, comp_year: int,
    ) -> float:
        """Calculate similarity score between subject and comp."""
        
        # Square footage similarity (within 20%)
        sqft_diff = abs(subj_sqft - comp_sqft) / max(subj_sqft, 1)
        sqft_score = max(0, 1 - sqft_diff / 0.2)
        
        # Bedroom similarity
        bed_diff = abs(subj_beds - comp_beds)
        bed_score = max(0, 1 - bed_diff * 0.25)
        
        # Year built similarity (within 10 years)
        year_diff = abs(subj_year - comp_year)
        year_score = max(0, 1 - year_diff / 10)
        
        # Weighted average
        return (sqft_score * 0.4) + (bed_score * 0.3) + (year_score * 0.3)
    
    def calculate_suggested_value(
        self,
        subject_property: Property,
        comparables: list[dict],
    ) -> dict:
        """Calculate suggested value from comparables."""
        
        if not comparables:
            return {"estimate": None, "range_low": None, "range_high": None, "confidence": 0}
        
        subject_building = subject_property.buildings[0] if subject_property.buildings else None
        subject_sqft = subject_building.sqft if subject_building else 0
        
        # Calculate weighted price per sqft
        total_weight = 0
        weighted_ppsf = 0
        
        for comp in comparables:
            txn = comp["transaction"]
            building = comp["building"]
            similarity = comp["similarity_score"]
            
            if building.sqft and txn.sale_price:
                ppsf = txn.sale_price / building.sqft
                weighted_ppsf += ppsf * similarity
                total_weight += similarity
        
        if total_weight == 0:
            return {"estimate": None, "range_low": None, "range_high": None, "confidence": 0}
        
        avg_ppsf = weighted_ppsf / total_weight
        estimate = int(avg_ppsf * subject_sqft)
        
        # Calculate range (±10%)
        return {
            "estimate": estimate,
            "range_low": int(estimate * 0.9),
            "range_high": int(estimate * 1.1),
            "confidence": min(total_weight / len(comparables), 1.0),
        }
```

### S7: Analytics Routes
Create `api/app/routes/analytics.py` for comparables and trends.

```python
# api/app/routes/analytics.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.connection import get_db
from app.services.property_service import PropertyService
from app.services.comparables_service import ComparablesService
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/v1/analytics", tags=["Analytics"])

class ComparableProperty(BaseModel):
    property_id: str
    address: str
    distance_miles: float
    sale_date: str | None
    sale_price: int | None
    sqft: int | None
    bedrooms: int | None
    year_built: int | None
    price_per_sqft: float | None
    similarity_score: float

class ComparablesResponse(BaseModel):
    subject_property: dict
    comparables: list[ComparableProperty]
    suggested_value: dict
    data_quality: dict

@router.get("/comparables", response_model=ComparablesResponse)
async def get_comparables(
    property_id: str = Query(..., description="Subject property ID"),
    radius_miles: float = Query(1.0, ge=0.1, le=10),
    months: int = Query(6, ge=1, le=24),
    limit: int = Query(10, ge=1, le=25),
    db: AsyncSession = Depends(get_db),
):
    """
    Find comparable sales for a property.
    
    Returns similar properties that sold within the radius and time period,
    along with a suggested value estimate.
    """
    prop_service = PropertyService(db)
    subject = await prop_service.get_by_id(property_id)
    
    if not subject:
        raise HTTPException(status_code=404, detail="Property not found")
    
    comp_service = ComparablesService(db)
    comps = await comp_service.find_comparables(
        subject_property=subject,
        radius_miles=radius_miles,
        months=months,
        limit=limit,
    )
    
    suggested = comp_service.calculate_suggested_value(subject, comps)
    
    # Format response
    subject_building = subject.buildings[0] if subject.buildings else None
    
    return ComparablesResponse(
        subject_property={
            "property_id": subject.id,
            "sqft": subject_building.sqft if subject_building else None,
            "bedrooms": subject_building.bedrooms if subject_building else None,
            "year_built": subject_building.year_built if subject_building else None,
        },
        comparables=[
            ComparableProperty(
                property_id=c["property"].id,
                address=c["property"].address.formatted_address if c["property"].address else "",
                distance_miles=0,  # Calculate from ST_Distance
                sale_date=c["transaction"].transaction_date.isoformat() if c["transaction"].transaction_date else None,
                sale_price=c["transaction"].sale_price,
                sqft=c["building"].sqft,
                bedrooms=c["building"].bedrooms,
                year_built=c["building"].year_built,
                price_per_sqft=c["transaction"].sale_price / c["building"].sqft if c["building"].sqft else None,
                similarity_score=c["similarity_score"],
            )
            for c in comps
        ],
        suggested_value=suggested,
        data_quality={
            "score": sum(c["property"].quality_score for c in comps) / len(comps) if comps else 0,
            "comp_count": len(comps),
            "confidence": "high" if len(comps) >= 5 else "medium" if len(comps) >= 3 else "low",
        },
    )

class MarketTrendsResponse(BaseModel):
    location: dict
    period: str
    metrics: dict
    trends: list[dict]
    data_quality: dict

@router.get("/market-trends", response_model=MarketTrendsResponse)
async def get_market_trends(
    zip: str | None = Query(None),
    city: str | None = Query(None),
    state: str | None = Query(None),
    county: str | None = Query(None),
    property_type: str | None = Query(None),
    period: str = Query("12m", description="3m, 6m, 12m, 24m, 5y"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get market statistics and trends for an area.
    
    Returns price trends, days on market, inventory levels, etc.
    """
    # Implementation calculates aggregate statistics from transactions and listings
    # This is a placeholder that should be implemented with actual analytics queries
    
    return MarketTrendsResponse(
        location={
            "zip": zip,
            "city": city,
            "state": state,
            "county": county,
        },
        period=period,
        metrics={
            "median_sale_price": 500000,
            "price_per_sqft": 250,
            "days_on_market": 21,
            "inventory_months": 2.5,
            "list_to_sale_ratio": 0.98,
            "total_sales": 150,
            "total_active": 45,
        },
        trends=[
            {"month": "2026-01", "median_price": 495000, "sales_count": 12},
            {"month": "2026-02", "median_price": 502000, "sales_count": 14},
        ],
        data_quality={
            "score": 0.85,
            "confidence": "high",
            "data_points": 150,
        },
    )
```

### S8: Batch Operations Route
Add batch lookup to `api/app/routes/properties.py`.

```python
# Add to api/app/routes/properties.py

class BatchLookupRequest(BaseModel):
    property_ids: list[str] = Field(..., max_length=100)
    detail: Literal["micro", "standard", "extended", "full"] = "standard"

class BatchLookupResponse(BaseModel):
    results: list[PropertyResponse | None]
    found: int
    not_found: int
    errors: list[str]

@router.post("/batch", response_model=BatchLookupResponse)
async def batch_lookup(
    request: BatchLookupRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Batch property lookup by IDs.
    
    Returns properties in the same order as requested IDs.
    Maximum 100 properties per request.
    """
    service = PropertyService(db)
    results = []
    errors = []
    found = 0
    not_found = 0
    
    for prop_id in request.property_ids:
        try:
            prop = await service.get_by_id(prop_id)
            if prop:
                results.append(service.to_response(prop, request.detail))
                found += 1
            else:
                results.append(None)
                not_found += 1
        except Exception as e:
            results.append(None)
            errors.append(f"{prop_id}: {str(e)}")
    
    return BatchLookupResponse(
        results=results,
        found=found,
        not_found=not_found,
        errors=errors,
    )
```

### S9: Field Selection
Add field selection support via `select` query parameter.

```python
# Update get_property_by_id in api/app/routes/properties.py

@router.get("/{property_id}")
async def get_property_by_id(
    property_id: str,
    detail: Literal["micro", "standard", "extended", "full"] = "standard",
    select: str | None = Query(None, description="Comma-separated field names to include"),
    include_provenance: bool = Query(True, description="Include provenance metadata"),
    db: AsyncSession = Depends(get_db),
):
    """..."""
    service = PropertyService(db)
    prop = await service.get_by_id(property_id)
    
    if not prop:
        raise HTTPException(status_code=404, detail=f"Property not found: {property_id}")
    
    response = service.to_response(prop, detail)
    
    # Apply field selection
    if select:
        fields = [f.strip() for f in select.split(",")]
        response_dict = response.model_dump()
        filtered = {k: v for k, v in response_dict.items() if k in fields}
        # Always include data_quality
        filtered["data_quality"] = response_dict["data_quality"]
        return filtered
    
    if not include_provenance:
        response_dict = response.model_dump()
        response_dict.pop("provenance", None)
        return response_dict
    
    return response
```

### S10: GraphQL Schema
Create `api/app/graphql/schema.py` with Strawberry GraphQL.

```python
# api/app/graphql/schema.py
import strawberry
from strawberry.fastapi import GraphQLRouter
from typing import Optional
from app.database.connection import async_session_maker
from app.services.property_service import PropertyService

@strawberry.type
class AddressType:
    street: Optional[str]
    city: Optional[str]
    state: Optional[str]
    zip: Optional[str]
    formatted: Optional[str]

@strawberry.type
class BuildingType:
    sqft: Optional[int]
    bedrooms: Optional[int]
    bathrooms: Optional[float]
    year_built: Optional[int]
    stories: Optional[int]

@strawberry.type
class ValuationType:
    assessed_total: Optional[int]
    estimated_value: Optional[int]
    price_per_sqft: Optional[float]

@strawberry.type
class ZoningType:
    zone_code: Optional[str]
    zone_description: Optional[str]
    permitted_uses: list[str]
    max_height: Optional[float]
    max_far: Optional[float]

@strawberry.type
class DataQualityType:
    score: float
    freshness_hours: int
    confidence: str

@strawberry.type
class PropertyType:
    id: str
    address: Optional[AddressType]
    building: Optional[BuildingType]
    valuation: Optional[ValuationType]
    zoning: Optional[ZoningType]
    data_quality: DataQualityType

@strawberry.type
class Query:
    @strawberry.field
    async def property(self, id: str) -> Optional[PropertyType]:
        async with async_session_maker() as db:
            service = PropertyService(db)
            prop = await service.get_by_id(id)
            if not prop:
                return None
            
            # Convert to GraphQL types
            return PropertyType(
                id=prop.id,
                address=AddressType(
                    street=prop.address.street_address if prop.address else None,
                    city=prop.address.city if prop.address else None,
                    state=prop.address.state if prop.address else None,
                    zip=prop.address.zip_code if prop.address else None,
                    formatted=prop.address.formatted_address if prop.address else None,
                ) if prop.address else None,
                building=BuildingType(
                    sqft=prop.buildings[0].sqft if prop.buildings else None,
                    bedrooms=prop.buildings[0].bedrooms if prop.buildings else None,
                    bathrooms=prop.buildings[0].bathrooms if prop.buildings else None,
                    year_built=prop.buildings[0].year_built if prop.buildings else None,
                    stories=prop.buildings[0].stories if prop.buildings else None,
                ) if prop.buildings else None,
                valuation=ValuationType(
                    assessed_total=prop.valuation.assessed_total if prop.valuation else None,
                    estimated_value=prop.valuation.estimated_value if prop.valuation else None,
                    price_per_sqft=prop.valuation.price_per_sqft if prop.valuation else None,
                ) if prop.valuation else None,
                zoning=ZoningType(
                    zone_code=prop.zoning.zone_code if prop.zoning else None,
                    zone_description=prop.zoning.zone_description if prop.zoning else None,
                    permitted_uses=prop.zoning.permitted_uses if prop.zoning else [],
                    max_height=prop.zoning.max_height_ft if prop.zoning else None,
                    max_far=prop.zoning.max_far if prop.zoning else None,
                ) if prop.zoning else None,
                data_quality=DataQualityType(
                    score=prop.quality_score,
                    freshness_hours=prop.freshness_hours,
                    confidence="high" if prop.quality_score >= 0.85 else "medium",
                ),
            )
    
    @strawberry.field
    async def properties(
        self,
        city: Optional[str] = None,
        state: Optional[str] = None,
        limit: int = 10,
    ) -> list[PropertyType]:
        # Implement search via GraphQL
        pass

schema = strawberry.Schema(query=Query)
graphql_router = GraphQLRouter(schema)
```

### S11: Mount GraphQL Router
Update `api/app/main.py` to mount GraphQL.

```python
# In api/app/main.py
from app.graphql.schema import graphql_router

app.include_router(graphql_router, prefix="/graphql")
```

### S12: OpenAPI Documentation
Add OpenAPI tags and descriptions.

```python
# Update api/app/main.py
app = FastAPI(
    title="ParcelData API",
    description="""
    ParcelData API provides clean, normalized real estate data for AI agents.
    
    ## Authentication
    All endpoints require an API key via `Authorization: Bearer <key>` or `X-API-Key: <key>`.
    
    ## Response Detail Levels
    - **micro**: Minimal response (~500 tokens)
    - **standard**: Full property details (~2000 tokens)
    - **extended**: Property + market context (~8000 tokens)
    - **full**: Everything + documents (~32000 tokens)
    
    ## Data Quality
    Every response includes a `data_quality` object with confidence scores.
    """,
    version="0.1.0",
    openapi_tags=[
        {"name": "Properties", "description": "Property lookup and search"},
        {"name": "Analytics", "description": "Comparables and market trends"},
        {"name": "Health", "description": "API health and version"},
    ],
)
```

### S13: Response Pagination
Add cursor-based pagination helper.

```python
# api/app/utils/pagination.py
from pydantic import BaseModel
from typing import Generic, TypeVar, Optional
import base64

T = TypeVar("T")

class CursorPage(BaseModel, Generic[T]):
    items: list[T]
    next_cursor: Optional[str]
    prev_cursor: Optional[str]
    total: int
    has_more: bool

def encode_cursor(offset: int) -> str:
    return base64.b64encode(f"offset:{offset}".encode()).decode()

def decode_cursor(cursor: str) -> int:
    try:
        decoded = base64.b64decode(cursor).decode()
        if decoded.startswith("offset:"):
            return int(decoded[7:])
    except:
        pass
    return 0
```

### S14: Integration Tests
Create `api/tests/test_properties.py` for route tests.

```python
# api/tests/test_properties.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_health_check(client):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded"]

@pytest.mark.asyncio
async def test_property_lookup_not_found(client):
    response = await client.get(
        "/v1/properties/NONEXISTENT-ID",
        headers={"Authorization": "Bearer pk_test_123"},
    )
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_search_requires_auth(client):
    response = await client.post("/v1/properties/search", json={"state": "TX"})
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_graphql_query(client):
    response = await client.post(
        "/graphql",
        json={"query": "{ property(id: \"test\") { id } }"},
        headers={"Authorization": "Bearer pk_test_123"},
    )
    assert response.status_code == 200
```

### S15: Data Quality in Every Response
Ensure all response schemas include `data_quality`.

Update all route handlers to always include `data_quality` object, even for error states:

```python
# In error handlers, include partial data_quality
{
    "error": {...},
    "data_quality": {
        "score": 0,
        "confidence": "none",
        "message": "No data available"
    }
}
```

---

## Acceptance Criteria
- `GET /v1/properties/{id}` returns property with data_quality
- `GET /v1/properties/address` finds property by address
- `GET /v1/properties/coordinates` finds property by lat/lng
- `POST /v1/properties/search` returns paginated results
- `POST /v1/properties/batch` handles up to 100 IDs
- `GET /v1/analytics/comparables` returns similar properties
- `GET /v1/analytics/market-trends` returns market statistics
- `POST /graphql` handles property queries
- Token tiers (micro, standard, extended, full) work correctly
- Field selection via `?select=` works
- All responses include `data_quality` object
- All new code passes `ruff check` and `mypy --strict`
