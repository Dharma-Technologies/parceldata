"""API key authentication middleware."""

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from app.config import settings
from app.database.redis import get_redis

PUBLIC_PATHS: set[str] = {
    "/health",
    "/version",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/v1/auth/signup",
    "/llms.txt",
    "/jsonld",
    "/.well-known/ai-plugin.json",
}

PUBLIC_PREFIXES: tuple[str, ...] = (
    "/docs",
    "/redoc",
    "/webhooks",
    "/v1/docs",
    "/v1/redoc",
    "/.well-known",
)


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Validate API keys for non-public endpoints."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        path = request.url.path

        # Skip auth for public paths
        if path in PUBLIC_PATHS or path.startswith(PUBLIC_PREFIXES):
            return await call_next(request)

        # Extract API key from headers
        api_key = request.headers.get(
            settings.api_key_header
        ) or request.headers.get(settings.auth_header, "").replace(
            "Bearer ", ""
        )

        if not api_key:
            return _auth_error("API key required")

        # Validate key
        key_info = await _validate_key(api_key)
        if key_info is None:
            return _auth_error("Invalid API key")

        # Attach key info to request state for downstream middleware
        request.state.api_key = api_key
        request.state.key_info = key_info

        return await call_next(request)


async def _validate_key(api_key: str) -> dict[str, str] | None:
    """Validate API key against Redis, with dev fallback for pk_ keys."""
    try:
        redis = await get_redis()
        key_data: dict[str, str] = await redis.hgetall(f"apikey:{api_key}")
        if key_data:
            return key_data
    except Exception:
        # Redis unavailable — fall through to dev fallback
        pass

    # Development fallback: accept keys starting with "pk_"
    if api_key.startswith("pk_"):
        return {"tier": "free", "key": api_key}

    return None


def _auth_error(message: str) -> JSONResponse:
    """Return a 401 JSON response."""
    return JSONResponse(
        status_code=401,
        content={
            "error": {
                "code": "UNAUTHORIZED",
                "message": message,
            },
            "data_quality": {
                "score": 0,
                "confidence": "none",
                "message": "No data available",
            },
        },
    )
