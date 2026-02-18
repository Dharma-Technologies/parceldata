"""Property lookup and response conversion service."""

from __future__ import annotations

from geoalchemy2.functions import ST_DWithin, ST_MakePoint, ST_SetSRID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.base import ExecutableOption

from app.models import (
    HOA,
    Address,
    Building,
    Environmental,
    Listing,
    Ownership,
    Property,
    School,
    Tax,
    Valuation,
    Zoning,
)
from app.schemas.property import (
    AddressSchema,
    BuildingSchema,
    DataQualitySchema,
    EnvironmentalSchema,
    HOASchema,
    ListingSchema,
    LocationSchema,
    OwnershipSchema,
    ParcelSchema,
    PropertyMicroResponse,
    PropertyResponse,
    ProvenanceSchema,
    SchoolSchema,
    TaxSchema,
    ValuationSchema,
    ZoningSchema,
)


def _all_eager_loads() -> list[ExecutableOption]:
    """Return selectinload options for all Property relationships."""
    return [
        selectinload(Property.address),
        selectinload(Property.buildings),
        selectinload(Property.valuation),
        selectinload(Property.ownership),
        selectinload(Property.zoning),
        selectinload(Property.listing),
        selectinload(Property.environmental),
        selectinload(Property.school),
        selectinload(Property.tax),
        selectinload(Property.hoa),
    ]


class PropertyService:
    """Lookup and convert Property model instances."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, property_id: str) -> Property | None:
        """Get property by Dharma Parcel ID."""
        stmt = select(Property).options(*_all_eager_loads()).where(
            Property.id == property_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    async def get_by_address(
        self,
        street: str,
        city: str,
        state: str,
        unit: str | None = None,
        zip_code: str | None = None,
    ) -> Property | None:
        """Get property by address components."""
        stmt = (
            select(Property)
            .join(Address)
            .options(*_all_eager_loads())
            .where(
                Address.street_address.ilike(f"%{street}%"),
                Address.city.ilike(city),
                Address.state == state.upper(),
            )
        )
        if zip_code:
            stmt = stmt.where(Address.zip_code == zip_code)

        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    async def get_by_coordinates(
        self,
        lat: float,
        lng: float,
        radius_meters: float = 50,
    ) -> Property | None:
        """Get property by lat/lng coordinates."""
        point = ST_SetSRID(ST_MakePoint(lng, lat), 4326)
        stmt = (
            select(Property)
            .options(*_all_eager_loads())
            .where(ST_DWithin(Property.location, point, radius_meters))
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    def to_response(
        self,
        prop: Property,
        detail: str = "standard",
    ) -> PropertyResponse | PropertyMicroResponse:
        """Convert a Property model instance to a response schema."""
        if detail == "micro":
            return self._to_micro(prop)
        return self._to_full(prop)

    # -- private helpers -------------------------------------------------

    def _to_micro(self, prop: Property) -> PropertyMicroResponse:
        building = prop.buildings[0] if prop.buildings else None
        return PropertyMicroResponse(
            id=prop.id,
            price=(
                prop.valuation.estimated_value if prop.valuation else None
            ),
            beds=building.bedrooms if building else None,
            baths=building.bathrooms if building else None,
            sqft=building.sqft if building else None,
            addr=(
                prop.address.formatted_address if prop.address else None
            ),
            data_quality=self._quality(prop),
        )

    def _to_full(self, prop: Property) -> PropertyResponse:
        return PropertyResponse(
            property_id=prop.id,
            address=self._address(prop.address),
            location=self._location(prop),
            parcel=self._parcel(prop),
            building=self._building(
                prop.buildings[0] if prop.buildings else None,
            ),
            valuation=self._valuation(prop.valuation),
            ownership=self._ownership(prop.ownership),
            zoning=self._zoning(prop.zoning),
            listing=self._listing(prop.listing),
            tax=self._tax(prop.tax),
            environmental=self._environmental(prop.environmental),
            schools=self._school(prop.school),
            hoa=self._hoa(prop.hoa),
            data_quality=self._quality(prop),
            provenance=self._provenance(prop),
            metadata={
                "last_updated": (
                    prop.updated_at.isoformat()
                    if prop.updated_at
                    else None
                ),
                "data_sources": (
                    [prop.source_system] if prop.source_system else []
                ),
            },
        )

    @staticmethod
    def _address(addr: Address | None) -> AddressSchema:
        if addr is None:
            return AddressSchema()
        return AddressSchema(
            street=addr.street_address,
            unit=addr.unit_number,
            city=addr.city,
            state=addr.state,
            zip=addr.zip_code,
            zip4=addr.zip4,
            county=addr.county,
            formatted=addr.formatted_address,
        )

    @staticmethod
    def _location(prop: Property) -> LocationSchema:
        addr = prop.address
        return LocationSchema(
            lat=addr.latitude if addr else None,
            lng=addr.longitude if addr else None,
            geoid={
                "census_tract": prop.census_tract,
                "census_block_group": prop.census_block_group,
            },
        )

    @staticmethod
    def _parcel(prop: Property) -> ParcelSchema:
        return ParcelSchema(
            apn=prop.county_apn,
            legal_description=prop.legal_description,
            lot_sqft=prop.lot_sqft,
            lot_acres=prop.lot_acres,
            lot_dimensions=prop.lot_dimensions,
        )

    @staticmethod
    def _building(bldg: Building | None) -> BuildingSchema | None:
        if bldg is None:
            return None
        return BuildingSchema(
            sqft=bldg.sqft,
            stories=bldg.stories,
            bedrooms=bldg.bedrooms,
            bathrooms=bldg.bathrooms,
            year_built=bldg.year_built,
            construction=bldg.construction_type,
            roof=bldg.roof_type,
            foundation=bldg.foundation_type,
            garage=bldg.garage_type,
            garage_spaces=bldg.garage_spaces,
            pool=bldg.pool,
        )

    @staticmethod
    def _valuation(val: Valuation | None) -> ValuationSchema | None:
        if val is None:
            return None
        return ValuationSchema(
            assessed_total=val.assessed_total,
            assessed_land=val.assessed_land,
            assessed_improvements=val.assessed_improvements,
            assessed_year=val.assessed_year,
            estimated_value=val.estimated_value,
            estimated_value_low=val.estimated_value_low,
            estimated_value_high=val.estimated_value_high,
            price_per_sqft=val.price_per_sqft,
        )

    @staticmethod
    def _ownership(own: Ownership | None) -> OwnershipSchema | None:
        if own is None:
            return None
        return OwnershipSchema(
            owner_name=own.owner_name,
            owner_type=own.owner_type,
            owner_occupied=own.owner_occupied,
            acquisition_date=own.acquisition_date,
            acquisition_price=own.acquisition_price,
            ownership_length_years=own.ownership_length_years,
        )

    @staticmethod
    def _zoning(z: Zoning | None) -> ZoningSchema | None:
        if z is None:
            return None
        return ZoningSchema(
            zone_code=z.zone_code,
            zone_description=z.zone_description,
            permitted_uses=z.permitted_uses or [],
            conditional_uses=z.conditional_uses or [],
            setbacks={
                "front": z.setback_front_ft,
                "rear": z.setback_rear_ft,
                "side": z.setback_side_ft,
            },
            max_height=z.max_height_ft,
            max_far=z.max_far,
            max_impervious=z.max_lot_coverage,
        )

    @staticmethod
    def _listing(lst: Listing | None) -> ListingSchema | None:
        if lst is None:
            return None
        return ListingSchema(
            status=lst.status,
            list_price=lst.list_price,
            list_date=lst.list_date,
            days_on_market=lst.days_on_market,
            mls_number=lst.mls_number,
            listing_agent={
                "name": lst.listing_agent_name,
                "phone": lst.listing_agent_phone,
                "email": lst.listing_agent_email,
            },
        )

    @staticmethod
    def _tax(t: Tax | None) -> TaxSchema | None:
        if t is None:
            return None
        return TaxSchema(
            annual_amount=t.annual_amount,
            tax_rate=t.tax_rate,
            exemptions=t.exemptions or [],
            last_paid_date=t.last_paid_date,
            delinquent=t.delinquent,
        )

    @staticmethod
    def _environmental(
        env: Environmental | None,
    ) -> EnvironmentalSchema | None:
        if env is None:
            return None
        return EnvironmentalSchema(
            flood_zone=env.flood_zone,
            flood_zone_description=env.flood_zone_description,
            in_100yr_floodplain=env.in_100yr_floodplain or False,
            wildfire_risk=env.wildfire_risk,
            earthquake_risk=env.earthquake_risk,
        )

    @staticmethod
    def _school(sch: School | None) -> SchoolSchema | None:
        if sch is None:
            return None
        return SchoolSchema(
            elementary={
                "name": sch.elementary_name,
                "id": sch.elementary_id,
                "rating": sch.elementary_rating,
                "distance_miles": sch.elementary_distance_miles,
            },
            middle={
                "name": sch.middle_name,
                "id": sch.middle_id,
                "rating": sch.middle_rating,
                "distance_miles": sch.middle_distance_miles,
            },
            high={
                "name": sch.high_name,
                "id": sch.high_id,
                "rating": sch.high_rating,
                "distance_miles": sch.high_distance_miles,
            },
        )

    @staticmethod
    def _hoa(hoa: HOA | None) -> HOASchema | None:
        if hoa is None:
            return None
        return HOASchema(
            name=hoa.hoa_name,
            fee_monthly=hoa.fee_monthly,
            fee_includes=hoa.fee_includes or [],
            contact_phone=hoa.contact_phone,
        )

    @staticmethod
    def _quality(prop: Property) -> DataQualitySchema:
        return DataQualitySchema(
            score=prop.quality_score,
            components={
                "completeness": prop.quality_completeness,
                "accuracy": prop.quality_accuracy,
                "consistency": prop.quality_consistency,
                "timeliness": prop.quality_timeliness,
                "validity": prop.quality_validity,
                "uniqueness": prop.quality_uniqueness,
            },
            freshness_hours=prop.freshness_hours,
            sources=(
                [prop.source_system] if prop.source_system else []
            ),
            confidence=(
                "high"
                if prop.quality_score >= 0.85
                else "medium"
                if prop.quality_score >= 0.7
                else "low"
            ),
        )

    @staticmethod
    def _provenance(prop: Property) -> ProvenanceSchema:
        return ProvenanceSchema(
            source_system=prop.source_system,
            source_type=prop.source_type,
            extraction_timestamp=prop.extraction_timestamp,
            transformation_version=prop.transformation_version,
        )
