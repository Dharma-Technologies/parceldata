"""Search request and response schemas."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.property import DataQualitySchema, PropertyResponse


class SearchRequest(BaseModel):
    """Property search request body."""

    state: str | None = None
    city: str | None = None
    zip: str | None = None
    county: str | None = None
    bounds: dict[str, float] | None = Field(
        None, description="Bounding box: {north, south, east, west}",
    )
    property_type: list[str] | None = None
    bedrooms_min: int | None = None
    bedrooms_max: int | None = None
    bathrooms_min: float | None = None
    sqft_min: int | None = None
    sqft_max: int | None = None
    year_built_min: int | None = None
    year_built_max: int | None = None
    lot_sqft_min: int | None = None
    lot_sqft_max: int | None = None
    price_min: int | None = None
    price_max: int | None = None
    listing_status: list[str] | None = None
    zoning: list[str] | None = None
    limit: int = Field(25, ge=1, le=100)
    offset: int = Field(0, ge=0)
    sort: str = Field("id:asc")


class SearchResponse(BaseModel):
    """Paginated search results."""

    results: list[PropertyResponse]
    total: int
    limit: int
    offset: int
    has_more: bool
    data_quality: DataQualitySchema


class BatchLookupRequest(BaseModel):
    """Batch property lookup request."""

    property_ids: list[str] = Field(..., max_length=100)
    detail: Literal["micro", "standard", "extended", "full"] = (
        "standard"
    )


class BatchLookupResponse(BaseModel):
    """Batch lookup results."""

    results: list[PropertyResponse | None]
    found: int
    not_found: int
    errors: list[str]
    data_quality: DataQualitySchema
