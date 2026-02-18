"""Comparable sales analysis service."""

from __future__ import annotations

from datetime import datetime, timedelta

from geoalchemy2.functions import ST_Distance, ST_DWithin
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Building, Property, Transaction


class ComparablesService:
    """Find and rank comparable property sales."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def find_comparables(
        self,
        subject_property: Property,
        radius_miles: float = 1.0,
        months: int = 6,
        limit: int = 10,
    ) -> list[dict[str, object]]:
        """Find comparable sales for a property."""
        if not subject_property.location:
            return []

        subject_building = (
            subject_property.buildings[0]
            if subject_property.buildings
            else None
        )
        subject_sqft = subject_building.sqft if subject_building else 0
        subject_beds = (
            subject_building.bedrooms if subject_building else 0
        )
        subject_year = (
            subject_building.year_built if subject_building else 2000
        )

        # Convert miles to meters
        radius_meters = radius_miles * 1609.34
        cutoff_date = datetime.utcnow() - timedelta(days=months * 30)

        stmt = (
            select(Property, Transaction, Building)
            .join(Transaction)
            .join(Building)
            .where(
                and_(
                    ST_DWithin(
                        Property.location,
                        subject_property.location,
                        radius_meters,
                    ),
                    Property.id != subject_property.id,
                    Transaction.sale_price.isnot(None),
                    Transaction.transaction_date >= cutoff_date,
                    Property.property_type
                    == subject_property.property_type,
                ),
            )
            .order_by(
                ST_Distance(
                    Property.location, subject_property.location,
                ),
            )
            .limit(limit * 3)
        )

        result = await self.db.execute(stmt)
        candidates = result.all()

        scored_comps: list[dict[str, object]] = []
        for prop, txn, building in candidates:
            score = self._calculate_similarity(
                subject_sqft or 0,
                subject_beds or 0,
                subject_year or 2000,
                building.sqft or 0,
                building.bedrooms or 0,
                building.year_built or 2000,
            )
            scored_comps.append(
                {
                    "property": prop,
                    "transaction": txn,
                    "building": building,
                    "similarity_score": score,
                },
            )

        scored_comps.sort(
            key=lambda x: float(str(x["similarity_score"])),
            reverse=True,
        )
        return scored_comps[:limit]

    @staticmethod
    def _calculate_similarity(
        subj_sqft: int,
        subj_beds: int,
        subj_year: int,
        comp_sqft: int,
        comp_beds: int,
        comp_year: int,
    ) -> float:
        """Calculate similarity score between subject and comp."""
        sqft_diff = abs(subj_sqft - comp_sqft) / max(subj_sqft, 1)
        sqft_score = max(0.0, 1.0 - sqft_diff / 0.2)

        bed_diff = abs(subj_beds - comp_beds)
        bed_score = max(0.0, 1.0 - bed_diff * 0.25)

        year_diff = abs(subj_year - comp_year)
        year_score = max(0.0, 1.0 - year_diff / 10.0)

        return (sqft_score * 0.4) + (bed_score * 0.3) + (year_score * 0.3)

    @staticmethod
    def calculate_suggested_value(
        subject_property: Property,
        comparables: list[dict[str, object]],
    ) -> dict[str, int | float | None]:
        """Calculate suggested value from comparables."""
        if not comparables:
            return {
                "estimate": None,
                "range_low": None,
                "range_high": None,
                "confidence": 0,
            }

        subject_building = (
            subject_property.buildings[0]
            if subject_property.buildings
            else None
        )
        subject_sqft = (
            subject_building.sqft if subject_building else 0
        )

        total_weight = 0.0
        weighted_ppsf = 0.0

        for comp in comparables:
            txn = comp["transaction"]
            building = comp["building"]
            similarity = float(str(comp["similarity_score"]))

            assert isinstance(txn, Transaction)
            assert isinstance(building, Building)

            if building.sqft and txn.sale_price:
                ppsf = txn.sale_price / building.sqft
                weighted_ppsf += ppsf * similarity
                total_weight += similarity

        if total_weight == 0 or not subject_sqft:
            return {
                "estimate": None,
                "range_low": None,
                "range_high": None,
                "confidence": 0,
            }

        avg_ppsf = weighted_ppsf / total_weight
        estimate = int(avg_ppsf * subject_sqft)

        return {
            "estimate": estimate,
            "range_low": int(estimate * 0.9),
            "range_high": int(estimate * 1.1),
            "confidence": min(
                total_weight / len(comparables), 1.0,
            ),
        }
