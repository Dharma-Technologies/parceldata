"""Analytics endpoints: comparables and market trends."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.models import Building, Property, Transaction
from app.schemas.analytics import (
    ComparableProperty,
    ComparablesResponse,
    MarketTrendsResponse,
)
from app.services.comparables_service import ComparablesService
from app.services.property_service import PropertyService

router = APIRouter(prefix="/v1/analytics", tags=["Analytics"])


@router.get("/comparables", response_model=ComparablesResponse)
async def get_comparables(
    property_id: str = Query(..., description="Subject property ID"),
    radius_miles: float = Query(1.0, ge=0.1, le=10),
    months: int = Query(6, ge=1, le=24),
    limit: int = Query(10, ge=1, le=25),
    db: AsyncSession = Depends(get_db),
) -> ComparablesResponse:
    """Find comparable sales for a property.

    Returns similar properties that sold within the radius and
    time period, along with a suggested value estimate.
    """
    prop_service = PropertyService(db)
    subject = await prop_service.get_by_id(property_id)

    if not subject:
        raise HTTPException(
            status_code=404, detail="Property not found",
        )

    comp_service = ComparablesService(db)
    comps = await comp_service.find_comparables(
        subject_property=subject,
        radius_miles=radius_miles,
        months=months,
        limit=limit,
    )

    suggested = comp_service.calculate_suggested_value(
        subject, comps,
    )

    subject_building = (
        subject.buildings[0] if subject.buildings else None
    )

    comp_items: list[ComparableProperty] = []
    for c in comps:
        prop = c["property"]
        txn = c["transaction"]
        bldg = c["building"]

        assert isinstance(prop, Property)
        assert isinstance(txn, Transaction)
        assert isinstance(bldg, Building)

        ppsf: float | None = None
        if bldg.sqft and txn.sale_price:
            ppsf = txn.sale_price / bldg.sqft

        comp_items.append(
            ComparableProperty(
                property_id=prop.id,
                address=(
                    prop.address.formatted_address
                    if prop.address
                    else ""
                ),
                distance_miles=0,
                sale_date=(
                    txn.transaction_date.isoformat()
                    if txn.transaction_date
                    else None
                ),
                sale_price=txn.sale_price,
                sqft=bldg.sqft,
                bedrooms=bldg.bedrooms,
                year_built=bldg.year_built,
                price_per_sqft=ppsf,
                similarity_score=float(
                    str(c["similarity_score"]),
                ),
            ),
        )

    avg_quality: float = 0
    if comps:
        avg_quality = sum(
            float(str(getattr(c["property"], "quality_score", 0)))
            for c in comps
        ) / len(comps)

    return ComparablesResponse(
        subject_property={
            "property_id": subject.id,
            "sqft": (
                subject_building.sqft if subject_building else None
            ),
            "bedrooms": (
                subject_building.bedrooms
                if subject_building
                else None
            ),
            "year_built": (
                subject_building.year_built
                if subject_building
                else None
            ),
        },
        comparables=comp_items,
        suggested_value=suggested,
        data_quality={
            "score": avg_quality,
            "comp_count": len(comps),
            "confidence": (
                "high"
                if len(comps) >= 5
                else "medium"
                if len(comps) >= 3
                else "low"
            ),
        },
    )


@router.get("/market-trends", response_model=MarketTrendsResponse)
async def get_market_trends(
    zip: str | None = Query(None),
    city: str | None = Query(None),
    state: str | None = Query(None),
    county: str | None = Query(None),
    property_type: str | None = Query(None),
    period: str = Query(
        "12m", description="3m, 6m, 12m, 24m, 5y",
    ),
    db: AsyncSession = Depends(get_db),
) -> MarketTrendsResponse:
    """Get market statistics and trends for an area.

    Returns price trends, days on market, inventory levels, etc.
    """
    _ = db  # Will use for actual analytics queries
    _ = property_type

    return MarketTrendsResponse(
        location={
            "zip": zip,
            "city": city,
            "state": state,
            "county": county,
        },
        period=period,
        metrics={
            "median_sale_price": 500000,
            "price_per_sqft": 250,
            "days_on_market": 21,
            "inventory_months": 2.5,
            "list_to_sale_ratio": 0.98,
            "total_sales": 150,
            "total_active": 45,
        },
        trends=[
            {
                "month": "2026-01",
                "median_price": 495000,
                "sales_count": 12,
            },
            {
                "month": "2026-02",
                "median_price": 502000,
                "sales_count": 14,
            },
        ],
        data_quality={
            "score": 0.85,
            "confidence": "high",
            "data_points": 150,
        },
    )
