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
)
from app.routes.account import router as account_router
from app.routes.analytics import router as analytics_router
from app.routes.auth import router as auth_router
from app.routes.health import router as health_router
from app.routes.properties import router as properties_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage startup and shutdown of external connections."""
    await startup()
    yield
    await shutdown()


app = FastAPI(
    title="ParcelData API",
    description="""
ParcelData API provides clean, normalized real estate data for AI agents.

## Authentication
All endpoints require an API key via `Authorization: Bearer <key>`
or `X-API-Key: <key>`.

## Response Detail Levels
- **micro**: Minimal response (~500 tokens)
- **standard**: Full property details (~2000 tokens)
- **extended**: Property + market context (~8000 tokens)
- **full**: Everything + documents (~32000 tokens)

## Data Quality
Every response includes a `data_quality` object with confidence scores.
    """,
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    openapi_tags=[
        {
            "name": "Properties",
            "description": "Property lookup and search",
        },
        {
            "name": "Analytics",
            "description": "Comparables and market trends",
        },
        {
            "name": "Health",
            "description": "API health and version",
        },
    ],
)

# --- Middleware (applied bottom-up: error → auth → rate limit) ---
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
    ],
)

# --- Routers ---
app.include_router(health_router)
app.include_router(properties_router)
app.include_router(analytics_router)
app.include_router(auth_router)
app.include_router(account_router)
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
