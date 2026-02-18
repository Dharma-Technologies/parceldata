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

## Current Stage: P10-06-mcp-server

# PRD: P10-06 — MCP Server

## Overview
Build the TypeScript MCP server with all property tools: property_lookup, property_search, get_comparables, get_market_trends, check_zoning, get_permits, get_owner_portfolio, estimate_value, and check_development_feasibility.

---

## Stories

### S1: MCP Server Entry Point
Create `mcp/src/index.ts` as the main server entry point.

```typescript
// mcp/src/index.ts
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  ListToolsRequestSchema,
  CallToolRequestSchema,
  ErrorCode,
  McpError,
} from "@modelcontextprotocol/sdk/types.js";
import { propertyLookup } from "./tools/property-lookup.js";
import { propertySearch } from "./tools/property-search.js";
import { getComparables } from "./tools/get-comparables.js";
import { getMarketTrends } from "./tools/get-market-trends.js";
import { checkZoning } from "./tools/check-zoning.js";
import { getPermits } from "./tools/get-permits.js";
import { getOwnerPortfolio } from "./tools/get-owner-portfolio.js";
import { estimateValue } from "./tools/estimate-value.js";
import { checkDevelopmentFeasibility } from "./tools/check-development-feasibility.js";
import { TOOLS } from "./tools/definitions.js";

const server = new Server(
  {
    name: "parceldata",
    version: "0.1.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// List available tools
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: TOOLS,
  };
});

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {
      case "property_lookup":
        return await propertyLookup(args);
      case "property_search":
        return await propertySearch(args);
      case "get_comparables":
        return await getComparables(args);
      case "get_market_trends":
        return await getMarketTrends(args);
      case "check_zoning":
        return await checkZoning(args);
      case "get_permits":
        return await getPermits(args);
      case "get_owner_portfolio":
        return await getOwnerPortfolio(args);
      case "estimate_value":
        return await estimateValue(args);
      case "check_development_feasibility":
        return await checkDevelopmentFeasibility(args);
      default:
        throw new McpError(
          ErrorCode.MethodNotFound,
          `Unknown tool: ${name}`
        );
    }
  } catch (error) {
    if (error instanceof McpError) {
      throw error;
    }
    throw new McpError(
      ErrorCode.InternalError,
      `Tool error: ${error instanceof Error ? error.message : "Unknown error"}`
    );
  }
});

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("ParcelData MCP server running on stdio");
}

main().catch(console.error);
```

### S2: Tool Definitions
Create `mcp/src/tools/definitions.ts` with all tool schemas.

```typescript
// mcp/src/tools/definitions.ts
import { Tool } from "@modelcontextprotocol/sdk/types.js";

export const TOOLS: Tool[] = [
  {
    name: "property_lookup",
    description: "Get comprehensive property data by address, parcel ID, or coordinates",
    inputSchema: {
      type: "object",
      properties: {
        address: {
          type: "string",
          description: "Full property address (e.g., '123 Main St, Austin, TX 78701')",
        },
        parcel_id: {
          type: "string",
          description: "Dharma parcel ID (e.g., 'TX-TRAVIS-0234567')",
        },
        lat: {
          type: "number",
          description: "Latitude coordinate",
        },
        lng: {
          type: "number",
          description: "Longitude coordinate",
        },
        include: {
          type: "array",
          items: { type: "string" },
          description: "Data sections to include: 'basic', 'valuation', 'zoning', 'permits', 'title', 'tax', 'environmental', 'schools', 'hoa', 'demographics', 'all'",
        },
        detail: {
          type: "string",
          enum: ["micro", "standard", "extended", "full"],
          description: "Response detail level for token optimization",
        },
      },
    },
  },
  {
    name: "property_search",
    description: "Search for properties matching criteria within a geographic area",
    inputSchema: {
      type: "object",
      properties: {
        city: { type: "string" },
        state: { type: "string" },
        zip: { type: "string" },
        bounds: {
          type: "object",
          properties: {
            north: { type: "number" },
            south: { type: "number" },
            east: { type: "number" },
            west: { type: "number" },
          },
        },
        property_type: {
          type: "array",
          items: {
            type: "string",
            enum: ["single_family", "condo", "townhouse", "multi_family", "land", "commercial"],
          },
        },
        bedrooms_min: { type: "integer" },
        bedrooms_max: { type: "integer" },
        bathrooms_min: { type: "number" },
        sqft_min: { type: "integer" },
        sqft_max: { type: "integer" },
        lot_sqft_min: { type: "integer" },
        year_built_min: { type: "integer" },
        year_built_max: { type: "integer" },
        price_min: { type: "integer" },
        price_max: { type: "integer" },
        listing_status: {
          type: "array",
          items: {
            type: "string",
            enum: ["active", "pending", "sold", "off_market"],
          },
        },
        zoning: {
          type: "array",
          items: { type: "string" },
        },
        limit: { type: "integer", default: 25 },
      },
      required: ["state"],
    },
  },
  {
    name: "get_comparables",
    description: "Find comparable sales for a property to estimate value",
    inputSchema: {
      type: "object",
      properties: {
        property_id: {
          type: "string",
          description: "Dharma parcel ID of subject property",
        },
        address: {
          type: "string",
          description: "Address of subject property (alternative to property_id)",
        },
        radius_miles: {
          type: "number",
          default: 1,
          description: "Search radius in miles",
        },
        months: {
          type: "integer",
          default: 6,
          description: "Look back period in months",
        },
        limit: { type: "integer", default: 10 },
      },
    },
  },
  {
    name: "get_market_trends",
    description: "Get market statistics and trends for an area",
    inputSchema: {
      type: "object",
      properties: {
        zip: { type: "string" },
        city: { type: "string" },
        county: { type: "string" },
        state: { type: "string" },
        property_type: { type: "string" },
        period: {
          type: "string",
          enum: ["3m", "6m", "12m", "24m", "5y"],
          default: "12m",
        },
      },
      required: ["state"],
    },
  },
  {
    name: "check_zoning",
    description: "Check if a specific use is permitted at a property",
    inputSchema: {
      type: "object",
      properties: {
        property_id: { type: "string" },
        address: { type: "string" },
        proposed_use: {
          type: "string",
          description: "The intended use (e.g., 'single_family', 'duplex', 'retail', 'restaurant', 'adu')",
        },
      },
      required: ["proposed_use"],
    },
  },
  {
    name: "get_permits",
    description: "Get permit history and active permits for a property",
    inputSchema: {
      type: "object",
      properties: {
        property_id: { type: "string" },
        address: { type: "string" },
        status: {
          type: "array",
          items: {
            type: "string",
            enum: ["issued", "in_review", "approved", "inspection", "finaled", "expired"],
          },
        },
        permit_type: {
          type: "array",
          items: {
            type: "string",
            enum: ["building", "electrical", "plumbing", "mechanical", "demolition", "grading"],
          },
        },
        since_date: { type: "string", format: "date" },
      },
    },
  },
  {
    name: "get_owner_portfolio",
    description: "Find all properties owned by a person or entity",
    inputSchema: {
      type: "object",
      properties: {
        owner_name: {
          type: "string",
          description: "Name of owner (person or entity)",
        },
        state: { type: "string" },
        include_related_entities: {
          type: "boolean",
          default: true,
          description: "Include properties owned by related LLCs/trusts",
        },
      },
      required: ["owner_name"],
    },
  },
  {
    name: "estimate_value",
    description: "Get an automated valuation estimate for a property",
    inputSchema: {
      type: "object",
      properties: {
        property_id: { type: "string" },
        address: { type: "string" },
        adjustments: {
          type: "object",
          properties: {
            condition: {
              type: "string",
              enum: ["poor", "fair", "average", "good", "excellent"],
            },
            recent_renovations: { type: "boolean" },
            renovation_value: { type: "integer" },
          },
        },
      },
    },
  },
  {
    name: "check_development_feasibility",
    description: "Given a parcel, return max buildable area based on zoning code — FAR, height limits, setbacks, permitted uses",
    inputSchema: {
      type: "object",
      properties: {
        property_id: {
          type: "string",
          description: "Dharma parcel ID (e.g., 'TX-TRAVIS-0234567')",
        },
        proposed_use: {
          type: "string",
          description: "Optional: intended use (e.g., 'single_family', 'multifamily', 'retail')",
        },
      },
      required: ["property_id"],
    },
  },
];
```

### S3: API Client
Create `mcp/src/client/api.ts` for ParcelData API calls.

```typescript
// mcp/src/client/api.ts
interface ApiConfig {
  baseUrl: string;
  apiKey: string;
}

const config: ApiConfig = {
  baseUrl: process.env.PARCELDATA_API_URL || "https://api.parceldata.ai",
  apiKey: process.env.PARCELDATA_API_KEY || "",
};

export async function apiCall<T>(
  endpoint: string,
  options: {
    method?: "GET" | "POST";
    params?: Record<string, string | number | boolean | undefined>;
    body?: Record<string, unknown>;
  } = {}
): Promise<T> {
  const { method = "GET", params, body } = options;

  let url = `${config.baseUrl}${endpoint}`;
  
  if (params) {
    const searchParams = new URLSearchParams();
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined) {
        searchParams.set(key, String(value));
      }
    }
    const queryString = searchParams.toString();
    if (queryString) {
      url += `?${queryString}`;
    }
  }

  const headers: Record<string, string> = {
    "Authorization": `Bearer ${config.apiKey}`,
    "Content-Type": "application/json",
  };

  const response = await fetch(url, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: "Unknown error" }));
    throw new Error(`API error: ${error.message || response.statusText}`);
  }

  return response.json();
}
```

### S4: Property Lookup Tool
Create `mcp/src/tools/property-lookup.ts`.

```typescript
// mcp/src/tools/property-lookup.ts
import { apiCall } from "../client/api.js";

interface PropertyLookupArgs {
  address?: string;
  parcel_id?: string;
  lat?: number;
  lng?: number;
  include?: string[];
  detail?: "micro" | "standard" | "extended" | "full";
}

interface PropertyResponse {
  property_id: string;
  address: {
    street: string;
    city: string;
    state: string;
    zip: string;
    formatted: string;
  };
  // ... other fields
}

export async function propertyLookup(args: PropertyLookupArgs) {
  // Determine endpoint based on provided identifiers
  let endpoint: string;
  let params: Record<string, string | number | undefined> = {};

  if (args.parcel_id) {
    endpoint = `/v1/properties/${args.parcel_id}`;
  } else if (args.address) {
    endpoint = "/v1/properties/address";
    params.street = args.address;
    // Parse city/state from address if provided together
    const parts = args.address.split(",").map((p) => p.trim());
    if (parts.length >= 2) {
      params.street = parts[0];
      params.city = parts[1];
      if (parts.length >= 3) {
        params.state = parts[2].split(" ")[0];
      }
    }
  } else if (args.lat !== undefined && args.lng !== undefined) {
    endpoint = "/v1/properties/coordinates";
    params.lat = args.lat;
    params.lng = args.lng;
  } else {
    return {
      content: [
        {
          type: "text",
          text: JSON.stringify({
            error: "Must provide address, parcel_id, or lat/lng coordinates",
          }),
        },
      ],
    };
  }

  if (args.detail) {
    params.detail = args.detail;
  }

  try {
    const property = await apiCall<PropertyResponse>(endpoint, { params });

    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(property, null, 2),
        },
      ],
    };
  } catch (error) {
    return {
      content: [
        {
          type: "text",
          text: JSON.stringify({
            error: error instanceof Error ? error.message : "Unknown error",
          }),
        },
      ],
      isError: true,
    };
  }
}
```

### S5: Property Search Tool
Create `mcp/src/tools/property-search.ts`.

```typescript
// mcp/src/tools/property-search.ts
import { apiCall } from "../client/api.js";

interface PropertySearchArgs {
  city?: string;
  state: string;
  zip?: string;
  bounds?: {
    north: number;
    south: number;
    east: number;
    west: number;
  };
  property_type?: string[];
  bedrooms_min?: number;
  bedrooms_max?: number;
  bathrooms_min?: number;
  sqft_min?: number;
  sqft_max?: number;
  lot_sqft_min?: number;
  year_built_min?: number;
  year_built_max?: number;
  price_min?: number;
  price_max?: number;
  listing_status?: string[];
  zoning?: string[];
  limit?: number;
}

export async function propertySearch(args: PropertySearchArgs) {
  try {
    const response = await apiCall<{
      results: unknown[];
      total: number;
      has_more: boolean;
    }>("/v1/properties/search", {
      method: "POST",
      body: args,
    });

    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(
            {
              total: response.total,
              returned: response.results.length,
              has_more: response.has_more,
              results: response.results,
            },
            null,
            2
          ),
        },
      ],
    };
  } catch (error) {
    return {
      content: [
        {
          type: "text",
          text: JSON.stringify({
            error: error instanceof Error ? error.message : "Unknown error",
          }),
        },
      ],
      isError: true,
    };
  }
}
```

### S6: Get Comparables Tool
Create `mcp/src/tools/get-comparables.ts`.

```typescript
// mcp/src/tools/get-comparables.ts
import { apiCall } from "../client/api.js";

interface GetComparablesArgs {
  property_id?: string;
  address?: string;
  radius_miles?: number;
  months?: number;
  limit?: number;
}

export async function getComparables(args: GetComparablesArgs) {
  const params: Record<string, string | number | undefined> = {};

  if (args.property_id) {
    params.property_id = args.property_id;
  } else if (args.address) {
    // First lookup the property, then get comps
    const lookupResult = await apiCall<{ property_id: string }>(
      "/v1/properties/address",
      { params: { street: args.address } }
    );
    params.property_id = lookupResult.property_id;
  } else {
    return {
      content: [
        {
          type: "text",
          text: JSON.stringify({
            error: "Must provide property_id or address",
          }),
        },
      ],
    };
  }

  if (args.radius_miles) params.radius_miles = args.radius_miles;
  if (args.months) params.months = args.months;
  if (args.limit) params.limit = args.limit;

  try {
    const response = await apiCall<unknown>("/v1/analytics/comparables", {
      params,
    });

    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(response, null, 2),
        },
      ],
    };
  } catch (error) {
    return {
      content: [
        {
          type: "text",
          text: JSON.stringify({
            error: error instanceof Error ? error.message : "Unknown error",
          }),
        },
      ],
      isError: true,
    };
  }
}
```

### S7: Get Market Trends Tool
Create `mcp/src/tools/get-market-trends.ts`.

```typescript
// mcp/src/tools/get-market-trends.ts
import { apiCall } from "../client/api.js";

interface GetMarketTrendsArgs {
  zip?: string;
  city?: string;
  county?: string;
  state: string;
  property_type?: string;
  period?: "3m" | "6m" | "12m" | "24m" | "5y";
}

export async function getMarketTrends(args: GetMarketTrendsArgs) {
  try {
    const response = await apiCall<unknown>("/v1/analytics/market-trends", {
      params: args as Record<string, string | undefined>,
    });

    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(response, null, 2),
        },
      ],
    };
  } catch (error) {
    return {
      content: [
        {
          type: "text",
          text: JSON.stringify({
            error: error instanceof Error ? error.message : "Unknown error",
          }),
        },
      ],
      isError: true,
    };
  }
}
```

### S8: Check Zoning Tool
Create `mcp/src/tools/check-zoning.ts`.

```typescript
// mcp/src/tools/check-zoning.ts
import { apiCall } from "../client/api.js";

interface CheckZoningArgs {
  property_id?: string;
  address?: string;
  proposed_use: string;
}

interface ZoningResponse {
  property_id: string;
  address: string;
  current_zoning: string;
  proposed_use: string;
  permitted: boolean;
  permit_type: "by_right" | "conditional" | "variance" | "prohibited";
  requirements?: {
    max_size_sqft?: number;
    max_height_ft?: number;
    setback_rear_ft?: number;
    setback_side_ft?: number;
    parking_spaces?: number;
    owner_occupancy_required?: boolean;
  };
  notes?: string;
}

export async function checkZoning(args: CheckZoningArgs) {
  // First get the property
  let propertyId = args.property_id;

  if (!propertyId && args.address) {
    try {
      const lookup = await apiCall<{ property_id: string }>(
        "/v1/properties/address",
        { params: { street: args.address } }
      );
      propertyId = lookup.property_id;
    } catch {
      return {
        content: [
          {
            type: "text",
            text: JSON.stringify({
              error: "Property not found at provided address",
            }),
          },
        ],
        isError: true,
      };
    }
  }

  if (!propertyId) {
    return {
      content: [
        {
          type: "text",
          text: JSON.stringify({
            error: "Must provide property_id or address",
          }),
        },
      ],
    };
  }

  try {
    // Get property with zoning data
    const property = await apiCall<{
      property_id: string;
      address: { formatted: string };
      zoning: {
        zone_code: string;
        zone_description: string;
        permitted_uses: string[];
        conditional_uses: string[];
        setbacks: { front: number; rear: number; side: number };
        max_height: number;
        max_far: number;
      };
    }>(`/v1/properties/${propertyId}?detail=standard`, {});

    const zoning = property.zoning;
    const use = args.proposed_use.toLowerCase();

    // Check if use is permitted
    let permitted = false;
    let permitType: "by_right" | "conditional" | "variance" | "prohibited" =
      "prohibited";

    if (zoning.permitted_uses?.some((u) => u.toLowerCase().includes(use))) {
      permitted = true;
      permitType = "by_right";
    } else if (
      zoning.conditional_uses?.some((u) => u.toLowerCase().includes(use))
    ) {
      permitted = true;
      permitType = "conditional";
    }

    const response: ZoningResponse = {
      property_id: property.property_id,
      address: property.address.formatted,
      current_zoning: zoning.zone_code,
      proposed_use: args.proposed_use,
      permitted,
      permit_type: permitType,
      requirements: {
        max_height_ft: zoning.max_height,
        setback_rear_ft: zoning.setbacks?.rear,
        setback_side_ft: zoning.setbacks?.side,
      },
    };

    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(response, null, 2),
        },
      ],
    };
  } catch (error) {
    return {
      content: [
        {
          type: "text",
          text: JSON.stringify({
            error: error instanceof Error ? error.message : "Unknown error",
          }),
        },
      ],
      isError: true,
    };
  }
}
```

### S9: Get Permits Tool
Create `mcp/src/tools/get-permits.ts`.

```typescript
// mcp/src/tools/get-permits.ts
import { apiCall } from "../client/api.js";

interface GetPermitsArgs {
  property_id?: string;
  address?: string;
  status?: string[];
  permit_type?: string[];
  since_date?: string;
}

export async function getPermits(args: GetPermitsArgs) {
  let propertyId = args.property_id;

  if (!propertyId && args.address) {
    try {
      const lookup = await apiCall<{ property_id: string }>(
        "/v1/properties/address",
        { params: { street: args.address } }
      );
      propertyId = lookup.property_id;
    } catch {
      return {
        content: [
          {
            type: "text",
            text: JSON.stringify({ error: "Property not found" }),
          },
        ],
        isError: true,
      };
    }
  }

  if (!propertyId) {
    return {
      content: [
        {
          type: "text",
          text: JSON.stringify({
            error: "Must provide property_id or address",
          }),
        },
      ],
    };
  }

  try {
    const property = await apiCall<{
      property_id: string;
      permits: Array<{
        permit_number: string;
        type: string;
        description: string;
        status: string;
        issue_date: string;
        valuation: number;
        contractor: string;
      }>;
    }>(`/v1/properties/${propertyId}?detail=extended`, {});

    let permits = property.permits || [];

    // Filter by status if specified
    if (args.status && args.status.length > 0) {
      permits = permits.filter((p) =>
        args.status!.some((s) => p.status.toLowerCase().includes(s.toLowerCase()))
      );
    }

    // Filter by type if specified
    if (args.permit_type && args.permit_type.length > 0) {
      permits = permits.filter((p) =>
        args.permit_type!.some((t) => p.type.toLowerCase().includes(t.toLowerCase()))
      );
    }

    // Filter by date if specified
    if (args.since_date) {
      const sinceDate = new Date(args.since_date);
      permits = permits.filter((p) => new Date(p.issue_date) >= sinceDate);
    }

    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(
            {
              property_id: propertyId,
              permit_count: permits.length,
              permits,
            },
            null,
            2
          ),
        },
      ],
    };
  } catch (error) {
    return {
      content: [
        {
          type: "text",
          text: JSON.stringify({
            error: error instanceof Error ? error.message : "Unknown error",
          }),
        },
      ],
      isError: true,
    };
  }
}
```

### S10: Remaining Tools
Create the remaining tool files: `get-owner-portfolio.ts`, `estimate-value.ts`, `check-development-feasibility.ts`.

```typescript
// mcp/src/tools/get-owner-portfolio.ts
import { apiCall } from "../client/api.js";

interface GetOwnerPortfolioArgs {
  owner_name: string;
  state?: string;
  include_related_entities?: boolean;
}

export async function getOwnerPortfolio(args: GetOwnerPortfolioArgs) {
  try {
    const response = await apiCall<{
      owner: string;
      property_count: number;
      properties: unknown[];
      related_entities: string[];
    }>("/v1/analytics/owner-portfolio", {
      params: {
        owner_name: args.owner_name,
        state: args.state,
        include_related: args.include_related_entities ? "true" : "false",
      },
    });

    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(response, null, 2),
        },
      ],
    };
  } catch (error) {
    return {
      content: [
        {
          type: "text",
          text: JSON.stringify({
            error: error instanceof Error ? error.message : "Unknown error",
          }),
        },
      ],
      isError: true,
    };
  }
}

// mcp/src/tools/estimate-value.ts
export async function estimateValue(args: {
  property_id?: string;
  address?: string;
  adjustments?: {
    condition?: string;
    recent_renovations?: boolean;
    renovation_value?: number;
  };
}) {
  // Similar pattern - lookup property, call valuation endpoint
  return {
    content: [
      {
        type: "text",
        text: JSON.stringify({
          message: "Valuation estimate functionality",
          args,
        }),
      },
    ],
  };
}

// mcp/src/tools/check-development-feasibility.ts
export async function checkDevelopmentFeasibility(args: {
  property_id: string;
  proposed_use?: string;
}) {
  // Get property zoning data and calculate max buildable
  return {
    content: [
      {
        type: "text",
        text: JSON.stringify({
          message: "Development feasibility check",
          args,
        }),
      },
    ],
  };
}
```

---

## Acceptance Criteria
- MCP server starts and connects via stdio
- All 9 tools registered and callable
- Tools make proper API calls to ParcelData backend
- Error handling returns structured error responses
- TypeScript compiles without errors
- Tests pass for all tools
- Package builds and can be published to npm
