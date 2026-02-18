"""Redis client for caching and rate limiting."""

from __future__ import annotations

from redis.asyncio import Redis
from redis.asyncio import from_url as redis_from_url

from app.config import settings

_redis_client: Redis | None = None  # type: ignore[type-arg]


async def get_redis() -> Redis:  # type: ignore[type-arg]
    """Get or create the global async Redis client."""
    global _redis_client  # noqa: PLW0603
    if _redis_client is None:
        _redis_client = redis_from_url(
            settings.redis_url, decode_responses=True
        )
    return _redis_client


async def close_redis() -> None:
    """Close the Redis connection."""
    global _redis_client  # noqa: PLW0603
    if _redis_client is not None:
        await _redis_client.close()
        _redis_client = None
