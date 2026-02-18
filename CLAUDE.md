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

## Current Stage: P10-08-landing-page

# P10-08: Landing Page

**Phase 8 — ParcelData.ai Landing Page**

Adapt the Aura Finance template into the ParcelData.ai landing page using the design brief.

---

## Template Reference
The base template is at `/home/numen/dharma/templates/aura-finance/`.
Files: `index.html`, `about.html`, `features.html`, `pricing.html`, `login.html`

The landing page design brief is at `/home/numen/.openclaw/workspace/plans/re-data-service/LANDING_PAGE_BRIEF.md`.

## Design Direction
- **Keep:** Dark theme, animations (beams, sonar, spotlight cards), Tailwind CSS, pill nav, serif+sans font combo
- **Change:** All content, brand colors (sky blue → ParcelData green/teal #10B981 or keep blue), brand name, copy, features, pricing
- **Add:** Interactive code examples, MCP integration showcase, ASCII art hero concept, agent readability features
- **Remove:** Fake testimonials, "Dr. Elias Thorne", financial/banking language, UnicornStudio dependency (replace with CSS-only effects)
- **Vibe:** Stripe/Supabase energy. Developer-first. Code-forward. Zero stock photos. Zero "schedule a demo."

---

## Stories

### Story 1: Copy Base Template to Site Directory
**Action:** Copy template files from `/home/numen/dharma/templates/aura-finance/` to `site/`
- Copy `index.html` as starting point
- Copy CSS/styling patterns
- Do NOT copy images or UnicornStudio scripts

---

### Story 2: Brand & Navigation Replacement
**File:** `site/index.html`

Replace throughout:
- "Aura" → "ParcelData"
- "Aura Financial" → "ParcelData.ai"
- Logo icon: Use a map/parcel icon (inline SVG, Lucide `map-pin` or `layers` or `grid-3x3`)
- Nav links: Docs, Pricing, GitHub (external link to repo), API Reference
- CTA button: "Get API Key" (not "Start Engine")
- Brand color: Keep `#38BDF8` (sky blue) OR switch to `#10B981` (emerald/teal) — pick one, use consistently
- Font: Keep Inter + Newsreader combo (it works)

---

### Story 3: Hero Section
**File:** `site/index.html`

Replace hero content:
- Status pill: "Open Source · MIT Licensed" (with green dot)
- Headline: `Clean data for smart agents.` (italic serif, large)
- Subheadline: "Universal real estate data via API and MCP. Property records, valuations, ownership, zoning — structured for machines, readable by humans."
- Primary CTA: "Get API Key" (shiny animated button)
- Secondary CTA: "View Documentation" (outline button with arrow)

Optional: Add a code snippet preview floating on the right side (replacing the sonar visualization):
```python
from parceldata import ParcelData

pd = ParcelData(api_key="pk_live_...")
property = pd.lookup("CA-037-1234-567")
print(property.address)      # "123 Main St, Los Angeles, CA"
print(property.value)         # "$1,250,000"
print(property.quality_score) # 0.94
```

---

### Story 4: Feature Cards Section
**File:** `site/index.html`

Replace the 3 feature cards:

**Card 1: "Property Intelligence"**
- Icon: Building/Home icon
- Description: "Unified property records from 20+ data sources. Ownership, tax, zoning, permits, valuations — all normalized to a single schema."
- Visual: Mock API response card showing a property JSON snippet

**Card 2: "MCP Native"**
- Icon: Plug/Connection icon
- Description: "First-class Model Context Protocol support. Connect any AI agent to real estate data in one line. Tools: property_lookup, search, comps, batch."
- Visual: MCP connection diagram (agent → MCP → ParcelData → data sources)

**Card 3: "Entity Resolution"**
- Icon: Fingerprint/Match icon
- Description: "Cross-source identity matching with confidence scores. One property, one record, regardless of how many sources report it."
- Visual: Data quality score visualization (0.94 with breakdown)

---

### Story 5: Code Examples Section
**File:** `site/index.html`

Replace the "testimonial/quote" section with interactive code examples:

Tab-based code switcher showing:
1. **Python** — SDK usage
2. **curl** — REST API
3. **TypeScript** — MCP integration
4. **GraphQL** — Query example

Dark code blocks with syntax highlighting (use `<pre><code>` with manual span coloring, no external lib needed).

---

### Story 6: Pricing Section
**File:** `site/index.html`

Replace pricing cards with ParcelData tiers:

**Free** — $0/mo
- 1,000 lookups/month
- Standard response tier
- Community support
- CTA: "Start Free"

**Pro** — $49/mo
- 50,000 lookups/month
- All response tiers
- Batch API (100/request)
- Priority support
- CTA: "Get Started"

**Scale** — Usage-based
- Unlimited lookups
- Volume discounts
- SLA guarantee
- Dedicated support
- CTA: "Contact Us"

Toggle: Monthly / Annual (20% discount)

---

### Story 7: Data Coverage Section
**File:** `site/index.html`

New section showing data coverage:
- "150M+ Properties" stat
- "50 States" coverage
- "20+ Data Sources" integrated
- Visual: Simple US map or grid showing coverage density
- Data source logos (in monotone marquee): Regrid, ATTOM, Census, FEMA, EPA

---

### Story 8: Agent Readability Section
**File:** `site/index.html`

Section showcasing agent-first design:
- `/llms.txt` — "Your agent reads our docs"
- MCP tools — "Connect in one line"
- Token-optimized responses — "Micro (500 tokens) → Full (32K tokens)"
- JSON-LD — "Structured data in every response"

---

### Story 9: Footer
**File:** `site/index.html`

Replace footer:
- Brand: ParcelData.ai
- Links: Documentation, API Reference, GitHub, Status, Privacy, Terms
- Social: GitHub, X/Twitter, Discord
- "Open Source · MIT License"
- Remove Stripe/Visa logos (not relevant)
- Add: "Built by Dharma Technologies"

---

### Story 10: /llms.txt Static File
**File:** `site/llms.txt`

Create a static `/llms.txt` file for the landing page domain:
```
# ParcelData.ai
> Clean, universal real estate data for AI agents.

## Quick Start
pip install parceldata

## API
Base URL: https://api.parceldata.ai/v1
Auth: API key via X-API-Key header

## MCP
Server: mcp://api.parceldata.ai/v1
Tools: property_lookup, property_search, get_comps, batch_lookup

## Links
- API Docs: https://api.parceldata.ai/v1/docs
- GitHub: https://github.com/Dharma-Technologies/parceldata
- SDK: pip install parceldata
```

---

### Story 11: ai-plugin.json Static File
**File:** `site/.well-known/ai-plugin.json`

OpenAI-compatible plugin manifest for the landing page domain.

---

### Story 12: Meta Tags & SEO
**File:** `site/index.html`

- Title: "ParcelData.ai — Clean Real Estate Data for AI Agents"
- Meta description optimized for search
- Open Graph tags (title, description, image)
- Twitter card tags
- Favicon (simple SVG inline)
- Canonical URL: https://parceldata.ai

---

## Acceptance Criteria
- [ ] Landing page renders correctly in browser
- [ ] All "Aura" references removed
- [ ] Content matches ParcelData product
- [ ] Code examples are accurate and working
- [ ] Pricing matches plan
- [ ] Mobile responsive
- [ ] `/llms.txt` accessible
- [ ] `/.well-known/ai-plugin.json` accessible
- [ ] No external dependencies that require paid accounts (UnicornStudio removed)
- [ ] Dark theme preserved with consistent brand color
