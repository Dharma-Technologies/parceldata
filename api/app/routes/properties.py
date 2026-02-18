"""Property lookup and search endpoints."""

from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.schemas.property import PropertyMicroResponse, PropertyResponse
from app.schemas.search import (
    BatchLookupRequest,
    BatchLookupResponse,
    SearchRequest,
    SearchResponse,
)
from app.services.property_service import PropertyService
from app.services.search_service import SearchFilters, SearchService

router = APIRouter(prefix="/v1/properties", tags=["Properties"])

DetailLevel = Literal["micro", "standard", "extended", "full"]


def _apply_field_selection(
    response: PropertyResponse | PropertyMicroResponse,
    fields: str | None,
    include_provenance: bool,
) -> dict[str, Any] | PropertyResponse | PropertyMicroResponse:
    """Filter response fields based on select parameter."""
    if fields is None and include_provenance:
        return response

    response_dict = response.model_dump()

    if fields is not None:
        field_list = [f.strip() for f in fields.split(",")]
        filtered = {
            k: v for k, v in response_dict.items() if k in field_list
        }
        # Always include data_quality
        filtered["data_quality"] = response_dict["data_quality"]
        return filtered

    if not include_provenance:
        response_dict.pop("provenance", None)

    return response_dict


@router.post("/search", response_model=SearchResponse)
async def search_properties(
    request: SearchRequest,
    detail: DetailLevel = "standard",
    db: AsyncSession = Depends(get_db),
) -> SearchResponse:
    """Search for properties matching criteria.

    Supports filtering by location, property characteristics,
    price, listing status, and zoning.
    """
    filters = SearchFilters(
        **request.model_dump(exclude={"limit", "offset", "sort"}),
    )

    sort_parts = request.sort.split(":")
    sort_field = sort_parts[0]
    sort_order = sort_parts[1] if len(sort_parts) > 1 else "asc"

    search_service = SearchService(db)
    properties, total = await search_service.search(
        filters=filters,
        limit=request.limit,
        offset=request.offset,
        sort_field=sort_field,
        sort_order=sort_order,
    )

    prop_service = PropertyService(db)
    results = [
        prop_service.to_response(p, detail)
        for p in properties
    ]
    full_results: list[PropertyResponse] = []
    for r in results:
        if isinstance(r, PropertyResponse):
            full_results.append(r)

    return SearchResponse(
        results=full_results,
        total=total,
        limit=request.limit,
        offset=request.offset,
        has_more=(request.offset + len(full_results)) < total,
    )


@router.post("/batch", response_model=BatchLookupResponse)
async def batch_lookup(
    request: BatchLookupRequest,
    db: AsyncSession = Depends(get_db),
) -> BatchLookupResponse:
    """Batch property lookup by IDs.

    Returns properties in the same order as requested IDs.
    Maximum 100 properties per request.
    """
    service = PropertyService(db)
    results: list[PropertyResponse | None] = []
    errors: list[str] = []
    found = 0
    not_found = 0

    for prop_id in request.property_ids:
        try:
            prop = await service.get_by_id(prop_id)
            if prop:
                resp = service.to_response(prop, request.detail)
                if isinstance(resp, PropertyResponse):
                    results.append(resp)
                else:
                    results.append(None)
                found += 1
            else:
                results.append(None)
                not_found += 1
        except Exception as e:
            results.append(None)
            errors.append(f"{prop_id}: {e!s}")

    return BatchLookupResponse(
        results=results,
        found=found,
        not_found=not_found,
        errors=errors,
    )


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


@router.get("/{property_id}")
async def get_property_by_id(
    property_id: str,
    detail: DetailLevel = "standard",
    select: str | None = Query(
        None, description="Comma-separated fields to include",
    ),
    include_provenance: bool = Query(
        True, description="Include provenance metadata",
    ),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any] | PropertyResponse | PropertyMicroResponse:
    """Get property by Dharma Parcel ID.

    Args:
        property_id: Dharma Parcel ID (e.g., TX-TRAVIS-0234567).
        detail: Response detail level (micro, standard, extended, full).
        select: Comma-separated field names to include.
        include_provenance: Whether to include provenance metadata.
    """
    service = PropertyService(db)
    prop = await service.get_by_id(property_id)
    if not prop:
        raise HTTPException(
            status_code=404,
            detail=f"Property not found: {property_id}",
        )
    response = service.to_response(prop, detail)
    return _apply_field_selection(
        response, select, include_provenance,
    )
