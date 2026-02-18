"""Per-key, tier-based rate limiting middleware backed by Redis."""

from __future__ import annotations

import time
from datetime import date

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

# Monthly quota limits by tier
MONTHLY_QUOTAS: dict[str, int] = {
    "free": 3000,
    "pro": 50000,
    "business": 500000,
    "enterprise": 10000000,
}

_DATA_QUALITY_NONE = {
    "score": 0,
    "confidence": "none",
    "message": "No data available",
}


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Enforce per-second, per-day rate limits and monthly quotas."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Check rate limits and quotas before processing."""
        # Skip if no API key (public endpoints already bypassed auth)
        if not hasattr(request.state, "api_key"):
            return await call_next(request)

        api_key: str = request.state.api_key
        tier: str = request.state.key_info.get("tier", "free")
        per_second, per_day = TIER_LIMITS.get(tier, TIER_LIMITS["free"])
        monthly_quota = MONTHLY_QUOTAS.get(tier, 3000)

        day_count = 0
        monthly_used = 0
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
                        "data_quality": _DATA_QUALITY_NONE,
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
                        "data_quality": _DATA_QUALITY_NONE,
                    },
                )

            # Monthly quota check
            key_id = request.state.key_info.get("id")
            if key_id:
                today_str = date.today().isoformat()
                usage_key = f"usage:{key_id}:{today_str}"
                monthly_used = int(await redis.get(usage_key) or 0)

                if monthly_used >= monthly_quota:
                    return JSONResponse(
                        status_code=429,
                        content={
                            "error": {
                                "code": "QUOTA_EXCEEDED",
                                "message": (
                                    f"Monthly quota exceeded ({monthly_quota} "
                                    f"queries for {tier} tier). "
                                    "Upgrade at parceldata.ai/pricing"
                                ),
                            },
                            "data_quality": _DATA_QUALITY_NONE,
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

        # Add usage headers
        response.headers["X-Usage-Limit"] = str(monthly_quota)
        response.headers["X-Usage-Remaining"] = str(
            max(0, monthly_quota - monthly_used)
        )

        return response
