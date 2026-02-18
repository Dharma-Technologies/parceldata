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

## Current Stage: P10-05-data-pipeline

# PRD: P10-05 — Data Pipeline

## Overview
Build the data ingestion framework with provider adapters for Regrid, ATTOM, Census, FEMA, and EPA. Implement address normalization, geocoding, entity resolution, data quality scoring, and freshness tracking.

---

## Stories

### S1: Provider Adapter Base Class
Create `api/app/services/ingestion/base.py` with abstract adapter.

```python
# api/app/services/ingestion/base.py
from abc import ABC, abstractmethod
from datetime import datetime
from typing import AsyncIterator
from pydantic import BaseModel

class RawPropertyRecord(BaseModel):
    """Raw property record from a data provider."""
    source_system: str
    source_type: str
    source_record_id: str
    extraction_timestamp: datetime
    raw_data: dict
    
    # Parsed fields (provider fills what it can)
    parcel_id: str | None = None
    address_raw: str | None = None
    latitude: float | None = None
    longitude: float | None = None

class ProviderAdapter(ABC):
    """Base class for data provider adapters."""
    
    name: str
    source_type: str
    
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key
    
    @abstractmethod
    async def fetch_property(self, property_id: str) -> RawPropertyRecord | None:
        """Fetch a single property by ID."""
        pass
    
    @abstractmethod
    async def fetch_by_address(
        self,
        street: str,
        city: str,
        state: str,
        zip_code: str | None = None,
    ) -> RawPropertyRecord | None:
        """Fetch property by address."""
        pass
    
    @abstractmethod
    async def fetch_batch(
        self,
        property_ids: list[str],
    ) -> list[RawPropertyRecord]:
        """Fetch multiple properties by ID."""
        pass
    
    @abstractmethod
    async def stream_region(
        self,
        state: str,
        county: str | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[RawPropertyRecord]:
        """Stream all properties in a region."""
        pass
    
    @abstractmethod
    def get_coverage_info(self) -> dict:
        """Return coverage information for this provider."""
        pass
```

### S2: Regrid Adapter
Create `api/app/services/ingestion/providers/regrid.py`.

```python
# api/app/services/ingestion/providers/regrid.py
import httpx
from datetime import datetime
from typing import AsyncIterator
from app.services.ingestion.base import ProviderAdapter, RawPropertyRecord
from app.config import settings

class RegridAdapter(ProviderAdapter):
    """Adapter for Regrid parcel data API."""
    
    name = "regrid"
    source_type = "parcel_data"
    base_url = "https://app.regrid.com/api/v1"
    
    def __init__(self, api_key: str | None = None):
        super().__init__(api_key or settings.regrid_api_key)
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=30.0,
        )
    
    async def fetch_property(self, property_id: str) -> RawPropertyRecord | None:
        """Fetch property by Regrid parcel ID."""
        try:
            response = await self.client.get(f"/parcels/{property_id}")
            response.raise_for_status()
            data = response.json()
            
            return self._to_raw_record(data)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise
    
    async def fetch_by_address(
        self,
        street: str,
        city: str,
        state: str,
        zip_code: str | None = None,
    ) -> RawPropertyRecord | None:
        """Fetch property by address using Regrid geocoding."""
        address = f"{street}, {city}, {state}"
        if zip_code:
            address += f" {zip_code}"
        
        response = await self.client.get(
            "/parcels/search",
            params={"address": address, "limit": 1},
        )
        response.raise_for_status()
        results = response.json().get("results", [])
        
        if results:
            return self._to_raw_record(results[0])
        return None
    
    async def fetch_batch(self, property_ids: list[str]) -> list[RawPropertyRecord]:
        """Fetch multiple properties."""
        results = []
        for prop_id in property_ids:
            record = await self.fetch_property(prop_id)
            if record:
                results.append(record)
        return results
    
    async def stream_region(
        self,
        state: str,
        county: str | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[RawPropertyRecord]:
        """Stream parcels in a region."""
        params = {"state": state}
        if county:
            params["county"] = county
        if limit:
            params["limit"] = limit
        
        offset = 0
        page_size = 100
        
        while True:
            params["offset"] = offset
            params["limit"] = min(page_size, limit - offset if limit else page_size)
            
            response = await self.client.get("/parcels", params=params)
            response.raise_for_status()
            data = response.json()
            
            parcels = data.get("results", [])
            if not parcels:
                break
            
            for parcel in parcels:
                yield self._to_raw_record(parcel)
            
            offset += len(parcels)
            if limit and offset >= limit:
                break
    
    def _to_raw_record(self, data: dict) -> RawPropertyRecord:
        """Convert Regrid response to RawPropertyRecord."""
        properties = data.get("properties", {})
        geometry = data.get("geometry", {})
        
        # Extract coordinates from geometry
        lat, lng = None, None
        if geometry.get("type") == "Point":
            coords = geometry.get("coordinates", [])
            if len(coords) >= 2:
                lng, lat = coords[0], coords[1]
        
        return RawPropertyRecord(
            source_system="regrid",
            source_type="parcel_data",
            source_record_id=data.get("id", ""),
            extraction_timestamp=datetime.utcnow(),
            raw_data=data,
            parcel_id=properties.get("parcelnumb"),
            address_raw=properties.get("address"),
            latitude=lat,
            longitude=lng,
        )
    
    def get_coverage_info(self) -> dict:
        return {
            "provider": "Regrid",
            "coverage": "Nationwide (US)",
            "data_types": ["parcel_boundaries", "ownership", "zoning", "tax"],
            "update_frequency": "monthly",
        }
```

### S3: ATTOM Adapter
Create `api/app/services/ingestion/providers/attom.py`.

```python
# api/app/services/ingestion/providers/attom.py
import httpx
from datetime import datetime
from typing import AsyncIterator
from app.services.ingestion.base import ProviderAdapter, RawPropertyRecord
from app.config import settings

class ATTOMAdapter(ProviderAdapter):
    """Adapter for ATTOM property data API."""
    
    name = "attom"
    source_type = "property_records"
    base_url = "https://api.gateway.attomdata.com"
    
    def __init__(self, api_key: str | None = None):
        super().__init__(api_key or settings.attom_api_key)
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "apikey": self.api_key,
                "Accept": "application/json",
            },
            timeout=30.0,
        )
    
    async def fetch_property(self, property_id: str) -> RawPropertyRecord | None:
        """Fetch property by ATTOM ID."""
        try:
            response = await self.client.get(
                "/propertyapi/v1.0.0/property/detail",
                params={"attomid": property_id},
            )
            response.raise_for_status()
            data = response.json()
            
            properties = data.get("property", [])
            if properties:
                return self._to_raw_record(properties[0])
            return None
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise
    
    async def fetch_by_address(
        self,
        street: str,
        city: str,
        state: str,
        zip_code: str | None = None,
    ) -> RawPropertyRecord | None:
        """Fetch property by address."""
        params = {
            "address1": street,
            "address2": f"{city}, {state}",
        }
        if zip_code:
            params["address2"] += f" {zip_code}"
        
        response = await self.client.get(
            "/propertyapi/v1.0.0/property/address",
            params=params,
        )
        response.raise_for_status()
        data = response.json()
        
        properties = data.get("property", [])
        if properties:
            return self._to_raw_record(properties[0])
        return None
    
    async def fetch_batch(self, property_ids: list[str]) -> list[RawPropertyRecord]:
        """Fetch multiple properties."""
        results = []
        for prop_id in property_ids:
            record = await self.fetch_property(prop_id)
            if record:
                results.append(record)
        return results
    
    async def stream_region(
        self,
        state: str,
        county: str | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[RawPropertyRecord]:
        """Stream properties in a region (via snapshot/bulk)."""
        # ATTOM uses different endpoints for bulk access
        # This is a placeholder - actual implementation depends on ATTOM contract
        params = {"geoid": f"{state}"}  # Simplified
        
        response = await self.client.get(
            "/propertyapi/v1.0.0/property/snapshot",
            params=params,
        )
        response.raise_for_status()
        data = response.json()
        
        for prop in data.get("property", [])[:limit]:
            yield self._to_raw_record(prop)
    
    def _to_raw_record(self, data: dict) -> RawPropertyRecord:
        """Convert ATTOM response to RawPropertyRecord."""
        address = data.get("address", {})
        location = data.get("location", {})
        
        return RawPropertyRecord(
            source_system="attom",
            source_type="property_records",
            source_record_id=str(data.get("identifier", {}).get("attomId", "")),
            extraction_timestamp=datetime.utcnow(),
            raw_data=data,
            parcel_id=data.get("identifier", {}).get("apn"),
            address_raw=f"{address.get('line1', '')} {address.get('line2', '')}".strip(),
            latitude=location.get("latitude"),
            longitude=location.get("longitude"),
        )
    
    def get_coverage_info(self) -> dict:
        return {
            "provider": "ATTOM",
            "coverage": "155M+ US properties",
            "data_types": ["ownership", "valuation", "tax", "title", "building"],
            "update_frequency": "monthly",
        }
```

### S4: Census Adapter (Free)
Create `api/app/services/ingestion/providers/census.py`.

```python
# api/app/services/ingestion/providers/census.py
import httpx
from datetime import datetime
from app.services.ingestion.base import ProviderAdapter, RawPropertyRecord

class CensusAdapter(ProviderAdapter):
    """Adapter for US Census Bureau ACS data (free)."""
    
    name = "census"
    source_type = "demographics"
    base_url = "https://api.census.gov/data"
    
    def __init__(self, api_key: str | None = None):
        super().__init__(api_key)  # Census API key is optional but recommended
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def fetch_demographics(
        self,
        state_fips: str,
        county_fips: str | None = None,
        tract: str | None = None,
    ) -> dict:
        """Fetch ACS demographics for a geography."""
        
        # ACS 5-year estimates
        year = 2023
        dataset = f"{year}/acs/acs5"
        
        # Variables to fetch
        variables = [
            "B01003_001E",  # Total population
            "B19013_001E",  # Median household income
            "B25077_001E",  # Median home value
            "B25064_001E",  # Median gross rent
            "B01002_001E",  # Median age
        ]
        
        # Build geography
        geo = f"state:{state_fips}"
        if county_fips:
            geo = f"county:{county_fips}&in=state:{state_fips}"
        if tract:
            geo = f"tract:{tract}&in=state:{state_fips}&in=county:{county_fips}"
        
        url = f"{self.base_url}/{dataset}"
        params = {
            "get": ",".join(variables),
            "for": geo,
        }
        if self.api_key:
            params["key"] = self.api_key
        
        response = await self.client.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        # Parse response (first row is headers)
        if len(data) > 1:
            headers = data[0]
            values = data[1]
            return dict(zip(headers, values))
        
        return {}
    
    async def fetch_property(self, property_id: str) -> RawPropertyRecord | None:
        """Not applicable for Census - use fetch_demographics instead."""
        return None
    
    async def fetch_by_address(self, *args, **kwargs) -> RawPropertyRecord | None:
        return None
    
    async def fetch_batch(self, property_ids: list[str]) -> list[RawPropertyRecord]:
        return []
    
    async def stream_region(self, *args, **kwargs):
        yield None  # Not applicable
    
    def get_coverage_info(self) -> dict:
        return {
            "provider": "US Census Bureau",
            "coverage": "Nationwide (US)",
            "data_types": ["demographics", "income", "housing"],
            "update_frequency": "annual (ACS 5-year)",
            "cost": "free",
        }
```

### S5: FEMA Adapter (Free)
Create `api/app/services/ingestion/providers/fema.py`.

```python
# api/app/services/ingestion/providers/fema.py
import httpx
from datetime import datetime
from app.services.ingestion.base import ProviderAdapter, RawPropertyRecord

class FEMAAdapter(ProviderAdapter):
    """Adapter for FEMA flood zone data (free)."""
    
    name = "fema"
    source_type = "flood_zones"
    base_url = "https://hazards.fema.gov/gis/nfhl/rest/services"
    
    def __init__(self, api_key: str | None = None):
        super().__init__(api_key)  # No API key required
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def get_flood_zone(self, lat: float, lng: float) -> dict:
        """Get flood zone for a coordinate."""
        
        # Query FEMA National Flood Hazard Layer (NFHL)
        url = f"{self.base_url}/public/NFHL/MapServer/28/query"
        
        params = {
            "geometry": f"{lng},{lat}",
            "geometryType": "esriGeometryPoint",
            "spatialRel": "esriSpatialRelIntersects",
            "outFields": "FLD_ZONE,ZONE_SUBTY,SFHA_TF,STATIC_BFE",
            "returnGeometry": "false",
            "f": "json",
        }
        
        response = await self.client.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        features = data.get("features", [])
        if features:
            attrs = features[0].get("attributes", {})
            return {
                "flood_zone": attrs.get("FLD_ZONE"),
                "zone_subtype": attrs.get("ZONE_SUBTY"),
                "in_sfha": attrs.get("SFHA_TF") == "T",  # Special Flood Hazard Area
                "base_flood_elevation": attrs.get("STATIC_BFE"),
            }
        
        return {
            "flood_zone": "X",  # Default to minimal risk
            "zone_subtype": None,
            "in_sfha": False,
            "base_flood_elevation": None,
        }
    
    async def fetch_property(self, property_id: str) -> RawPropertyRecord | None:
        return None
    
    async def fetch_by_address(self, *args, **kwargs) -> RawPropertyRecord | None:
        return None
    
    async def fetch_batch(self, property_ids: list[str]) -> list[RawPropertyRecord]:
        return []
    
    async def stream_region(self, *args, **kwargs):
        yield None
    
    def get_coverage_info(self) -> dict:
        return {
            "provider": "FEMA",
            "coverage": "Nationwide (US)",
            "data_types": ["flood_zones", "flood_risk"],
            "update_frequency": "varies by region",
            "cost": "free",
        }
```

### S6: Address Normalization Service
Create `api/app/services/address.py` for USPS standardization.

```python
# api/app/services/address.py
import re
from dataclasses import dataclass
from typing import Optional
import usaddress

# Street suffix standardization
STREET_SUFFIXES = {
    "avenue": "Ave", "ave": "Ave",
    "boulevard": "Blvd", "blvd": "Blvd",
    "circle": "Cir", "cir": "Cir",
    "court": "Ct", "ct": "Ct",
    "drive": "Dr", "dr": "Dr",
    "highway": "Hwy", "hwy": "Hwy",
    "lane": "Ln", "ln": "Ln",
    "parkway": "Pkwy", "pkwy": "Pkwy",
    "place": "Pl", "pl": "Pl",
    "road": "Rd", "rd": "Rd",
    "street": "St", "st": "St",
    "terrace": "Ter", "ter": "Ter",
    "trail": "Trl", "trl": "Trl",
    "way": "Way",
}

DIRECTIONALS = {
    "north": "N", "n": "N",
    "south": "S", "s": "S",
    "east": "E", "e": "E",
    "west": "W", "w": "W",
    "northeast": "NE", "ne": "NE",
    "northwest": "NW", "nw": "NW",
    "southeast": "SE", "se": "SE",
    "southwest": "SW", "sw": "SW",
}

UNIT_TYPES = {
    "apartment": "Apt", "apt": "Apt",
    "suite": "Ste", "ste": "Ste",
    "unit": "Unit",
    "floor": "Fl", "fl": "Fl",
    "#": "Apt",
}

@dataclass
class NormalizedAddress:
    street_number: str | None
    street_name: str | None
    street_suffix: str | None
    street_direction: str | None
    unit_type: str | None
    unit_number: str | None
    city: str | None
    state: str | None
    zip_code: str | None
    zip4: str | None
    street_address: str | None
    formatted_address: str | None
    confidence: float

def normalize(raw_address: str) -> NormalizedAddress:
    """
    Normalize a raw address string to USPS standard format.
    
    Uses usaddress library for parsing, then applies USPS standardization.
    """
    if not raw_address:
        return NormalizedAddress(
            street_number=None, street_name=None, street_suffix=None,
            street_direction=None, unit_type=None, unit_number=None,
            city=None, state=None, zip_code=None, zip4=None,
            street_address=None, formatted_address=None, confidence=0.0,
        )
    
    try:
        # Parse with usaddress
        parsed, address_type = usaddress.tag(raw_address)
    except usaddress.RepeatedLabelError:
        # Fallback parsing
        parsed = {}
        address_type = "Unknown"
    
    # Extract and standardize components
    street_number = parsed.get("AddressNumber", "").strip()
    
    # Street name (combine parts)
    street_name_parts = []
    for key in ["StreetNamePreDirectional", "StreetNamePreModifier", 
                "StreetNamePreType", "StreetName"]:
        if key in parsed:
            street_name_parts.append(parsed[key])
    street_name = " ".join(street_name_parts).strip()
    
    # Street suffix
    street_suffix = parsed.get("StreetNamePostType", "").lower()
    street_suffix = STREET_SUFFIXES.get(street_suffix, street_suffix.title())
    
    # Direction
    direction = parsed.get("StreetNamePostDirectional", "").lower()
    direction = DIRECTIONALS.get(direction, direction.upper() if direction else None)
    
    # Unit
    unit_type = parsed.get("OccupancyType", "").lower()
    unit_type = UNIT_TYPES.get(unit_type, unit_type.title() if unit_type else None)
    unit_number = parsed.get("OccupancyIdentifier", "").strip()
    
    # Location
    city = parsed.get("PlaceName", "").title()
    state = parsed.get("StateName", "").upper()
    zip_code = parsed.get("ZipCode", "")[:5] if parsed.get("ZipCode") else None
    zip4 = parsed.get("ZipCode", "")[6:10] if len(parsed.get("ZipCode", "")) > 5 else None
    
    # Build formatted addresses
    street_parts = [street_number, street_name, street_suffix]
    if direction:
        street_parts.append(direction)
    street_address = " ".join(p for p in street_parts if p)
    
    if unit_type and unit_number:
        street_address += f" {unit_type} {unit_number}"
    
    formatted_parts = [street_address]
    if city:
        formatted_parts.append(city)
    if state:
        formatted_parts[-1] += ","
        formatted_parts.append(state)
    if zip_code:
        formatted_parts.append(zip_code)
    
    formatted_address = " ".join(formatted_parts)
    
    # Calculate confidence
    confidence = 0.0
    if street_number:
        confidence += 0.2
    if street_name:
        confidence += 0.3
    if city:
        confidence += 0.2
    if state:
        confidence += 0.2
    if zip_code:
        confidence += 0.1
    
    return NormalizedAddress(
        street_number=street_number or None,
        street_name=street_name or None,
        street_suffix=street_suffix or None,
        street_direction=direction,
        unit_type=unit_type,
        unit_number=unit_number or None,
        city=city or None,
        state=state if len(state) == 2 else None,
        zip_code=zip_code,
        zip4=zip4,
        street_address=street_address or None,
        formatted_address=formatted_address or None,
        confidence=confidence,
    )
```

### S7: Geocoding Service
Create `api/app/services/geocoding.py` with multiple provider fallback.

```python
# api/app/services/geocoding.py
import httpx
from dataclasses import dataclass
from typing import Optional
from app.config import settings

@dataclass
class GeocodingResult:
    latitude: float
    longitude: float
    accuracy: str  # rooftop, parcel, street, city
    source: str
    confidence: float

class GeocodingService:
    """Geocoding with multiple provider fallback."""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=10.0)
    
    async def geocode(
        self,
        address: str,
        city: str | None = None,
        state: str | None = None,
        zip_code: str | None = None,
    ) -> GeocodingResult | None:
        """
        Geocode an address using multiple providers with fallback.
        
        Tries providers in order: Census, Nominatim, Google (if configured).
        """
        full_address = address
        if city:
            full_address += f", {city}"
        if state:
            full_address += f", {state}"
        if zip_code:
            full_address += f" {zip_code}"
        
        # Try Census Geocoder first (free, high quality for US)
        result = await self._census_geocode(full_address)
        if result:
            return result
        
        # Fallback to Nominatim (free, global)
        result = await self._nominatim_geocode(full_address)
        if result:
            return result
        
        # Could add Google Maps, HERE, etc. as paid fallbacks
        
        return None
    
    async def _census_geocode(self, address: str) -> GeocodingResult | None:
        """Use Census Bureau geocoder (free, US only)."""
        try:
            url = "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"
            params = {
                "address": address,
                "benchmark": "Public_AR_Current",
                "format": "json",
            }
            
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            matches = data.get("result", {}).get("addressMatches", [])
            if matches:
                match = matches[0]
                coords = match.get("coordinates", {})
                
                return GeocodingResult(
                    latitude=coords.get("y"),
                    longitude=coords.get("x"),
                    accuracy="rooftop",
                    source="census",
                    confidence=0.95,
                )
        except Exception:
            pass
        
        return None
    
    async def _nominatim_geocode(self, address: str) -> GeocodingResult | None:
        """Use OpenStreetMap Nominatim (free, global)."""
        try:
            url = "https://nominatim.openstreetmap.org/search"
            params = {
                "q": address,
                "format": "json",
                "limit": 1,
            }
            headers = {"User-Agent": "ParcelData/0.1"}
            
            response = await self.client.get(url, params=params, headers=headers)
            response.raise_for_status()
            results = response.json()
            
            if results:
                result = results[0]
                return GeocodingResult(
                    latitude=float(result["lat"]),
                    longitude=float(result["lon"]),
                    accuracy="street",
                    source="nominatim",
                    confidence=0.8,
                )
        except Exception:
            pass
        
        return None
    
    async def reverse_geocode(
        self,
        lat: float,
        lng: float,
    ) -> dict | None:
        """Reverse geocode coordinates to address."""
        try:
            url = "https://nominatim.openstreetmap.org/reverse"
            params = {
                "lat": lat,
                "lon": lng,
                "format": "json",
            }
            headers = {"User-Agent": "ParcelData/0.1"}
            
            response = await self.client.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            return {
                "address": data.get("display_name"),
                "house_number": data.get("address", {}).get("house_number"),
                "road": data.get("address", {}).get("road"),
                "city": data.get("address", {}).get("city"),
                "state": data.get("address", {}).get("state"),
                "postcode": data.get("address", {}).get("postcode"),
            }
        except Exception:
            return None
```

### S8: Entity Resolution Pipeline
Create `api/app/services/entity_resolution.py`.

```python
# api/app/services/entity_resolution.py
import hashlib
from dataclasses import dataclass
from typing import Optional
from jellyfish import jaro_winkler_similarity
from app.services.address import normalize, NormalizedAddress
from app.services.geocoding import GeocodingService
import math

@dataclass
class MatchCandidate:
    property_id: str
    confidence: float
    match_type: str  # exact, fuzzy, geocode
    matched_fields: list[str]

@dataclass
class EntityResolutionResult:
    canonical_id: str | None
    confidence: float
    matches: list[MatchCandidate]
    action: str  # auto_merge, review, keep_separate

class EntityResolutionService:
    """
    Cross-source property deduplication.
    
    Pipeline stages:
    1. Blocking - Geohash/address to reduce comparison space
    2. Pairwise comparison - Score field similarity
    3. Classification - Determine merge action
    4. Clustering - Assign canonical IDs
    """
    
    CONFIDENCE_AUTO_MERGE = 0.90
    CONFIDENCE_REVIEW = 0.70
    CONFIDENCE_SEPARATE = 0.50
    
    def __init__(self, db):
        self.db = db
        self.geocoder = GeocodingService()
    
    async def resolve(
        self,
        address: str | None = None,
        lat: float | None = None,
        lng: float | None = None,
        parcel_id: str | None = None,
        source_record_id: str | None = None,
    ) -> EntityResolutionResult:
        """
        Resolve a property to its canonical entity.
        """
        candidates = []
        
        # 1. BLOCKING: Find potential matches
        if parcel_id:
            # Exact parcel ID match is highest confidence
            exact_matches = await self._find_by_parcel_id(parcel_id)
            candidates.extend(exact_matches)
        
        if address:
            # Normalized address blocking
            normalized = normalize(address)
            address_matches = await self._find_by_address(normalized)
            candidates.extend(address_matches)
        
        if lat and lng:
            # Geohash blocking (properties within 100m)
            geo_matches = await self._find_by_location(lat, lng, radius_meters=100)
            candidates.extend(geo_matches)
        
        if not candidates:
            return EntityResolutionResult(
                canonical_id=None,
                confidence=0.0,
                matches=[],
                action="keep_separate",
            )
        
        # 2. PAIRWISE COMPARISON: Score each candidate
        scored_candidates = []
        for candidate in candidates:
            score = await self._score_match(
                address=address,
                lat=lat,
                lng=lng,
                parcel_id=parcel_id,
                candidate=candidate,
            )
            if score.confidence > 0.3:
                scored_candidates.append(score)
        
        # 3. CLASSIFICATION: Determine action
        scored_candidates.sort(key=lambda x: x.confidence, reverse=True)
        
        if not scored_candidates:
            return EntityResolutionResult(
                canonical_id=None,
                confidence=0.0,
                matches=[],
                action="keep_separate",
            )
        
        best_match = scored_candidates[0]
        
        if best_match.confidence >= self.CONFIDENCE_AUTO_MERGE:
            action = "auto_merge"
        elif best_match.confidence >= self.CONFIDENCE_REVIEW:
            action = "review"
        else:
            action = "keep_separate"
        
        return EntityResolutionResult(
            canonical_id=best_match.property_id if action == "auto_merge" else None,
            confidence=best_match.confidence,
            matches=scored_candidates[:5],
            action=action,
        )
    
    async def _find_by_parcel_id(self, parcel_id: str) -> list[dict]:
        """Find properties by parcel ID."""
        from sqlalchemy import select
        from app.models import Property
        
        stmt = select(Property).where(Property.county_apn == parcel_id).limit(5)
        result = await self.db.execute(stmt)
        return [{"property": p, "match_type": "parcel_id"} for p in result.scalars()]
    
    async def _find_by_address(self, normalized: NormalizedAddress) -> list[dict]:
        """Find properties by normalized address."""
        from sqlalchemy import select
        from app.models import Property, Address
        
        if not normalized.street_address:
            return []
        
        stmt = (
            select(Property)
            .join(Address)
            .where(
                Address.city == normalized.city,
                Address.state == normalized.state,
            )
            .limit(20)
        )
        result = await self.db.execute(stmt)
        return [{"property": p, "match_type": "address"} for p in result.scalars()]
    
    async def _find_by_location(
        self,
        lat: float,
        lng: float,
        radius_meters: float,
    ) -> list[dict]:
        """Find properties by location."""
        from sqlalchemy import select
        from geoalchemy2.functions import ST_DWithin, ST_MakePoint, ST_SetSRID
        from app.models import Property
        
        point = ST_SetSRID(ST_MakePoint(lng, lat), 4326)
        
        stmt = (
            select(Property)
            .where(ST_DWithin(Property.location, point, radius_meters))
            .limit(10)
        )
        result = await self.db.execute(stmt)
        return [{"property": p, "match_type": "geocode"} for p in result.scalars()]
    
    async def _score_match(
        self,
        address: str | None,
        lat: float | None,
        lng: float | None,
        parcel_id: str | None,
        candidate: dict,
    ) -> MatchCandidate:
        """Score similarity between input and candidate."""
        prop = candidate["property"]
        matched_fields = []
        scores = []
        
        # Parcel ID match (highest weight)
        if parcel_id and prop.county_apn:
            if parcel_id == prop.county_apn:
                scores.append(1.0)
                matched_fields.append("parcel_id")
        
        # Address similarity
        if address and prop.address:
            normalized_input = normalize(address)
            normalized_db = normalize(prop.address.formatted_address or "")
            
            if normalized_input.formatted_address and normalized_db.formatted_address:
                sim = jaro_winkler_similarity(
                    normalized_input.formatted_address.lower(),
                    normalized_db.formatted_address.lower(),
                )
                if sim > 0.85:
                    scores.append(sim)
                    matched_fields.append("address")
        
        # Location proximity
        if lat and lng and prop.address:
            if prop.address.latitude and prop.address.longitude:
                distance = self._haversine_distance(
                    lat, lng,
                    prop.address.latitude, prop.address.longitude,
                )
                if distance < 10:  # Within 10 meters
                    scores.append(0.95)
                    matched_fields.append("location")
                elif distance < 50:
                    scores.append(0.80)
                    matched_fields.append("location")
        
        confidence = sum(scores) / len(scores) if scores else 0.0
        
        return MatchCandidate(
            property_id=prop.id,
            confidence=confidence,
            match_type=candidate["match_type"],
            matched_fields=matched_fields,
        )
    
    def _haversine_distance(
        self,
        lat1: float, lon1: float,
        lat2: float, lon2: float,
    ) -> float:
        """Calculate distance between two points in meters."""
        R = 6371000  # Earth radius in meters
        
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)
        
        a = (
            math.sin(delta_phi / 2) ** 2 +
            math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
```

### S9: Data Quality Scoring Service
Create `api/app/services/quality.py`.

```python
# api/app/services/quality.py
from datetime import datetime, timedelta
from dataclasses import dataclass

@dataclass
class DataQualityScore:
    score: float  # Overall 0-1
    completeness: float
    accuracy: float
    consistency: float
    timeliness: float
    validity: float
    uniqueness: float
    freshness_hours: int
    confidence: str  # low, medium, high

REQUIRED_FIELDS = [
    "address", "city", "state", "zip_code",
    "latitude", "longitude",
    "lot_sqft", "property_type",
]

OPTIONAL_FIELDS = [
    "bedrooms", "bathrooms", "sqft", "year_built",
    "assessed_value", "estimated_value",
    "zoning", "owner_name",
]

def calculate_quality_score(
    property_data: dict,
    source_timestamp: datetime | None = None,
    duplicate_check: bool = False,
) -> DataQualityScore:
    """
    Calculate data quality score for a property record.
    
    Formula:
    score = (completeness × 0.25) + (accuracy × 0.25) + 
            (consistency × 0.20) + (timeliness × 0.15) + 
            (validity × 0.10) + (uniqueness × 0.05)
    """
    
    # Completeness: What fraction of required/optional fields are present?
    required_present = sum(
        1 for f in REQUIRED_FIELDS
        if property_data.get(f) is not None
    )
    optional_present = sum(
        1 for f in OPTIONAL_FIELDS
        if property_data.get(f) is not None
    )
    
    completeness = (
        (required_present / len(REQUIRED_FIELDS)) * 0.7 +
        (optional_present / len(OPTIONAL_FIELDS)) * 0.3
    )
    
    # Accuracy: Validate field formats and ranges
    accuracy_checks = []
    
    # ZIP code format
    zip_code = property_data.get("zip_code", "")
    if zip_code:
        accuracy_checks.append(1.0 if len(zip_code) == 5 and zip_code.isdigit() else 0.5)
    
    # State is valid 2-letter code
    state = property_data.get("state", "")
    if state:
        accuracy_checks.append(1.0 if len(state) == 2 and state.isalpha() else 0.5)
    
    # Year built is reasonable
    year_built = property_data.get("year_built")
    if year_built:
        accuracy_checks.append(1.0 if 1800 <= year_built <= 2030 else 0.5)
    
    # Coordinates are valid
    lat = property_data.get("latitude")
    lng = property_data.get("longitude")
    if lat and lng:
        accuracy_checks.append(1.0 if -90 <= lat <= 90 and -180 <= lng <= 180 else 0.0)
    
    accuracy = sum(accuracy_checks) / len(accuracy_checks) if accuracy_checks else 0.8
    
    # Consistency: Cross-field validation
    consistency_checks = []
    
    # Lot sqft > building sqft
    lot_sqft = property_data.get("lot_sqft", 0) or 0
    building_sqft = property_data.get("sqft", 0) or 0
    if lot_sqft and building_sqft:
        consistency_checks.append(1.0 if lot_sqft >= building_sqft else 0.5)
    
    # Assessed value reasonable given sqft
    assessed = property_data.get("assessed_value", 0) or 0
    if assessed and building_sqft:
        price_per_sqft = assessed / building_sqft
        consistency_checks.append(1.0 if 50 <= price_per_sqft <= 2000 else 0.7)
    
    consistency = sum(consistency_checks) / len(consistency_checks) if consistency_checks else 0.85
    
    # Timeliness: How fresh is the data?
    freshness_hours = 0
    if source_timestamp:
        age = datetime.utcnow() - source_timestamp
        freshness_hours = int(age.total_seconds() / 3600)
        
        if freshness_hours < 24:
            timeliness = 1.0
        elif freshness_hours < 168:  # 1 week
            timeliness = 0.9
        elif freshness_hours < 720:  # 30 days
            timeliness = 0.8
        elif freshness_hours < 2160:  # 90 days
            timeliness = 0.7
        else:
            timeliness = 0.5
    else:
        timeliness = 0.7  # Unknown age
    
    # Validity: Schema compliance
    validity = 0.95  # Assume valid if we got this far
    
    # Uniqueness: Is this a duplicate?
    uniqueness = 1.0 if not duplicate_check else 0.95
    
    # Calculate weighted score
    score = (
        completeness * 0.25 +
        accuracy * 0.25 +
        consistency * 0.20 +
        timeliness * 0.15 +
        validity * 0.10 +
        uniqueness * 0.05
    )
    
    # Determine confidence level
    if score >= 0.85:
        confidence = "high"
    elif score >= 0.70:
        confidence = "medium"
    else:
        confidence = "low"
    
    return DataQualityScore(
        score=round(score, 3),
        completeness=round(completeness, 3),
        accuracy=round(accuracy, 3),
        consistency=round(consistency, 3),
        timeliness=round(timeliness, 3),
        validity=round(validity, 3),
        uniqueness=round(uniqueness, 3),
        freshness_hours=freshness_hours,
        confidence=confidence,
    )
```

### S10: Data Ingestion Pipeline
Create `api/app/services/ingestion/pipeline.py`.

```python
# api/app/services/ingestion/pipeline.py
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Property, Address, Building, Valuation
from app.services.ingestion.base import RawPropertyRecord
from app.services.address import normalize
from app.services.geocoding import GeocodingService
from app.services.entity_resolution import EntityResolutionService
from app.services.quality import calculate_quality_score
import hashlib
import structlog

logger = structlog.get_logger()

class IngestionPipeline:
    """
    ETL pipeline for property data ingestion.
    
    Stages:
    1. Extract - Fetch from provider
    2. Transform - Normalize, enrich, deduplicate
    3. Load - Upsert to database
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.geocoder = GeocodingService()
        self.entity_resolver = EntityResolutionService(db)
    
    async def process_record(self, raw: RawPropertyRecord) -> str | None:
        """
        Process a single raw record through the pipeline.
        
        Returns the property ID if successful, None otherwise.
        """
        try:
            # 1. TRANSFORM: Normalize address
            address = None
            if raw.address_raw:
                normalized = normalize(raw.address_raw)
                address = normalized
            
            # 2. TRANSFORM: Geocode if needed
            lat, lng = raw.latitude, raw.longitude
            if (not lat or not lng) and address:
                geo_result = await self.geocoder.geocode(
                    address=address.formatted_address or "",
                )
                if geo_result:
                    lat, lng = geo_result.latitude, geo_result.longitude
            
            # 3. TRANSFORM: Entity resolution
            entity_result = await self.entity_resolver.resolve(
                address=address.formatted_address if address else None,
                lat=lat,
                lng=lng,
                parcel_id=raw.parcel_id,
                source_record_id=raw.source_record_id,
            )
            
            # 4. Generate property ID
            if entity_result.canonical_id and entity_result.action == "auto_merge":
                property_id = entity_result.canonical_id
            else:
                property_id = self._generate_property_id(raw, address)
            
            # 5. TRANSFORM: Calculate quality score
            property_data = self._extract_property_data(raw.raw_data)
            quality = calculate_quality_score(
                property_data,
                source_timestamp=raw.extraction_timestamp,
            )
            
            # 6. LOAD: Upsert to database
            await self._upsert_property(
                property_id=property_id,
                raw=raw,
                address=address,
                lat=lat,
                lng=lng,
                quality=quality,
            )
            
            logger.info(
                "Processed property",
                property_id=property_id,
                source=raw.source_system,
                quality_score=quality.score,
            )
            
            return property_id
            
        except Exception as e:
            logger.error(
                "Failed to process record",
                source=raw.source_system,
                source_id=raw.source_record_id,
                error=str(e),
            )
            return None
    
    def _generate_property_id(
        self,
        raw: RawPropertyRecord,
        address,
    ) -> str:
        """Generate a Dharma property ID."""
        # Format: {STATE}-{COUNTY}-{HASH}
        state = address.state if address else "XX"
        
        # Create hash from source ID or address
        hash_input = f"{raw.source_system}:{raw.source_record_id}"
        if raw.parcel_id:
            hash_input = raw.parcel_id
        
        hash_suffix = hashlib.md5(hash_input.encode()).hexdigest()[:10].upper()
        
        return f"{state}-UNKNOWN-{hash_suffix}"
    
    def _extract_property_data(self, raw_data: dict) -> dict:
        """Extract property fields from raw data (provider-specific)."""
        # This should be customized per provider
        return {
            "address": raw_data.get("address"),
            "city": raw_data.get("city"),
            "state": raw_data.get("state"),
            "zip_code": raw_data.get("zip"),
            "latitude": raw_data.get("lat"),
            "longitude": raw_data.get("lng"),
            "lot_sqft": raw_data.get("lot_sqft"),
            "property_type": raw_data.get("property_type"),
            "bedrooms": raw_data.get("bedrooms"),
            "bathrooms": raw_data.get("bathrooms"),
            "sqft": raw_data.get("sqft"),
            "year_built": raw_data.get("year_built"),
            "assessed_value": raw_data.get("assessed_value"),
        }
    
    async def _upsert_property(
        self,
        property_id: str,
        raw: RawPropertyRecord,
        address,
        lat: float | None,
        lng: float | None,
        quality,
    ) -> None:
        """Insert or update property in database."""
        from sqlalchemy import select
        from geoalchemy2.functions import ST_MakePoint, ST_SetSRID
        
        # Check if exists
        stmt = select(Property).where(Property.id == property_id)
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if existing:
            # Update
            existing.source_system = raw.source_system
            existing.quality_score = quality.score
            existing.quality_completeness = quality.completeness
            existing.quality_accuracy = quality.accuracy
            existing.quality_consistency = quality.consistency
            existing.quality_timeliness = quality.timeliness
            existing.quality_validity = quality.validity
            existing.quality_uniqueness = quality.uniqueness
            existing.freshness_hours = quality.freshness_hours
            existing.updated_at = datetime.utcnow()
        else:
            # Insert
            prop = Property(
                id=property_id,
                source_system=raw.source_system,
                source_type=raw.source_type,
                source_record_id=raw.source_record_id,
                quality_score=quality.score,
                quality_completeness=quality.completeness,
                quality_accuracy=quality.accuracy,
                quality_consistency=quality.consistency,
                quality_timeliness=quality.timeliness,
                quality_validity=quality.validity,
                quality_uniqueness=quality.uniqueness,
                freshness_hours=quality.freshness_hours,
            )
            
            # Set location if available
            if lat and lng:
                prop.location = f"SRID=4326;POINT({lng} {lat})"
            
            self.db.add(prop)
        
        await self.db.commit()
```

### S11: Batch Import CLI
Create `api/app/cli/import_data.py` for command-line imports.

```python
# api/app/cli/import_data.py
import asyncio
import argparse
from app.database.connection import async_session_maker
from app.services.ingestion.pipeline import IngestionPipeline
from app.services.ingestion.providers.regrid import RegridAdapter
from app.services.ingestion.providers.attom import ATTOMAdapter
from app.services.ingestion.providers.census import CensusAdapter

async def import_region(
    provider: str,
    state: str,
    county: str | None = None,
    limit: int | None = None,
    dry_run: bool = False,
):
    """Import properties for a region from a provider."""
    
    # Get provider adapter
    if provider == "regrid":
        adapter = RegridAdapter()
    elif provider == "attom":
        adapter = ATTOMAdapter()
    else:
        print(f"Unknown provider: {provider}")
        return
    
    print(f"Importing from {provider} for {state}" + (f"/{county}" if county else ""))
    
    async with async_session_maker() as db:
        pipeline = IngestionPipeline(db)
        
        count = 0
        errors = 0
        
        async for raw_record in adapter.stream_region(state, county, limit):
            if raw_record is None:
                continue
            
            if dry_run:
                print(f"Would process: {raw_record.source_record_id}")
            else:
                result = await pipeline.process_record(raw_record)
                if result:
                    count += 1
                else:
                    errors += 1
            
            if limit and count >= limit:
                break
    
    print(f"Imported {count} properties, {errors} errors")

def main():
    parser = argparse.ArgumentParser(description="Import property data")
    parser.add_argument("--provider", required=True, help="Data provider (regrid, attom, census)")
    parser.add_argument("--state", required=True, help="State code (TX, CA, etc.)")
    parser.add_argument("--county", help="County name (optional)")
    parser.add_argument("--limit", type=int, help="Max records to import")
    parser.add_argument("--dry-run", action="store_true", help="Don't actually import")
    
    args = parser.parse_args()
    
    asyncio.run(import_region(
        provider=args.provider,
        state=args.state,
        county=args.county,
        limit=args.limit,
        dry_run=args.dry_run,
    ))

if __name__ == "__main__":
    main()
```

### S12: Provider Adapter Package
Create `api/app/services/ingestion/providers/__init__.py`.

```python
# api/app/services/ingestion/providers/__init__.py
from .regrid import RegridAdapter
from .attom import ATTOMAdapter
from .census import CensusAdapter
from .fema import FEMAAdapter

__all__ = ["RegridAdapter", "ATTOMAdapter", "CensusAdapter", "FEMAAdapter"]
```

---

## Acceptance Criteria
- Provider adapters work for Regrid, ATTOM, Census, FEMA
- Address normalization produces USPS-standard format
- Geocoding returns coordinates with accuracy info
- Entity resolution identifies duplicates with confidence scores
- Data quality scores calculated for all records
- Pipeline processes records and upserts to database
- CLI tool can import regions with dry-run mode
- All new code passes `ruff check` and `mypy --strict`
