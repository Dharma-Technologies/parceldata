"""Usage tracking middleware for automatic API metering."""

from __future__ import annotations

import time

import structlog
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from app.database.connection import async_session_maker
from app.services.usage_service import UsageService

logger = structlog.get_logger()


class UsageTrackingMiddleware(BaseHTTPMiddleware):
    """Record API usage for every authenticated /v1/ request."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Track usage after processing the request."""
        # Skip non-API routes
        if not request.url.path.startswith("/v1/"):
            return await call_next(request)

        # Skip if not authenticated
        if not hasattr(request.state, "key_info"):
            return await call_next(request)

        start_time = time.time()
        response = await call_next(request)
        response_time_ms = int((time.time() - start_time) * 1000)

        # Track usage (best effort — don't fail the request)
        try:
            key_info = request.state.key_info
            key_id = key_info.get("id")

            if key_id:
                # Determine query count for batch endpoints
                query_count = 1
                if "/batch" in request.url.path:
                    query_count = getattr(
                        request.state, "batch_count", 1
                    )

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
            logger.debug("usage_tracking_failed", path=request.url.path)

        return response
