"""Analytics response schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ComparableProperty(BaseModel):
    """A comparable property in the response."""

    property_id: str
    address: str
    distance_miles: float
    sale_date: str | None
    sale_price: int | None
    sqft: int | None
    bedrooms: int | None
    year_built: int | None
    price_per_sqft: float | None
    similarity_score: float


class ComparablesResponse(BaseModel):
    """Response for comparables analysis."""

    subject_property: dict[str, str | int | None]
    comparables: list[ComparableProperty]
    suggested_value: dict[str, int | float | None]
    data_quality: dict[str, float | int | str]


class MarketTrendsResponse(BaseModel):
    """Response for market trend analysis."""

    location: dict[str, str | None]
    period: str
    metrics: dict[str, float | int]
    trends: list[dict[str, str | int | float]] = Field(
        default_factory=list,
    )
    data_quality: dict[str, float | int | str]
