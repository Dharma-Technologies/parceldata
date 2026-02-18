"""Property endpoints (placeholder)."""

from typing import Any

from fastapi import APIRouter

router = APIRouter(prefix="/v1/properties", tags=["Properties"])


@router.get("/{property_id}")
async def get_property(property_id: str) -> dict[str, Any]:
    """Get a property by ID (placeholder)."""
    return {"message": "Not implemented yet", "property_id": property_id}
