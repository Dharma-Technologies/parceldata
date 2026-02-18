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

## Current Stage: P10-04-auth-billing

# PRD: P10-04 — Auth & Billing

## Overview
Implement API key management, authentication, usage metering, rate limiting by tier, and Stripe billing integration for self-serve signup and payment.

---

## Stories

### S1: API Key Model
Create `api/app/models/api_key.py` for key storage.

```python
# api/app/models/api_key.py
from datetime import datetime
from sqlalchemy import String, Integer, Boolean, DateTime, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB
from app.models.base import Base, TimestampMixin
import enum

class TierEnum(str, enum.Enum):
    FREE = "free"
    PRO = "pro"
    BUSINESS = "business"
    ENTERPRISE = "enterprise"

class APIKey(Base, TimestampMixin):
    __tablename__ = "api_keys"
    __table_args__ = {"schema": "parcel"}
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    key_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    key_prefix: Mapped[str] = mapped_column(String(10))  # pk_live_, pk_test_
    
    # Account
    account_id: Mapped[int] = mapped_column(ForeignKey("parcel.accounts.id"), index=True)
    
    # Key metadata
    name: Mapped[str | None] = mapped_column(String(100))
    tier: Mapped[TierEnum] = mapped_column(Enum(TierEnum), default=TierEnum.FREE)
    scopes: Mapped[list] = mapped_column(JSONB, default=["read"])  # read, write, admin
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_used: Mapped[datetime | None] = mapped_column(DateTime)
    
    # Limits
    rate_limit_override: Mapped[int | None] = mapped_column(Integer)  # Custom rate limit
    daily_limit_override: Mapped[int | None] = mapped_column(Integer)
    
    # Expiration
    expires_at: Mapped[datetime | None] = mapped_column(DateTime)
    
    account = relationship("Account", back_populates="api_keys")

class Account(Base, TimestampMixin):
    __tablename__ = "accounts"
    __table_args__ = {"schema": "parcel"}
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # Identity
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Profile
    name: Mapped[str | None] = mapped_column(String(200))
    company: Mapped[str | None] = mapped_column(String(200))
    
    # Billing
    stripe_customer_id: Mapped[str | None] = mapped_column(String(50), index=True)
    tier: Mapped[TierEnum] = mapped_column(Enum(TierEnum), default=TierEnum.FREE)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    api_keys = relationship("APIKey", back_populates="account")
    usage_records = relationship("UsageRecord", back_populates="account")
```

### S2: Usage Record Model
Create `api/app/models/usage.py` for tracking API usage.

```python
# api/app/models/usage.py
from datetime import datetime, date
from sqlalchemy import String, Integer, Float, Date, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

class UsageRecord(Base):
    __tablename__ = "usage_records"
    __table_args__ = {"schema": "parcel"}
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("parcel.accounts.id"), index=True)
    api_key_id: Mapped[int] = mapped_column(ForeignKey("parcel.api_keys.id"), index=True)
    
    # Period
    usage_date: Mapped[date] = mapped_column(Date, index=True)
    
    # Counts
    queries_count: Mapped[int] = mapped_column(Integer, default=0)
    queries_billable: Mapped[int] = mapped_column(Integer, default=0)
    
    # Breakdown by endpoint
    property_lookups: Mapped[int] = mapped_column(Integer, default=0)
    property_searches: Mapped[int] = mapped_column(Integer, default=0)
    comparables_requests: Mapped[int] = mapped_column(Integer, default=0)
    batch_requests: Mapped[int] = mapped_column(Integer, default=0)
    
    # Costs (for metered billing)
    estimated_cost: Mapped[float] = mapped_column(Float, default=0.0)
    
    account = relationship("Account", back_populates="usage_records")

class UsageEvent(Base):
    __tablename__ = "usage_events"
    __table_args__ = {"schema": "parcel"}
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    api_key_id: Mapped[int] = mapped_column(ForeignKey("parcel.api_keys.id"), index=True)
    
    # Event details
    endpoint: Mapped[str] = mapped_column(String(100), index=True)
    method: Mapped[str] = mapped_column(String(10))
    query_count: Mapped[int] = mapped_column(Integer, default=1)  # Batch = multiple
    
    # Response
    status_code: Mapped[int] = mapped_column(Integer)
    response_time_ms: Mapped[int] = mapped_column(Integer)
    
    # Timestamp
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
```

### S3: API Key Service
Create `api/app/services/auth_service.py` for key management.

```python
# api/app/services/auth_service.py
import hashlib
import secrets
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.api_key import APIKey, Account, TierEnum
from app.database.redis import get_redis

class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_account(self, email: str, name: str | None = None) -> Account:
        """Create a new account."""
        account = Account(email=email.lower(), name=name)
        self.db.add(account)
        await self.db.commit()
        await self.db.refresh(account)
        return account
    
    async def create_api_key(
        self,
        account_id: int,
        name: str | None = None,
        tier: TierEnum = TierEnum.FREE,
        scopes: list[str] | None = None,
    ) -> tuple[str, APIKey]:
        """
        Create a new API key for an account.
        
        Returns (raw_key, APIKey) - raw_key is only shown once.
        """
        # Generate key
        key_id = secrets.token_urlsafe(24)
        prefix = "pk_live_" if tier != TierEnum.FREE else "pk_test_"
        raw_key = f"{prefix}{key_id}"
        
        # Hash for storage
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        
        api_key = APIKey(
            key_hash=key_hash,
            key_prefix=prefix,
            account_id=account_id,
            name=name,
            tier=tier,
            scopes=scopes or ["read"],
        )
        
        self.db.add(api_key)
        await self.db.commit()
        await self.db.refresh(api_key)
        
        # Cache key info in Redis for fast lookup
        redis = await get_redis()
        await redis.hset(f"apikey:{raw_key}", mapping={
            "id": str(api_key.id),
            "account_id": str(account_id),
            "tier": tier.value,
            "scopes": ",".join(api_key.scopes),
        })
        await redis.expire(f"apikey:{raw_key}", 86400)  # 24 hour cache
        
        return raw_key, api_key
    
    async def validate_key(self, raw_key: str) -> dict | None:
        """
        Validate an API key and return key info.
        
        Returns None if invalid.
        """
        # Check Redis cache first
        redis = await get_redis()
        cached = await redis.hgetall(f"apikey:{raw_key}")
        
        if cached:
            return {
                "id": int(cached["id"]),
                "account_id": int(cached["account_id"]),
                "tier": cached["tier"],
                "scopes": cached["scopes"].split(","),
            }
        
        # Check database
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        stmt = select(APIKey).where(
            APIKey.key_hash == key_hash,
            APIKey.is_active == True,
        )
        result = await self.db.execute(stmt)
        api_key = result.scalar_one_or_none()
        
        if not api_key:
            return None
        
        # Check expiration
        if api_key.expires_at and api_key.expires_at < datetime.utcnow():
            return None
        
        # Update last used
        api_key.last_used = datetime.utcnow()
        await self.db.commit()
        
        # Cache in Redis
        key_info = {
            "id": str(api_key.id),
            "account_id": str(api_key.account_id),
            "tier": api_key.tier.value,
            "scopes": ",".join(api_key.scopes),
        }
        await redis.hset(f"apikey:{raw_key}", mapping=key_info)
        await redis.expire(f"apikey:{raw_key}", 86400)
        
        return {
            "id": api_key.id,
            "account_id": api_key.account_id,
            "tier": api_key.tier.value,
            "scopes": api_key.scopes,
        }
    
    async def revoke_key(self, key_id: int) -> bool:
        """Revoke an API key."""
        stmt = select(APIKey).where(APIKey.id == key_id)
        result = await self.db.execute(stmt)
        api_key = result.scalar_one_or_none()
        
        if not api_key:
            return False
        
        api_key.is_active = False
        await self.db.commit()
        
        # Invalidate Redis cache
        # (Note: we don't have the raw key here, so cache will expire naturally)
        
        return True
```

### S4: Usage Tracking Service
Create `api/app/services/usage_service.py` for metering.

```python
# api/app/services/usage_service.py
from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.usage import UsageRecord, UsageEvent
from app.database.redis import get_redis

# Query cost weights
QUERY_COSTS = {
    "property_lookup": 1,
    "property_lookup_full": 2,
    "property_search": 1,
    "comparables": 3,
    "market_trends": 5,
    "batch": 1,  # Per property in batch
}

class UsageService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def record_usage(
        self,
        api_key_id: int,
        endpoint: str,
        method: str,
        status_code: int,
        response_time_ms: int,
        query_count: int = 1,
    ) -> None:
        """Record an API usage event."""
        
        # Create event record
        event = UsageEvent(
            api_key_id=api_key_id,
            endpoint=endpoint,
            method=method,
            query_count=query_count,
            status_code=status_code,
            response_time_ms=response_time_ms,
        )
        self.db.add(event)
        
        # Update daily aggregate (async, best effort)
        await self._update_daily_aggregate(api_key_id, endpoint, query_count)
        
        await self.db.commit()
    
    async def _update_daily_aggregate(
        self,
        api_key_id: int,
        endpoint: str,
        query_count: int,
    ) -> None:
        """Update daily usage aggregate."""
        today = date.today()
        
        # Get or create daily record
        stmt = select(UsageRecord).where(
            UsageRecord.api_key_id == api_key_id,
            UsageRecord.usage_date == today,
        )
        result = await self.db.execute(stmt)
        record = result.scalar_one_or_none()
        
        if not record:
            # Get account_id from key
            from app.models.api_key import APIKey
            key_stmt = select(APIKey.account_id).where(APIKey.id == api_key_id)
            key_result = await self.db.execute(key_stmt)
            account_id = key_result.scalar_one()
            
            record = UsageRecord(
                api_key_id=api_key_id,
                account_id=account_id,
                usage_date=today,
            )
            self.db.add(record)
        
        # Update counts
        record.queries_count += query_count
        record.queries_billable += query_count * QUERY_COSTS.get(endpoint, 1)
        
        # Update endpoint-specific counts
        if "property" in endpoint and "search" not in endpoint:
            record.property_lookups += query_count
        elif "search" in endpoint:
            record.property_searches += query_count
        elif "comparable" in endpoint:
            record.comparables_requests += query_count
        elif "batch" in endpoint:
            record.batch_requests += query_count
    
    async def get_usage_summary(
        self,
        account_id: int,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict:
        """Get usage summary for an account."""
        
        if not start_date:
            start_date = date.today().replace(day=1)  # Start of month
        if not end_date:
            end_date = date.today()
        
        stmt = select(
            func.sum(UsageRecord.queries_count).label("total_queries"),
            func.sum(UsageRecord.queries_billable).label("billable_queries"),
            func.sum(UsageRecord.property_lookups).label("property_lookups"),
            func.sum(UsageRecord.property_searches).label("property_searches"),
            func.sum(UsageRecord.comparables_requests).label("comparables"),
        ).where(
            UsageRecord.account_id == account_id,
            UsageRecord.usage_date >= start_date,
            UsageRecord.usage_date <= end_date,
        )
        
        result = await self.db.execute(stmt)
        row = result.one()
        
        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
            "queries": {
                "total": row.total_queries or 0,
                "billable": row.billable_queries or 0,
            },
            "breakdown": {
                "property_lookups": row.property_lookups or 0,
                "property_searches": row.property_searches or 0,
                "comparables": row.comparables or 0,
            },
        }
    
    async def check_quota(self, api_key_id: int, tier: str) -> tuple[bool, int, int]:
        """
        Check if key has remaining quota.
        
        Returns (has_quota, used, limit).
        """
        redis = await get_redis()
        today = date.today().isoformat()
        
        # Get daily usage from Redis
        usage_key = f"usage:{api_key_id}:{today}"
        used = int(await redis.get(usage_key) or 0)
        
        # Get limit for tier
        limits = {
            "free": 100,
            "pro": 10000,
            "business": 500000,
            "enterprise": 10000000,
        }
        limit = limits.get(tier, 100)
        
        return (used < limit, used, limit)
```

### S5: Authentication Routes
Create `api/app/routes/auth.py` for key management endpoints.

```python
# api/app/routes/auth.py
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr
from app.database.connection import get_db
from app.services.auth_service import AuthService
from app.models.api_key import TierEnum

router = APIRouter(prefix="/v1/auth", tags=["Authentication"])

class SignupRequest(BaseModel):
    email: EmailStr
    name: str | None = None
    company: str | None = None

class SignupResponse(BaseModel):
    account_id: int
    api_key: str
    tier: str
    message: str

@router.post("/signup", response_model=SignupResponse)
async def signup(
    request: SignupRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new account and get an API key.
    
    The API key is only shown once — save it securely.
    """
    service = AuthService(db)
    
    # Check if email already exists
    from sqlalchemy import select
    from app.models.api_key import Account
    stmt = select(Account).where(Account.email == request.email.lower())
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail="An account with this email already exists",
        )
    
    # Create account
    account = await service.create_account(
        email=request.email,
        name=request.name,
    )
    
    # Create API key
    raw_key, api_key = await service.create_api_key(
        account_id=account.id,
        name="Default Key",
        tier=TierEnum.FREE,
    )
    
    return SignupResponse(
        account_id=account.id,
        api_key=raw_key,
        tier="free",
        message="Save your API key — it will not be shown again.",
    )

class CreateKeyRequest(BaseModel):
    name: str | None = None
    scopes: list[str] = ["read"]

class CreateKeyResponse(BaseModel):
    api_key: str
    key_id: int
    tier: str
    scopes: list[str]

@router.post("/keys", response_model=CreateKeyResponse)
async def create_key(
    request: CreateKeyRequest,
    db: AsyncSession = Depends(get_db),
    # Note: This should be authenticated with existing key
):
    """
    Create an additional API key for your account.
    
    Requires authentication with an existing key that has 'admin' scope.
    """
    # TODO: Get account_id from authenticated key
    # For now, this is a placeholder
    raise HTTPException(status_code=501, detail="Not implemented")

@router.get("/keys")
async def list_keys(
    db: AsyncSession = Depends(get_db),
):
    """
    List all API keys for your account.
    
    Does not show the actual key values.
    """
    # TODO: Get account_id from authenticated key
    raise HTTPException(status_code=501, detail="Not implemented")

@router.delete("/keys/{key_id}")
async def revoke_key(
    key_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Revoke an API key.
    
    The key will immediately stop working.
    """
    service = AuthService(db)
    success = await service.revoke_key(key_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Key not found")
    
    return {"message": "Key revoked successfully"}
```

### S6: Account Routes
Create `api/app/routes/account.py` for account and usage info.

```python
# api/app/routes/account.py
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
from pydantic import BaseModel
from app.database.connection import get_db
from app.services.usage_service import UsageService

router = APIRouter(prefix="/v1/account", tags=["Account"])

class UsageResponse(BaseModel):
    period: dict
    queries: dict
    breakdown: dict
    limits: dict
    remaining: int

@router.get("/usage", response_model=UsageResponse)
async def get_usage(
    request: Request,
    start_date: date | None = None,
    end_date: date | None = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Get your API usage for the current billing period.
    """
    key_info = request.state.key_info
    account_id = key_info.get("account_id")
    tier = key_info.get("tier", "free")
    
    service = UsageService(db)
    usage = await service.get_usage_summary(account_id, start_date, end_date)
    
    # Get tier limits
    limits = {
        "free": 3000,
        "pro": 50000,
        "business": 500000,
        "enterprise": 10000000,
    }
    monthly_limit = limits.get(tier, 3000)
    
    return UsageResponse(
        period=usage["period"],
        queries=usage["queries"],
        breakdown=usage["breakdown"],
        limits={
            "monthly": monthly_limit,
            "tier": tier,
        },
        remaining=max(0, monthly_limit - usage["queries"]["total"]),
    )

class BillingResponse(BaseModel):
    tier: str
    status: str
    current_period: dict
    payment_method: dict | None
    invoices: list[dict]

@router.get("/billing", response_model=BillingResponse)
async def get_billing(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Get your billing information and invoices.
    """
    key_info = request.state.key_info
    tier = key_info.get("tier", "free")
    
    # TODO: Integrate with Stripe to get real billing data
    return BillingResponse(
        tier=tier,
        status="active",
        current_period={
            "start": date.today().replace(day=1).isoformat(),
            "end": date.today().isoformat(),
        },
        payment_method=None,
        invoices=[],
    )

@router.post("/upgrade")
async def upgrade_tier(
    request: Request,
    target_tier: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Upgrade your account to a higher tier.
    
    Redirects to Stripe checkout for payment.
    """
    # TODO: Create Stripe checkout session
    raise HTTPException(status_code=501, detail="Not implemented - use Stripe checkout")
```

### S7: Stripe Integration
Create `api/app/services/stripe_service.py` for billing.

```python
# api/app/services/stripe_service.py
import stripe
from app.config import settings

stripe.api_key = settings.stripe_secret_key

PRICE_IDS = {
    "pro": "price_pro_monthly",  # Replace with actual Stripe price IDs
    "business": "price_business_monthly",
}

class StripeService:
    @staticmethod
    async def create_customer(email: str, name: str | None = None) -> str:
        """Create a Stripe customer."""
        customer = stripe.Customer.create(
            email=email,
            name=name,
        )
        return customer.id
    
    @staticmethod
    async def create_checkout_session(
        customer_id: str,
        price_id: str,
        success_url: str,
        cancel_url: str,
    ) -> str:
        """Create a Stripe checkout session for subscription."""
        session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            mode="subscription",
            success_url=success_url,
            cancel_url=cancel_url,
        )
        return session.url
    
    @staticmethod
    async def create_portal_session(customer_id: str, return_url: str) -> str:
        """Create a Stripe customer portal session."""
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=return_url,
        )
        return session.url
    
    @staticmethod
    async def get_subscription(customer_id: str) -> dict | None:
        """Get active subscription for a customer."""
        subscriptions = stripe.Subscription.list(
            customer=customer_id,
            status="active",
            limit=1,
        )
        if subscriptions.data:
            return subscriptions.data[0]
        return None
    
    @staticmethod
    async def record_usage(subscription_item_id: str, quantity: int) -> None:
        """Record metered usage for overage billing."""
        stripe.SubscriptionItem.create_usage_record(
            subscription_item_id,
            quantity=quantity,
            action="increment",
        )
```

### S8: Stripe Webhook Handler
Create `api/app/routes/webhooks.py` for Stripe events.

```python
# api/app/routes/webhooks.py
from fastapi import APIRouter, Request, HTTPException, Header
import stripe
from app.config import settings
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.connection import get_db

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])

@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None),
):
    """
    Handle Stripe webhook events.
    
    Processes subscription changes, payment events, etc.
    """
    payload = await request.body()
    
    try:
        event = stripe.Webhook.construct_event(
            payload,
            stripe_signature,
            settings.stripe_webhook_secret,
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    # Handle event types
    if event.type == "checkout.session.completed":
        session = event.data.object
        await _handle_checkout_complete(session)
    
    elif event.type == "customer.subscription.updated":
        subscription = event.data.object
        await _handle_subscription_update(subscription)
    
    elif event.type == "customer.subscription.deleted":
        subscription = event.data.object
        await _handle_subscription_cancel(subscription)
    
    elif event.type == "invoice.payment_failed":
        invoice = event.data.object
        await _handle_payment_failed(invoice)
    
    return {"received": True}

async def _handle_checkout_complete(session: dict) -> None:
    """Handle successful checkout - upgrade account tier."""
    customer_id = session.get("customer")
    # TODO: Find account by stripe_customer_id and update tier
    pass

async def _handle_subscription_update(subscription: dict) -> None:
    """Handle subscription changes."""
    # TODO: Update account tier based on subscription
    pass

async def _handle_subscription_cancel(subscription: dict) -> None:
    """Handle subscription cancellation - downgrade to free."""
    # TODO: Downgrade account to free tier
    pass

async def _handle_payment_failed(invoice: dict) -> None:
    """Handle failed payment - may need to restrict access."""
    # TODO: Mark account as payment_failed, send notification
    pass
```

### S9: Usage Tracking Middleware
Create `api/app/middleware/usage_tracking.py` for automatic metering.

```python
# api/app/middleware/usage_tracking.py
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import time
from app.database.connection import async_session_maker
from app.services.usage_service import UsageService

class UsageTrackingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip non-API routes
        if not request.url.path.startswith("/v1/"):
            return await call_next(request)
        
        # Skip if not authenticated
        if not hasattr(request.state, "key_info"):
            return await call_next(request)
        
        start_time = time.time()
        response = await call_next(request)
        response_time_ms = int((time.time() - start_time) * 1000)
        
        # Track usage (async, best effort)
        try:
            key_info = request.state.key_info
            key_id = key_info.get("id")
            
            if key_id:
                # Determine query count for batch endpoints
                query_count = 1
                if "/batch" in request.url.path:
                    # Get count from response or request body
                    query_count = getattr(request.state, "batch_count", 1)
                
                # Record async
                async with async_session_maker() as db:
                    service = UsageService(db)
                    await service.record_usage(
                        api_key_id=key_id,
                        endpoint=request.url.path,
                        method=request.method,
                        status_code=response.status_code,
                        response_time_ms=response_time_ms,
                        query_count=query_count,
                    )
        except Exception:
            # Don't fail the request if usage tracking fails
            pass
        
        return response
```

### S10: Enhanced Rate Limiting
Update `api/app/middleware/rate_limit.py` with quota checks.

```python
# Update api/app/middleware/rate_limit.py

from app.services.usage_service import UsageService

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not hasattr(request.state, "api_key"):
            return await call_next(request)
        
        key_info = request.state.key_info
        key_id = key_info.get("id")
        tier = key_info.get("tier", "free")
        
        # Check per-second rate limit (existing code)
        # ...
        
        # Check monthly quota
        async with async_session_maker() as db:
            service = UsageService(db)
            has_quota, used, limit = await service.check_quota(key_id, tier)
            
            if not has_quota:
                raise HTTPException(
                    status_code=429,
                    detail=f"Monthly quota exceeded ({limit} queries for {tier} tier). Upgrade at parceldata.ai/pricing",
                )
        
        response = await call_next(request)
        
        # Add usage headers
        response.headers["X-Usage-Remaining"] = str(limit - used)
        response.headers["X-Usage-Limit"] = str(limit)
        
        return response
```

### S11: Add Stripe Config
Update `api/app/config.py` with Stripe settings.

```python
# Add to api/app/config.py

class Settings(BaseSettings):
    # ... existing settings ...
    
    # Stripe
    stripe_secret_key: str = ""
    stripe_publishable_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_pro_price_id: str = ""
    stripe_business_price_id: str = ""
```

### S12: Alembic Migration for Auth Tables
Create migration for API key and usage tables.

```bash
cd /home/numen/dharma/parceldata/api
alembic revision --autogenerate -m "Add auth and usage tables"
alembic upgrade head
```

---

## Acceptance Criteria
- `POST /v1/auth/signup` creates account and returns API key
- API key validation works via Redis cache + database fallback
- Rate limiting enforces per-second and daily limits by tier
- Usage tracking records all API calls
- `GET /v1/account/usage` returns usage summary
- `GET /v1/account/billing` returns billing info
- `POST /webhooks/stripe` handles Stripe events
- Free tier: 3,000 queries/month, 1/second
- Pro tier: 50,000 queries/month, 10/second
- Business tier: 500,000 queries/month, 50/second
- All new code passes `ruff check` and `mypy --strict`
