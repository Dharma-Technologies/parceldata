"""Authentication endpoints (placeholder)."""

from typing import Any

from fastapi import APIRouter

router = APIRouter(prefix="/v1/auth", tags=["Authentication"])


@router.post("/keys")
async def create_api_key() -> dict[str, Any]:
    """Create a new API key (placeholder)."""
    return {"message": "Not implemented yet"}
