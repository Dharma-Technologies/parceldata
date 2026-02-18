"""Tests for Pydantic response schemas."""

from __future__ import annotations

from datetime import date, datetime

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


class TestDataQualitySchema:
    def test_required_score(self) -> None:
        dq = DataQualitySchema(score=0.87)
        assert dq.score == 0.87
        assert dq.confidence == "medium"
        assert dq.freshness_hours == 0

    def test_score_bounds(self) -> None:
        dq = DataQualitySchema(score=0.0)
        assert dq.score == 0.0
        dq = DataQualitySchema(score=1.0)
        assert dq.score == 1.0

    def test_full_quality(self) -> None:
        dq = DataQualitySchema(
            score=0.92,
            components={
                "completeness": 0.95,
                "accuracy": 0.90,
            },
            freshness_hours=6,
            sources=["travis_cad"],
            confidence="high",
        )
        assert dq.components["completeness"] == 0.95
        assert dq.sources == ["travis_cad"]


class TestProvenanceSchema:
    def test_defaults(self) -> None:
        p = ProvenanceSchema()
        assert p.source_system is None
        assert p.attribution_required is False

    def test_full(self) -> None:
        p = ProvenanceSchema(
            source_system="travis_cad",
            source_type="county_assessor",
            extraction_timestamp=datetime(2026, 1, 1),
            transformation_version="1.0",
        )
        assert p.source_system == "travis_cad"


class TestAddressSchema:
    def test_empty(self) -> None:
        a = AddressSchema()
        assert a.street is None
        assert a.formatted is None

    def test_full(self) -> None:
        a = AddressSchema(
            street="123 Main St",
            city="Austin",
            state="TX",
            zip="78701",
            formatted="123 Main St, Austin, TX 78701",
        )
        assert a.city == "Austin"


class TestLocationSchema:
    def test_coordinates(self) -> None:
        loc = LocationSchema(lat=30.2672, lng=-97.7431)
        assert loc.lat == 30.2672
        assert loc.lng == -97.7431


class TestParcelSchema:
    def test_lot_info(self) -> None:
        p = ParcelSchema(apn="0234567", lot_sqft=8500, lot_acres=0.195)
        assert p.apn == "0234567"
        assert p.lot_sqft == 8500


class TestBuildingSchema:
    def test_building_details(self) -> None:
        b = BuildingSchema(
            sqft=2000,
            bedrooms=3,
            bathrooms=2.5,
            year_built=2005,
            pool=True,
        )
        assert b.sqft == 2000
        assert b.pool is True

    def test_defaults(self) -> None:
        b = BuildingSchema()
        assert b.pool is False


class TestValuationSchema:
    def test_values(self) -> None:
        v = ValuationSchema(
            assessed_total=350000,
            estimated_value=425000,
            price_per_sqft=212.5,
        )
        assert v.assessed_total == 350000


class TestOwnershipSchema:
    def test_owner(self) -> None:
        o = OwnershipSchema(
            owner_name="Jane Smith",
            owner_occupied=True,
            acquisition_date=date(2020, 6, 15),
            acquisition_price=375000,
        )
        assert o.owner_name == "Jane Smith"
        assert o.acquisition_date == date(2020, 6, 15)


class TestZoningSchema:
    def test_zoning(self) -> None:
        z = ZoningSchema(
            zone_code="SF-3",
            permitted_uses=["single_family", "adu"],
            max_height=35.0,
        )
        assert z.zone_code == "SF-3"
        assert len(z.permitted_uses) == 2


class TestListingSchema:
    def test_listing(self) -> None:
        ls = ListingSchema(
            status="active",
            list_price=499000,
            mls_number="MLS-12345",
        )
        assert ls.status == "active"


class TestTaxSchema:
    def test_tax(self) -> None:
        t = TaxSchema(
            annual_amount=8500.0,
            tax_rate=0.0245,
            exemptions=["homestead"],
            delinquent=False,
        )
        assert t.annual_amount == 8500.0
        assert t.exemptions == ["homestead"]


class TestEnvironmentalSchema:
    def test_environmental(self) -> None:
        e = EnvironmentalSchema(
            flood_zone="X",
            wildfire_risk="low",
        )
        assert e.in_100yr_floodplain is False


class TestSchoolSchema:
    def test_schools(self) -> None:
        s = SchoolSchema(
            elementary={"name": "Oak Hill Elementary", "rating": 8},
            middle={"name": "Bailey Middle", "rating": 7},
        )
        assert s.elementary is not None
        assert s.elementary["name"] == "Oak Hill Elementary"


class TestHOASchema:
    def test_hoa(self) -> None:
        h = HOASchema(
            name="Sunset HOA",
            fee_monthly=250.0,
            fee_includes=["pool", "landscaping"],
        )
        assert h.name == "Sunset HOA"


class TestPropertyResponse:
    def test_minimal(self) -> None:
        resp = PropertyResponse(
            property_id="TX-TRAVIS-ABC123",
            address=AddressSchema(),
            location=LocationSchema(),
            parcel=ParcelSchema(),
            data_quality=DataQualitySchema(score=0.5),
        )
        assert resp.property_id == "TX-TRAVIS-ABC123"
        assert resp.data_quality.score == 0.5
        assert resp.building is None

    def test_full(self) -> None:
        resp = PropertyResponse(
            property_id="TX-TRAVIS-ABC123",
            address=AddressSchema(city="Austin", state="TX"),
            location=LocationSchema(lat=30.27, lng=-97.74),
            parcel=ParcelSchema(apn="0234567"),
            building=BuildingSchema(sqft=2000, bedrooms=3),
            valuation=ValuationSchema(estimated_value=500000),
            data_quality=DataQualitySchema(
                score=0.92, confidence="high"
            ),
            provenance=ProvenanceSchema(source_system="travis_cad"),
            metadata={"last_updated": "2026-01-15T00:00:00"},
        )
        assert resp.building is not None
        assert resp.building.sqft == 2000
        assert resp.provenance is not None

    def test_serialization(self) -> None:
        resp = PropertyResponse(
            property_id="TX-TRAVIS-ABC123",
            address=AddressSchema(city="Austin"),
            location=LocationSchema(),
            parcel=ParcelSchema(),
            data_quality=DataQualitySchema(score=0.8),
        )
        data = resp.model_dump()
        assert data["property_id"] == "TX-TRAVIS-ABC123"
        assert data["data_quality"]["score"] == 0.8
        assert "address" in data


class TestPropertyMicroResponse:
    def test_micro(self) -> None:
        resp = PropertyMicroResponse(
            id="TX-TRAVIS-ABC123",
            price=450000,
            beds=3,
            baths=2.0,
            sqft=1800,
            addr="123 Main St, Austin TX",
            data_quality=DataQualitySchema(score=0.75),
        )
        assert resp.id == "TX-TRAVIS-ABC123"
        assert resp.price == 450000
        assert resp.data_quality.score == 0.75

    def test_minimal(self) -> None:
        resp = PropertyMicroResponse(
            id="TX-TRAVIS-ABC123",
            data_quality=DataQualitySchema(score=0.5),
        )
        assert resp.price is None
        assert resp.beds is None
