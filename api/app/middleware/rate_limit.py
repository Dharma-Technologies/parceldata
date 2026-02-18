"""Per-key, tier-based rate limiting middleware backed by Redis."""

import time

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from app.config import settings
from app.database.redis import get_redis

TIER_LIMITS: dict[str, tuple[int, int]] = {
    "free": (settings.rate_limit_free_per_second, settings.rate_limit_free_per_day),
    "pro": (settings.rate_limit_pro_per_second, settings.rate_limit_pro_per_day),
    "business": (
        settings.rate_limit_business_per_second,
        settings.rate_limit_business_per_day,
    ),
    "enterprise": (1000, 10_000_000),
}


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Enforce per-second and per-day rate limits based on API key tier."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Skip if no API key (public endpoints already bypassed auth)
        if not hasattr(request.state, "api_key"):
            return await call_next(request)

        api_key: str = request.state.api_key
        tier: str = request.state.key_info.get("tier", "free")
        per_second, per_day = TIER_LIMITS.get(tier, TIER_LIMITS["free"])

        day_count = 0
        try:
            redis = await get_redis()
            now = int(time.time())
            today = now // 86400

            # Per-second sliding window
            second_key = f"rl:{api_key}:s:{now}"
            second_count = await redis.incr(second_key)
            if second_count == 1:
                await redis.expire(second_key, 2)

            if second_count > per_second:
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": {
                            "code": "RATE_LIMIT_EXCEEDED",
                            "message": (
                                f"Rate limit exceeded ({per_second}/second "
                                f"for {tier} tier)"
                            ),
                        },
                        "data_quality": {
                            "score": 0,
                            "confidence": "none",
                            "message": "No data available",
                        },
                    },
                )

            # Per-day counter
            day_key = f"rl:{api_key}:d:{today}"
            day_count = await redis.incr(day_key)
            if day_count == 1:
                await redis.expire(day_key, 86400)

            if day_count > per_day:
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": {
                            "code": "RATE_LIMIT_EXCEEDED",
                            "message": (
                                f"Daily rate limit exceeded ({per_day}/day "
                                f"for {tier} tier)"
                            ),
                        },
                        "data_quality": {
                            "score": 0,
                            "confidence": "none",
                            "message": "No data available",
                        },
                    },
                )
        except Exception:
            # Redis unavailable — allow request through without rate limiting
            pass

        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(per_day)
        response.headers["X-RateLimit-Remaining"] = str(
            max(0, per_day - day_count)
        )
        response.headers["X-RateLimit-Reset"] = str(
            ((int(time.time()) // 86400) + 1) * 86400
        )

        return response
