"""Property lookup endpoints."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.schemas.property import PropertyMicroResponse, PropertyResponse
from app.services.property_service import PropertyService

router = APIRouter(prefix="/v1/properties", tags=["Properties"])

DetailLevel = Literal["micro", "standard", "extended", "full"]


@router.get(
    "/{property_id}",
    response_model=PropertyResponse | PropertyMicroResponse,
)
async def get_property_by_id(
    property_id: str,
    detail: DetailLevel = "standard",
    db: AsyncSession = Depends(get_db),
) -> PropertyResponse | PropertyMicroResponse:
    """Get property by Dharma Parcel ID.

    Args:
        property_id: Dharma Parcel ID (e.g., TX-TRAVIS-0234567).
        detail: Response detail level (micro, standard, extended, full).
    """
    service = PropertyService(db)
    prop = await service.get_by_id(property_id)
    if not prop:
        raise HTTPException(
            status_code=404,
            detail=f"Property not found: {property_id}",
        )
    return service.to_response(prop, detail)


@router.get(
    "/address/lookup",
    response_model=PropertyResponse | PropertyMicroResponse,
)
async def get_property_by_address(
    street: str = Query(..., description="Street address"),
    city: str = Query(..., description="City name"),
    state: str = Query(..., description="State (2-letter code)"),
    unit: str | None = Query(None, description="Unit/Apt number"),
    zip: str | None = Query(None, description="ZIP code"),
    detail: DetailLevel = "standard",
    db: AsyncSession = Depends(get_db),
) -> PropertyResponse | PropertyMicroResponse:
    """Get property by address components.

    Returns the best match for the given address.
    """
    service = PropertyService(db)
    prop = await service.get_by_address(
        street, city, state, unit, zip,
    )
    if not prop:
        raise HTTPException(
            status_code=404,
            detail="No property found matching the provided address",
        )
    return service.to_response(prop, detail)


@router.get(
    "/coordinates/lookup",
    response_model=PropertyResponse | PropertyMicroResponse,
)
async def get_property_by_coordinates(
    lat: float = Query(..., description="Latitude"),
    lng: float = Query(..., description="Longitude"),
    detail: DetailLevel = "standard",
    db: AsyncSession = Depends(get_db),
) -> PropertyResponse | PropertyMicroResponse:
    """Get property by coordinates.

    Returns the property at or nearest to the given coordinates.
    """
    service = PropertyService(db)
    prop = await service.get_by_coordinates(lat, lng)
    if not prop:
        raise HTTPException(
            status_code=404,
            detail="No property found at the provided coordinates",
        )
    return service.to_response(prop, detail)
