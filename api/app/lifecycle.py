"""Application startup and shutdown lifecycle handlers."""

import structlog

from app.database.connection import engine
from app.database.redis import close_redis, get_redis
from app.logging_config import configure_logging

logger = structlog.get_logger()


async def startup() -> None:
    """Initialize services on startup."""
    configure_logging()
    logger.info("Starting ParcelData API")

    # Test database connection
    try:
        async with engine.begin() as conn:
            await conn.run_sync(lambda _: None)
        logger.info("Database connected")
    except Exception as exc:
        logger.warning("Database not available", error=str(exc))

    # Test Redis connection
    try:
        redis = await get_redis()
        await redis.ping()
        logger.info("Redis connected")
    except Exception as exc:
        logger.warning("Redis not available", error=str(exc))


async def shutdown() -> None:
    """Cleanup on shutdown."""
    logger.info("Shutting down ParcelData API")

    await close_redis()
    await engine.dispose()

    logger.info("Shutdown complete")
