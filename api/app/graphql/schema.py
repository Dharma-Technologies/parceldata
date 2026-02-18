"""Strawberry GraphQL schema for property queries."""

from __future__ import annotations

import strawberry
from strawberry.fastapi import GraphQLRouter

from app.database.connection import async_session_maker
from app.services.property_service import PropertyService


@strawberry.type
class AddressType:
    """GraphQL address type."""

    street: str | None
    city: str | None
    state: str | None
    zip: str | None
    formatted: str | None


@strawberry.type
class BuildingType:
    """GraphQL building type."""

    sqft: int | None
    bedrooms: int | None
    bathrooms: float | None
    year_built: int | None
    stories: int | None


@strawberry.type
class ValuationType:
    """GraphQL valuation type."""

    assessed_total: int | None
    estimated_value: int | None
    price_per_sqft: float | None


@strawberry.type
class ZoningType:
    """GraphQL zoning type."""

    zone_code: str | None
    zone_description: str | None
    permitted_uses: list[str]
    max_height: float | None
    max_far: float | None


@strawberry.type
class DataQualityType:
    """GraphQL data quality type."""

    score: float
    freshness_hours: int
    confidence: str


@strawberry.type
class PropertyType:
    """GraphQL property type."""

    id: str
    address: AddressType | None
    building: BuildingType | None
    valuation: ValuationType | None
    zoning: ZoningType | None
    data_quality: DataQualityType


@strawberry.type
class Query:
    """Root GraphQL query type."""

    @strawberry.field
    async def property(self, id: str) -> PropertyType | None:
        """Look up a single property by ID."""
        async with async_session_maker() as db:
            service = PropertyService(db)
            prop = await service.get_by_id(id)
            if not prop:
                return None

            addr = prop.address
            bldg = (
                prop.buildings[0] if prop.buildings else None
            )
            val = prop.valuation
            zn = prop.zoning

            return PropertyType(
                id=prop.id,
                address=AddressType(
                    street=(
                        addr.street_address if addr else None
                    ),
                    city=addr.city if addr else None,
                    state=addr.state if addr else None,
                    zip=addr.zip_code if addr else None,
                    formatted=(
                        addr.formatted_address if addr else None
                    ),
                )
                if addr
                else None,
                building=BuildingType(
                    sqft=bldg.sqft if bldg else None,
                    bedrooms=bldg.bedrooms if bldg else None,
                    bathrooms=bldg.bathrooms if bldg else None,
                    year_built=(
                        bldg.year_built if bldg else None
                    ),
                    stories=bldg.stories if bldg else None,
                )
                if bldg
                else None,
                valuation=ValuationType(
                    assessed_total=(
                        val.assessed_total if val else None
                    ),
                    estimated_value=(
                        val.estimated_value if val else None
                    ),
                    price_per_sqft=(
                        val.price_per_sqft if val else None
                    ),
                )
                if val
                else None,
                zoning=ZoningType(
                    zone_code=zn.zone_code if zn else None,
                    zone_description=(
                        zn.zone_description if zn else None
                    ),
                    permitted_uses=(
                        zn.permitted_uses if zn else []
                    ),
                    max_height=(
                        zn.max_height_ft if zn else None
                    ),
                    max_far=zn.max_far if zn else None,
                )
                if zn
                else None,
                data_quality=DataQualityType(
                    score=prop.quality_score,
                    freshness_hours=prop.freshness_hours,
                    confidence=(
                        "high"
                        if prop.quality_score >= 0.85
                        else "medium"
                    ),
                ),
            )


schema = strawberry.Schema(query=Query)
graphql_router = GraphQLRouter(schema)
