"""Property search with filters service."""

from __future__ import annotations

from pydantic import BaseModel, Field
from sqlalchemy import ColumnElement, and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Address, Building, Listing, Property, Zoning


class SearchFilters(BaseModel):
    """Validated search filter parameters."""

    # Geographic
    state: str | None = None
    city: str | None = None
    zip: str | None = None
    county: str | None = None
    bounds: dict[str, float] | None = Field(
        None, description="Bounding box: {north, south, east, west}",
    )

    # Property type
    property_type: list[str] | None = None

    # Building
    bedrooms_min: int | None = None
    bedrooms_max: int | None = None
    bathrooms_min: float | None = None
    sqft_min: int | None = None
    sqft_max: int | None = None
    year_built_min: int | None = None
    year_built_max: int | None = None

    # Lot
    lot_sqft_min: int | None = None
    lot_sqft_max: int | None = None

    # Price
    price_min: int | None = None
    price_max: int | None = None

    # Listing
    listing_status: list[str] | None = None

    # Zoning
    zoning: list[str] | None = None


class SearchService:
    """Search properties with filters and pagination."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def search(
        self,
        filters: SearchFilters,
        limit: int = 25,
        offset: int = 0,
        sort_field: str = "id",
        sort_order: str = "asc",
    ) -> tuple[list[Property], int]:
        """Search properties matching filter criteria."""
        stmt = select(Property).options(
            selectinload(Property.address),
            selectinload(Property.buildings),
            selectinload(Property.valuation),
            selectinload(Property.listing),
        )

        conditions: list[ColumnElement[bool]] = []
        need_address_join = False
        need_building_join = False
        need_listing_join = False
        need_zoning_join = False

        # Geographic filters
        if filters.state:
            conditions.append(Address.state == filters.state.upper())
            need_address_join = True
        if filters.city:
            conditions.append(Address.city.ilike(f"%{filters.city}%"))
            need_address_join = True
        if filters.zip:
            conditions.append(Address.zip_code == filters.zip)
            need_address_join = True

        # Property type
        if filters.property_type:
            conditions.append(
                Property.property_type.in_(filters.property_type),
            )

        # Building filters
        if filters.bedrooms_min is not None:
            conditions.append(Building.bedrooms >= filters.bedrooms_min)
            need_building_join = True
        if filters.bedrooms_max is not None:
            conditions.append(Building.bedrooms <= filters.bedrooms_max)
            need_building_join = True
        if filters.bathrooms_min is not None:
            conditions.append(Building.bathrooms >= filters.bathrooms_min)
            need_building_join = True
        if filters.sqft_min is not None:
            conditions.append(Building.sqft >= filters.sqft_min)
            need_building_join = True
        if filters.sqft_max is not None:
            conditions.append(Building.sqft <= filters.sqft_max)
            need_building_join = True
        if filters.year_built_min is not None:
            conditions.append(Building.year_built >= filters.year_built_min)
            need_building_join = True
        if filters.year_built_max is not None:
            conditions.append(Building.year_built <= filters.year_built_max)
            need_building_join = True

        # Lot filters
        if filters.lot_sqft_min is not None:
            conditions.append(Property.lot_sqft >= filters.lot_sqft_min)
        if filters.lot_sqft_max is not None:
            conditions.append(Property.lot_sqft <= filters.lot_sqft_max)

        # Price filters
        if filters.price_min is not None:
            conditions.append(Listing.list_price >= filters.price_min)
            need_listing_join = True
        if filters.price_max is not None:
            conditions.append(Listing.list_price <= filters.price_max)
            need_listing_join = True

        # Listing status
        if filters.listing_status:
            conditions.append(
                Listing.status.in_(filters.listing_status),
            )
            need_listing_join = True

        # Zoning
        if filters.zoning:
            conditions.append(Zoning.zone_code.in_(filters.zoning))
            need_zoning_join = True

        # Apply joins as needed
        if need_address_join:
            stmt = stmt.join(Address)
        if need_building_join:
            stmt = stmt.join(Building)
        if need_listing_join:
            stmt = stmt.join(Listing, isouter=True)
        if need_zoning_join:
            stmt = stmt.join(Zoning, isouter=True)

        # Apply conditions
        if conditions:
            stmt = stmt.where(and_(*conditions))

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar() or 0

        # Sort
        sort_col = getattr(Property, sort_field, Property.id)
        if sort_order == "desc":
            stmt = stmt.order_by(sort_col.desc())
        else:
            stmt = stmt.order_by(sort_col.asc())

        # Paginate
        stmt = stmt.offset(offset).limit(limit)

        result = await self.db.execute(stmt)
        properties = list(result.scalars().all())

        return properties, total
