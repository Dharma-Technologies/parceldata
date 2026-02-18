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

## Current Stage: P10-01-api-foundation

# PRD: P10-01 — API Foundation

## Overview
Establish the core FastAPI application structure with configuration, database connection, authentication, rate limiting, error handling, and health endpoints. This is the foundation all other stages build upon.

---

## Stories

### S1: FastAPI Application Entry Point
Create `api/app/main.py` — the main FastAPI application.

```python
# api/app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.middleware import (
    RateLimitMiddleware,
    AuthenticationMiddleware,
    ErrorHandlerMiddleware,
)
from app.routes import health, properties, analytics, auth

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: connect to database, Redis
    await startup()
    yield
    # Shutdown: close connections
    await shutdown()

app = FastAPI(
    title="ParcelData API",
    description="Real estate data for AI agents",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)
```

- Include lifespan handler for startup/shutdown
- Configure CORS, rate limiting, auth, error handler middleware
- Mount routers for health, properties, analytics, auth
- Set OpenAPI metadata for agent discovery
- Export `app` for uvicorn

### S2: Configuration Module
Create `api/app/config.py` with Pydantic Settings.

```python
# api/app/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    
    # App
    app_name: str = "ParcelData"
    app_version: str = "0.1.0"
    debug: bool = False
    log_level: str = "INFO"
    
    # Database
    database_url: str = "postgresql+asyncpg://parceldata:parceldata@localhost:5432/parceldata"
    database_pool_size: int = 20
    database_max_overflow: int = 10
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # Auth
    api_key_header: str = "X-API-Key"
    auth_header: str = "Authorization"
    
    # Rate Limiting
    rate_limit_free_per_second: int = 1
    rate_limit_free_per_day: int = 100
    rate_limit_pro_per_second: int = 10
    rate_limit_pro_per_day: int = 10000
    rate_limit_business_per_second: int = 50
    rate_limit_business_per_day: int = 500000
    
    # External Services (placeholders)
    regrid_api_key: str = ""
    attom_api_key: str = ""

settings = Settings()
```

- All configuration via environment variables
- Sensible defaults for local development
- Separate settings for each tier's rate limits
- Include placeholders for data provider API keys

### S3: Database Connection Module
Create `api/app/database/connection.py` with async SQLAlchemy.

```python
# api/app/database/connection.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import settings

engine = create_async_engine(
    settings.database_url,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    echo=settings.debug,
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

class Base(DeclarativeBase):
    pass

async def get_db() -> AsyncSession:
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

- Async engine with connection pooling
- Session factory with proper lifecycle
- `get_db` dependency for route handlers
- Base class for all models

### S4: Redis Connection Module
Create `api/app/database/redis.py` for Redis cache and rate limiting.

```python
# api/app/database/redis.py
from redis.asyncio import Redis, from_url
from app.config import settings

redis_client: Redis | None = None

async def get_redis() -> Redis:
    global redis_client
    if redis_client is None:
        redis_client = from_url(settings.redis_url, decode_responses=True)
    return redis_client

async def close_redis() -> None:
    global redis_client
    if redis_client is not None:
        await redis_client.close()
        redis_client = None
```

- Lazy initialization of Redis client
- Async Redis client
- Proper cleanup on shutdown

### S5: Health Check Endpoint
Create `api/app/routes/health.py` with health and version endpoints.

```python
# api/app/routes/health.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.database.connection import get_db
from app.database.redis import get_redis
from app.config import settings

router = APIRouter(tags=["Health"])

@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """Check API health status."""
    checks = {
        "api": "healthy",
        "database": "unknown",
        "redis": "unknown",
    }
    
    # Check database
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = "healthy"
    except Exception as e:
        checks["database"] = f"unhealthy: {str(e)}"
    
    # Check Redis
    try:
        redis = await get_redis()
        await redis.ping()
        checks["redis"] = "healthy"
    except Exception as e:
        checks["redis"] = f"unhealthy: {str(e)}"
    
    overall = "healthy" if all(v == "healthy" for v in checks.values()) else "degraded"
    
    return {
        "status": overall,
        "checks": checks,
        "version": settings.app_version,
    }

@router.get("/version")
async def version():
    """Get API version information."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "api_version": "v1",
    }
```

- Health endpoint checks database AND Redis
- Returns degraded status if any service is down
- Version endpoint for API discovery

### S6: Error Handler Middleware
Create `api/app/middleware/error_handler.py` for consistent error responses.

```python
# api/app/middleware/error_handler.py
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import structlog
import uuid

logger = structlog.get_logger()

ERROR_CODES = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    429: "RATE_LIMIT_EXCEEDED",
    500: "INTERNAL_ERROR",
    503: "SERVICE_UNAVAILABLE",
}

class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id
        
        try:
            response = await call_next(request)
            return response
        except HTTPException as e:
            return self._error_response(e.status_code, e.detail, request_id)
        except Exception as e:
            logger.exception("Unhandled error", request_id=request_id, error=str(e))
            return self._error_response(500, "Internal server error", request_id)
    
    def _error_response(self, status_code: int, message: str, request_id: str):
        return JSONResponse(
            status_code=status_code,
            content={
                "error": {
                    "code": ERROR_CODES.get(status_code, "UNKNOWN"),
                    "message": message,
                },
                "request_id": request_id,
            },
        )
```

- Standard error response format with code, message, request_id
- Catches all unhandled exceptions
- Logs errors with structlog

### S7: Authentication Middleware
Create `api/app/middleware/authentication.py` for API key validation.

```python
# api/app/middleware/authentication.py
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from app.config import settings
from app.database.redis import get_redis

# Paths that don't require authentication
PUBLIC_PATHS = {"/health", "/version", "/docs", "/redoc", "/openapi.json"}

class AuthenticationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        
        # Skip auth for public paths
        if path in PUBLIC_PATHS or path.startswith("/docs") or path.startswith("/redoc"):
            return await call_next(request)
        
        # Extract API key
        api_key = (
            request.headers.get(settings.api_key_header) or
            request.headers.get(settings.auth_header, "").replace("Bearer ", "")
        )
        
        if not api_key:
            raise HTTPException(status_code=401, detail="API key required")
        
        # Validate API key (simple check for now, will be enhanced in auth stage)
        key_info = await self._validate_key(api_key)
        if key_info is None:
            raise HTTPException(status_code=401, detail="Invalid API key")
        
        # Attach key info to request state
        request.state.api_key = api_key
        request.state.key_info = key_info
        
        return await call_next(request)
    
    async def _validate_key(self, api_key: str) -> dict | None:
        """Validate API key and return key info. Returns None if invalid."""
        redis = await get_redis()
        key_data = await redis.hgetall(f"apikey:{api_key}")
        
        if not key_data:
            # For development, accept any key starting with "pk_"
            if api_key.startswith("pk_"):
                return {"tier": "free", "key": api_key}
            return None
        
        return key_data
```

- Supports both `X-API-Key` header and `Authorization: Bearer` header
- Public paths skip authentication
- Key info attached to request state for rate limiting

### S8: Rate Limiting Middleware
Create `api/app/middleware/rate_limit.py` for per-key rate limiting.

```python
# api/app/middleware/rate_limit.py
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from app.config import settings
from app.database.redis import get_redis
import time

TIER_LIMITS = {
    "free": (settings.rate_limit_free_per_second, settings.rate_limit_free_per_day),
    "pro": (settings.rate_limit_pro_per_second, settings.rate_limit_pro_per_day),
    "business": (settings.rate_limit_business_per_second, settings.rate_limit_business_per_day),
    "enterprise": (1000, 10000000),  # Effectively unlimited
}

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for public paths
        if not hasattr(request.state, "api_key"):
            return await call_next(request)
        
        api_key = request.state.api_key
        tier = request.state.key_info.get("tier", "free")
        per_second, per_day = TIER_LIMITS.get(tier, TIER_LIMITS["free"])
        
        redis = await get_redis()
        now = int(time.time())
        today = now // 86400
        
        # Check per-second limit (sliding window)
        second_key = f"rl:{api_key}:s:{now}"
        second_count = await redis.incr(second_key)
        if second_count == 1:
            await redis.expire(second_key, 2)
        
        if second_count > per_second:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded ({per_second}/second for {tier} tier)",
            )
        
        # Check daily limit
        day_key = f"rl:{api_key}:d:{today}"
        day_count = await redis.incr(day_key)
        if day_count == 1:
            await redis.expire(day_key, 86400)
        
        if day_count > per_day:
            raise HTTPException(
                status_code=429,
                detail=f"Daily rate limit exceeded ({per_day}/day for {tier} tier)",
            )
        
        # Add rate limit headers to response
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(per_day)
        response.headers["X-RateLimit-Remaining"] = str(max(0, per_day - day_count))
        response.headers["X-RateLimit-Reset"] = str((today + 1) * 86400)
        
        return response
```

- Per-second and per-day limits
- Tier-based limits (free, pro, business, enterprise)
- Rate limit headers in response
- Redis-backed counters

### S9: Logging Configuration
Create `api/app/logging_config.py` with structlog setup.

```python
# api/app/logging_config.py
import structlog
import logging
from app.config import settings

def configure_logging():
    """Configure structlog for JSON logging."""
    
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer() if not settings.debug else structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.log_level.upper())
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
```

- JSON logging for production
- Console logging for development (debug mode)
- Log level from settings

### S10: CORS Configuration
Update `api/app/main.py` to configure CORS.

```python
# In api/app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"],
)
```

- Allow all origins for development
- Expose rate limit headers
- Document production CORS configuration needed

### S11: Alembic Migration Setup
Initialize Alembic and create initial migration structure.

```bash
cd api
alembic init alembic
```

Update `api/alembic/env.py`:
```python
# api/alembic/env.py
from app.database.connection import Base
from app.config import settings

config.set_main_option("sqlalchemy.url", settings.database_url.replace("+asyncpg", ""))
target_metadata = Base.metadata
```

Create `api/alembic.ini` with proper configuration.

### S12: Startup and Shutdown Handlers
Create `api/app/lifecycle.py` for application lifecycle.

```python
# api/app/lifecycle.py
from app.database.connection import engine
from app.database.redis import get_redis, close_redis
from app.logging_config import configure_logging
import structlog

logger = structlog.get_logger()

async def startup():
    """Initialize services on startup."""
    configure_logging()
    logger.info("Starting ParcelData API")
    
    # Test database connection
    async with engine.begin() as conn:
        await conn.run_sync(lambda _: None)
    logger.info("Database connected")
    
    # Test Redis connection
    redis = await get_redis()
    await redis.ping()
    logger.info("Redis connected")

async def shutdown():
    """Cleanup on shutdown."""
    logger.info("Shutting down ParcelData API")
    
    await close_redis()
    await engine.dispose()
    
    logger.info("Shutdown complete")
```

### S13: Middleware Package Export
Create `api/app/middleware/__init__.py` to export middleware.

```python
# api/app/middleware/__init__.py
from .error_handler import ErrorHandlerMiddleware
from .authentication import AuthenticationMiddleware
from .rate_limit import RateLimitMiddleware

__all__ = [
    "ErrorHandlerMiddleware",
    "AuthenticationMiddleware", 
    "RateLimitMiddleware",
]
```

### S14: Routes Package Setup
Create `api/app/routes/__init__.py` and router mounting.

```python
# api/app/routes/__init__.py
from .health import router as health_router

# Placeholder routers (will be created in later stages)
from fastapi import APIRouter

properties_router = APIRouter(prefix="/v1/properties", tags=["Properties"])
analytics_router = APIRouter(prefix="/v1/analytics", tags=["Analytics"])
auth_router = APIRouter(prefix="/v1/auth", tags=["Authentication"])

# Placeholder endpoints
@properties_router.get("/{property_id}")
async def get_property_placeholder(property_id: str):
    return {"message": "Not implemented yet", "property_id": property_id}
```

### S15: Docker Build Verification
Ensure Docker builds successfully.

```bash
cd /home/numen/dharma/parceldata
docker-compose build api
docker-compose up -d postgres redis
docker-compose up api
```

- Dockerfile builds without errors
- Application starts and connects to database/Redis
- Health endpoint returns healthy

---

## Acceptance Criteria
- FastAPI app starts on port 8000
- `GET /health` returns `{"status": "healthy", ...}`
- `GET /version` returns version info
- Unauthenticated requests to `/v1/*` return 401
- Rate limiting enforces per-second and per-day limits
- Rate limit headers present in responses
- Error responses follow standard format
- Docker builds and runs successfully
- All new code passes `ruff check` and `mypy --strict`
