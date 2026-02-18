"""Health check and version endpoints."""

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database.connection import get_db
from app.database.redis import get_redis

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check(
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Check API health — database and Redis connectivity."""
    checks: dict[str, str] = {
        "api": "healthy",
        "database": "unknown",
        "redis": "unknown",
    }

    # Database
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = "healthy"
    except Exception as exc:
        checks["database"] = f"unhealthy: {exc}"

    # Redis
    try:
        redis = await get_redis()
        await redis.ping()
        checks["redis"] = "healthy"
    except Exception as exc:
        checks["redis"] = f"unhealthy: {exc}"

    overall = (
        "healthy"
        if all(v == "healthy" for v in checks.values())
        else "degraded"
    )

    return {
        "status": overall,
        "checks": checks,
        "version": settings.app_version,
    }


@router.get("/version")
async def version() -> dict[str, str]:
    """Get API version information."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "api_version": "v1",
    }
