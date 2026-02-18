"""ParcelData API — Real estate data for AI agents."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.graphql.schema import graphql_router
from app.lifecycle import shutdown, startup
from app.middleware import (
    AuthenticationMiddleware,
    ErrorHandlerMiddleware,
    RateLimitMiddleware,
    UsageTrackingMiddleware,
)
from app.openapi_config import OPENAPI_TAGS
from app.routes.account import router as account_router
from app.routes.agent_readable import router as agent_readable_router
from app.routes.analytics import router as analytics_router
from app.routes.auth import router as auth_router
from app.routes.health import router as health_router
from app.routes.properties import router as properties_router
from app.routes.webhooks import router as webhooks_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage startup and shutdown of external connections."""
    await startup()
    yield
    await shutdown()


app = FastAPI(
    title="ParcelData.ai API",
    description="""
**Clean, universal real estate data for AI agents.**

ParcelData provides structured property data via REST API, GraphQL, and MCP server.
Every response includes a `data_quality` object with confidence scores.

## Authentication
All endpoints require an API key via `Authorization: Bearer <key>`
or `X-API-Key: <key>` header.

Sign up at `POST /v1/auth/signup` to get your API key.

## Response Detail Levels
Control response size with `?detail=` parameter:
- **micro** (~500-1000 tokens): ID, price, basic stats only
- **standard** (~2000-4000 tokens): Full property details
- **extended** (~8000-16000 tokens): Property + market context
- **full** (~32000+ tokens): Everything + documents

## Rate Limits
- **Free**: 3,000 requests/month
- **Pro**: 50,000 requests/month
- **Business**: 500,000 requests/month
- **Enterprise**: 10,000,000 requests/month

## MCP Server
Connect AI agents via MCP at `mcp://api.parceldata.ai/v1`.
Tools: `property_lookup`, `property_search`, `get_comparables`,
`get_market_trends`, `check_zoning`, `get_permits`,
`get_owner_portfolio`, `estimate_value`, `check_development_feasibility`.
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/v1/docs",
    redoc_url="/v1/redoc",
    openapi_url="/openapi.json",
    openapi_tags=OPENAPI_TAGS,
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    contact={
        "name": "ParcelData.ai Support",
        "url": "https://parceldata.ai",
        "email": "hello@dharma.tech",
    },
    servers=[
        {"url": "https://api.parceldata.ai", "description": "Production"},
        {"url": "http://localhost:8000", "description": "Local development"},
    ],
)

# --- Middleware (applied bottom-up: error → auth → rate limit → usage) ---
app.add_middleware(UsageTrackingMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(AuthenticationMiddleware)
app.add_middleware(ErrorHandlerMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=[
        "X-RateLimit-Limit",
        "X-RateLimit-Remaining",
        "X-RateLimit-Reset",
        "X-Usage-Limit",
        "X-Usage-Remaining",
    ],
)

# --- Routers ---
app.include_router(health_router)
app.include_router(properties_router)
app.include_router(analytics_router)
app.include_router(auth_router)
app.include_router(account_router)
app.include_router(webhooks_router)
app.include_router(agent_readable_router)
app.include_router(graphql_router, prefix="/graphql")

_DATA_QUALITY_NONE = {
    "score": 0,
    "confidence": "none",
    "message": "No data available",
}


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    request: Request, exc: StarletteHTTPException,
) -> JSONResponse:
    """Include data_quality in all HTTP error responses."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "data_quality": _DATA_QUALITY_NONE,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError,
) -> JSONResponse:
    """Include data_quality in validation error responses."""
    return JSONResponse(
        status_code=422,
        content={
            "detail": exc.errors(),
            "data_quality": _DATA_QUALITY_NONE,
        },
    )
