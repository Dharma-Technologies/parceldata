"""Agent-readable endpoints for LLM crawlers and AI plugins."""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse

from app.middleware.jsonld import get_jsonld_script

router = APIRouter(tags=["Admin"])

LLMS_TXT = """\
# ParcelData.ai API

> Clean, universal real estate data for AI agents.

## Base URL
https://api.parceldata.ai/v1

## Authentication
API key via `Authorization: Bearer <key>` header or `X-API-Key: <key>` header.

Sign up: POST /v1/auth/signup with {"email": "you@example.com"}

## Response Tiers
Use `?detail=micro|standard|extended|full` to control response size.
- micro: ~500 tokens (ID, price, basic stats)
- standard: ~2000 tokens (full property details)
- extended: ~8000 tokens (property + market context)
- full: ~32000 tokens (everything + documents)

## Endpoints

### Property Lookup
GET /v1/properties/{parcel_id}?detail=standard
Returns property details including address, building, valuation, ownership, zoning.

### Address Lookup
GET /v1/properties/address/lookup?street=100+Congress+Ave&city=Austin&state=TX
Find property by address components.

### Coordinate Lookup
GET /v1/properties/coordinates/lookup?lat=30.2672&lng=-97.7431
Find property by latitude/longitude.

### Property Search
POST /v1/properties/search
Body: {"city": "Austin", "state": "TX", "bedrooms_min": 3, "limit": 25}
Search with filters: location, type, beds, baths, sqft, price, year.

### Batch Lookup
POST /v1/properties/batch
Body: {"property_ids": ["ID1", "ID2", ...], "detail": "standard"}
Look up multiple properties (max 100 per request).

### Comparable Properties
GET /v1/analytics/comparables?property_id=TX-TRAVIS-12345&radius=1.0&limit=10
Get comparable properties near a given property.

### Market Trends
GET /v1/analytics/market-trends?zip=78701&period=12m
Get market statistics for an area.

## Data Quality
Every response includes a `data_quality` object:
```json
{"score": 0.87, "confidence": "high", "freshness_hours": 12, "sources": ["travis_cad"]}
```

## Rate Limits
Free: 3,000/mo | Pro: 50,000/mo | Business: 500,000/mo | Enterprise: 10M/mo

## MCP Server
Connect via MCP at mcp://api.parceldata.ai/v1
Tools: property_lookup, property_search, get_comparables, get_market_trends,
check_zoning, get_permits, get_owner_portfolio, estimate_value,
check_development_feasibility

## SDK
pip install parceldata

```python
from parceldata import ParcelDataClient
client = ParcelDataClient("your-api-key")
prop = await client.property_lookup("TX-TRAVIS-12345")
```

## OpenAPI Spec
https://api.parceldata.ai/openapi.json
"""

AI_PLUGIN_MANIFEST = {
    "schema_version": "v1",
    "name_for_human": "ParcelData.ai",
    "name_for_model": "parceldata",
    "description_for_human": "Clean, universal real estate data API",
    "description_for_model": (
        "Access US property records, valuations, ownership, tax, zoning, "
        "and spatial data. Use for property lookups by parcel ID, address, "
        "or coordinates. Supports comparable analysis, market trends, "
        "batch retrieval (up to 100), and filtered search. Every response "
        "includes a data_quality score. Use ?detail=micro for token-efficient "
        "responses or ?detail=full for comprehensive data."
    ),
    "auth": {
        "type": "service_http",
        "authorization_type": "bearer",
    },
    "api": {
        "type": "openapi",
        "url": "https://api.parceldata.ai/openapi.json",
    },
    "logo_url": "https://parceldata.ai/logo.png",
    "contact_email": "hello@dharma.tech",
    "legal_info_url": "https://parceldata.ai/legal",
}


@router.get(
    "/llms.txt",
    response_class=PlainTextResponse,
    summary="LLM-readable API description",
    description="Plain text summary of the API optimized for LLM consumption.",
)
async def llms_txt() -> PlainTextResponse:
    """Return plain text API description for LLM crawlers."""
    return PlainTextResponse(content=LLMS_TXT, media_type="text/plain")


@router.get(
    "/.well-known/ai-plugin.json",
    response_class=JSONResponse,
    summary="AI plugin manifest",
    description="OpenAI-compatible plugin manifest for AI agent discovery.",
)
async def ai_plugin() -> JSONResponse:
    """Return AI plugin manifest for agent discovery."""
    return JSONResponse(content=AI_PLUGIN_MANIFEST)


@router.get(
    "/jsonld",
    response_class=HTMLResponse,
    summary="JSON-LD structured data",
    description="JSON-LD script tags for Organization, WebAPI, and DataCatalog.",
)
async def jsonld() -> HTMLResponse:
    """Return JSON-LD structured data as embeddable HTML."""
    return HTMLResponse(content=get_jsonld_script())
