"""Pydantic response schemas for property API endpoints."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field


class DataQualitySchema(BaseModel):
    """Data quality score included in every response."""

    score: float = Field(..., ge=0, le=1, description="Overall quality score 0-1")
    components: dict[str, float] = Field(default_factory=dict)
    freshness_hours: int = Field(0, description="Hours since last update")
    sources: list[str] = Field(default_factory=list)
    confidence: str = Field("medium", description="low/medium/high")


class ProvenanceSchema(BaseModel):
    """Source tracking for audit and compliance."""

    source_system: str | None = None
    source_type: str | None = None
    extraction_timestamp: datetime | None = None
    transformation_version: str | None = None
    license_type: str | None = None
    attribution_required: bool = False
    last_verified: datetime | None = None


class AddressSchema(BaseModel):
    """Normalized address components."""

    street: str | None = None
    unit: str | None = None
    city: str | None = None
    state: str | None = None
    zip: str | None = None
    zip4: str | None = None
    county: str | None = None
    formatted: str | None = None


class LocationSchema(BaseModel):
    """Geographic coordinates."""

    lat: float | None = None
    lng: float | None = None
    geoid: dict[str, str | None] | None = None


class ParcelSchema(BaseModel):
    """Parcel identification and lot details."""

    apn: str | None = None
    legal_description: str | None = None
    lot_sqft: int | None = None
    lot_acres: float | None = None
    lot_dimensions: str | None = None


class BuildingSchema(BaseModel):
    """Building structure details."""

    sqft: int | None = None
    stories: int | None = None
    bedrooms: int | None = None
    bathrooms: float | None = None
    year_built: int | None = None
    construction: str | None = None
    roof: str | None = None
    foundation: str | None = None
    garage: str | None = None
    garage_spaces: int | None = None
    pool: bool = False


class ValuationSchema(BaseModel):
    """Property value estimates."""

    assessed_total: int | None = None
    assessed_land: int | None = None
    assessed_improvements: int | None = None
    assessed_year: int | None = None
    estimated_value: int | None = None
    estimated_value_low: int | None = None
    estimated_value_high: int | None = None
    price_per_sqft: float | None = None


class OwnershipSchema(BaseModel):
    """Current ownership information."""

    owner_name: str | None = None
    owner_type: str | None = None
    owner_occupied: bool | None = None
    acquisition_date: date | None = None
    acquisition_price: int | None = None
    ownership_length_years: float | None = None


class ZoningSchema(BaseModel):
    """Zoning classification and restrictions."""

    zone_code: str | None = None
    zone_description: str | None = None
    permitted_uses: list[str] = Field(default_factory=list)
    conditional_uses: list[str] = Field(default_factory=list)
    setbacks: dict[str, float | None] | None = None
    max_height: float | None = None
    max_far: float | None = None
    max_impervious: float | None = None


class ListingSchema(BaseModel):
    """MLS listing details."""

    status: str | None = None
    list_price: int | None = None
    list_date: date | None = None
    days_on_market: int | None = None
    mls_number: str | None = None
    listing_agent: dict[str, str | None] | None = None


class TaxSchema(BaseModel):
    """Property tax information."""

    annual_amount: float | None = None
    tax_rate: float | None = None
    exemptions: list[str] = Field(default_factory=list)
    last_paid_date: date | None = None
    delinquent: bool = False


class EnvironmentalSchema(BaseModel):
    """Environmental hazard data."""

    flood_zone: str | None = None
    flood_zone_description: str | None = None
    in_100yr_floodplain: bool = False
    wildfire_risk: str | None = None
    earthquake_risk: str | None = None


class SchoolSchema(BaseModel):
    """Assigned school information."""

    elementary: dict[str, str | int | float | None] | None = None
    middle: dict[str, str | int | float | None] | None = None
    high: dict[str, str | int | float | None] | None = None


class HOASchema(BaseModel):
    """Homeowners association details."""

    name: str | None = None
    fee_monthly: float | None = None
    fee_includes: list[str] = Field(default_factory=list)
    contact_phone: str | None = None


class PropertyResponse(BaseModel):
    """Full property response with all nested schemas."""

    property_id: str
    address: AddressSchema
    location: LocationSchema
    parcel: ParcelSchema
    building: BuildingSchema | None = None
    valuation: ValuationSchema | None = None
    ownership: OwnershipSchema | None = None
    zoning: ZoningSchema | None = None
    listing: ListingSchema | None = None
    tax: TaxSchema | None = None
    environmental: EnvironmentalSchema | None = None
    schools: SchoolSchema | None = None
    hoa: HOASchema | None = None
    data_quality: DataQualitySchema
    provenance: ProvenanceSchema | None = None
    metadata: dict[str, str | list[str] | None] = Field(default_factory=dict)


class PropertyMicroResponse(BaseModel):
    """Minimal response for token efficiency."""

    id: str
    price: int | None = None
    beds: int | None = None
    baths: float | None = None
    sqft: int | None = None
    addr: str | None = None
    data_quality: DataQualitySchema
