"""Analytics endpoints (placeholder)."""

from typing import Any

from fastapi import APIRouter

router = APIRouter(prefix="/v1/analytics", tags=["Analytics"])


@router.get("/comparables")
async def get_comparables(property_id: str) -> dict[str, Any]:
    """Get comparable properties (placeholder)."""
    return {"message": "Not implemented yet", "property_id": property_id}
