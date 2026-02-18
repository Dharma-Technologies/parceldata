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

## Current Stage: P10-07-sdk-docs

# P10-07: Python SDK & Documentation

**Phase 7 — SDK, Documentation & Agent Readability**

Build the Python SDK, API documentation, and agent-readable endpoints.

---

## Stories

### Story 1: Python SDK Package Structure
**Directory:** `sdk/`

Create a pip-installable Python SDK:

```
sdk/
├── parceldata/
│   ├── __init__.py          # Version, top-level imports
│   ├── client.py            # ParcelDataClient class
│   ├── models.py            # Pydantic response models
│   ├── exceptions.py        # Custom exceptions
│   ├── types.py             # Type definitions
│   └── utils.py             # Helpers
├── tests/
│   ├── test_client.py
│   ├── test_models.py
│   └── conftest.py
├── setup.py
├── pyproject.toml
├── README.md
└── LICENSE
```

**Requirements:**
- `httpx` for async HTTP
- `pydantic` for models
- Python 3.9+ compatible
- Type hints throughout

---

### Story 2: ParcelDataClient Implementation
**File:** `sdk/parceldata/client.py`

```python
class ParcelDataClient:
    def __init__(self, api_key: str, base_url: str = "https://api.parceldata.ai/v1"):
        ...

    async def property_lookup(self, parcel_id: str, tier: str = "standard") -> Property:
        """Look up a single property by parcel ID."""

    async def property_search(self, query: PropertySearchQuery) -> SearchResults:
        """Search properties with filters."""

    async def get_comps(self, parcel_id: str, radius_miles: float = 1.0, limit: int = 10) -> list[Property]:
        """Get comparable properties."""

    async def batch_lookup(self, parcel_ids: list[str]) -> BatchResults:
        """Batch property lookup (up to 100)."""

    async def geocode(self, address: str) -> GeocodingResult:
        """Geocode an address to lat/lng + parcel."""

    def property_lookup_sync(self, parcel_id: str, tier: str = "standard") -> Property:
        """Synchronous wrapper."""
```

Both async and sync methods. Automatic retry with exponential backoff. Rate limit handling.

---

### Story 3: SDK Response Models
**File:** `sdk/parceldata/models.py`

Pydantic models matching API responses:
- `Property` — full property record
- `PropertySummary` — compact version
- `SearchResults` — paginated results
- `BatchResults` — batch response
- `GeocodingResult` — geocoding response
- `DataQuality` — quality scores
- `Provenance` — data source metadata

Token tier support: `micro`, `standard`, `full`

---

### Story 4: SDK Error Handling
**File:** `sdk/parceldata/exceptions.py`

```python
class ParcelDataError(Exception): ...
class AuthenticationError(ParcelDataError): ...
class RateLimitError(ParcelDataError): ...
class NotFoundError(ParcelDataError): ...
class ValidationError(ParcelDataError): ...
class QuotaExceededError(ParcelDataError): ...
```

---

### Story 5: SDK Tests
**Directory:** `sdk/tests/`

- Test client initialization
- Test all endpoint methods (mocked responses)
- Test error handling
- Test retry logic
- Test sync wrappers
- Test model serialization

---

### Story 6: OpenAPI Specification
**File:** `api/app/openapi_config.py`

Configure FastAPI's auto-generated OpenAPI spec:
- Title: "ParcelData.ai API"
- Version: "1.0.0"
- Description with examples
- Tag grouping (Properties, Search, Batch, Auth, Admin)
- Response examples for every endpoint
- Error response schemas

Expose at `/v1/docs` (Swagger UI) and `/v1/redoc` (ReDoc).

---

### Story 7: /llms.txt Endpoint
**File:** `api/app/routes/agent_readable.py`

```
GET /llms.txt
```

Returns plain text description of the API optimized for LLM consumption:
```
# ParcelData.ai API

> Clean, universal real estate data for AI agents.

## Base URL
https://api.parceldata.ai/v1

## Authentication
API key via X-API-Key header or ?api_key= query parameter.

## Endpoints

### Property Lookup
GET /v1/properties/{parcel_id}
Returns property details. Use ?tier=micro|standard|full for token optimization.

### Property Search
GET /v1/properties/search?query={text}&lat={lat}&lng={lng}&radius={miles}
Search properties by text, location, or filters.

### Comparable Properties
GET /v1/properties/{parcel_id}/comps?radius=1.0&limit=10
Get comparable properties near a given property.

### Batch Lookup
POST /v1/properties/batch
Body: {"parcel_ids": ["ID1", "ID2", ...]}
Look up multiple properties (max 100 per request).

## MCP Server
Connect via MCP at mcp://api.parceldata.ai/v1
Tools: property_lookup, property_search, get_comps, batch_lookup
```

---

### Story 8: /.well-known/ai-plugin.json
**File:** `api/app/routes/agent_readable.py`

```json
{
  "schema_version": "v1",
  "name_for_human": "ParcelData.ai",
  "name_for_model": "parceldata",
  "description_for_human": "Clean, universal real estate data API",
  "description_for_model": "Access US property records, valuations, ownership, tax, zoning, and spatial data. Use for property lookups, comparable analysis, and batch data retrieval.",
  "auth": {
    "type": "service_http",
    "authorization_type": "bearer"
  },
  "api": {
    "type": "openapi",
    "url": "https://api.parceldata.ai/v1/openapi.json"
  }
}
```

---

### Story 9: JSON-LD Structured Data
**File:** `api/app/middleware/jsonld.py`

Add JSON-LD `<script type="application/ld+json">` to HTML responses:
- Organization schema for ParcelData.ai
- WebAPI schema describing the API
- DataCatalog schema for available datasets

---

### Story 10: Documentation README
**Files:** `README.md`, `docs/QUICKSTART.md`, `docs/API_REFERENCE.md`

Root README:
- What is ParcelData
- Quick start (3 lines: install, init, query)
- Link to full docs
- MIT license badge
- Status badges

QUICKSTART.md:
- Install SDK: `pip install parceldata`
- Get API key
- First query example
- MCP setup example

API_REFERENCE.md:
- All endpoints with curl examples
- Response format documentation
- Rate limits and quotas
- Error codes

---

## Acceptance Criteria
- [ ] `pip install -e sdk/` works
- [ ] All SDK tests pass
- [ ] `/llms.txt` returns valid agent-readable text
- [ ] `/.well-known/ai-plugin.json` returns valid plugin manifest
- [ ] OpenAPI spec is complete with examples
- [ ] README has working quick start
