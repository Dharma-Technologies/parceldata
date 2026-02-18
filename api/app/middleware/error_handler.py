"""Global error handler middleware for consistent error responses."""

import uuid

import structlog
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

logger = structlog.get_logger()

ERROR_CODES: dict[int, str] = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    429: "RATE_LIMIT_EXCEEDED",
    500: "INTERNAL_ERROR",
    503: "SERVICE_UNAVAILABLE",
}


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Catch unhandled exceptions and return standard JSON error responses."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id

        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            logger.exception(
                "Unhandled error", request_id=request_id, error=str(exc)
            )
            return _error_response(500, "Internal server error", request_id)


def _error_response(
    status_code: int, message: str, request_id: str
) -> JSONResponse:
    """Build a standard JSON error response."""
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": ERROR_CODES.get(status_code, "UNKNOWN"),
                "message": message,
            },
            "request_id": request_id,
            "data_quality": {
                "score": 0,
                "confidence": "none",
                "message": "No data available",
            },
        },
    )
