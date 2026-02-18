"""Tests for PropertyService model-to-schema conversion."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock

from app.schemas.property import (
    PropertyMicroResponse,
    PropertyResponse,
)
from app.services.property_service import PropertyService


def _mock_property(
    *,
    with_address: bool = True,
    with_building: bool = True,
    with_valuation: bool = True,
) -> MagicMock:
    """Create a mock Property for testing conversions."""
    prop = MagicMock()
    prop.id = "TX-TRAVIS-ABC123"
    prop.county_apn = "0234567"
    prop.legal_description = "LOT 5 BLK 3"
    prop.lot_sqft = 8500
    prop.lot_acres = 0.195
    prop.lot_dimensions = "85x100"
    prop.census_tract = "48453001234"
    prop.census_block_group = "1"
    prop.property_type = "single_family"
    prop.source_system = "travis_cad"
    prop.source_type = "county_assessor"
    prop.extraction_timestamp = datetime(2026, 1, 15)
    prop.transformation_version = "1.0"
    prop.updated_at = datetime(2026, 1, 15, 12, 0, 0)

    # Quality mixin
    prop.quality_score = 0.87
    prop.quality_completeness = 0.92
    prop.quality_accuracy = 0.95
    prop.quality_consistency = 0.88
    prop.quality_timeliness = 0.80
    prop.quality_validity = 0.99
    prop.quality_uniqueness = 0.98
    prop.freshness_hours = 12

    if with_address:
        addr = MagicMock()
        addr.street_address = "123 Main St"
        addr.unit_number = None
        addr.city = "Austin"
        addr.state = "TX"
        addr.zip_code = "78701"
        addr.zip4 = "1234"
        addr.county = "Travis"
        addr.formatted_address = "123 Main St, Austin, TX 78701"
        addr.latitude = 30.2672
        addr.longitude = -97.7431
        prop.address = addr
    else:
        prop.address = None

    if with_building:
        bldg = MagicMock()
        bldg.sqft = 2000
        bldg.stories = 2
        bldg.bedrooms = 3
        bldg.bathrooms = 2.5
        bldg.year_built = 2005
        bldg.construction_type = "frame"
        bldg.roof_type = "composition"
        bldg.foundation_type = "slab"
        bldg.garage_type = "attached"
        bldg.garage_spaces = 2
        bldg.pool = True
        prop.buildings = [bldg]
    else:
        prop.buildings = []

    if with_valuation:
        val = MagicMock()
        val.assessed_total = 350000
        val.assessed_land = 100000
        val.assessed_improvements = 250000
        val.assessed_year = 2025
        val.estimated_value = 425000
        val.estimated_value_low = 400000
        val.estimated_value_high = 450000
        val.price_per_sqft = 212.5
        prop.valuation = val
    else:
        prop.valuation = None

    # Optional relationships not set
    prop.ownership = None
    prop.zoning = None
    prop.listing = None
    prop.tax = None
    prop.environmental = None
    prop.school = None
    prop.hoa = None

    return prop


class TestToResponse:
    def test_full_response(self) -> None:
        db = MagicMock()
        service = PropertyService(db)
        prop = _mock_property()
        resp = service.to_response(prop, "standard")

        assert isinstance(resp, PropertyResponse)
        assert resp.property_id == "TX-TRAVIS-ABC123"
        assert resp.address.city == "Austin"
        assert resp.location.lat == 30.2672
        assert resp.parcel.apn == "0234567"
        assert resp.building is not None
        assert resp.building.sqft == 2000
        assert resp.valuation is not None
        assert resp.valuation.estimated_value == 425000
        assert resp.data_quality.score == 0.87
        assert resp.data_quality.confidence == "high"

    def test_micro_response(self) -> None:
        db = MagicMock()
        service = PropertyService(db)
        prop = _mock_property()
        resp = service.to_response(prop, "micro")

        assert isinstance(resp, PropertyMicroResponse)
        assert resp.id == "TX-TRAVIS-ABC123"
        assert resp.price == 425000
        assert resp.beds == 3
        assert resp.baths == 2.5
        assert resp.sqft == 2000
        assert resp.addr == "123 Main St, Austin, TX 78701"

    def test_no_address(self) -> None:
        db = MagicMock()
        service = PropertyService(db)
        prop = _mock_property(with_address=False)
        resp = service.to_response(prop, "standard")

        assert isinstance(resp, PropertyResponse)
        assert resp.address.city is None
        assert resp.location.lat is None

    def test_no_building(self) -> None:
        db = MagicMock()
        service = PropertyService(db)
        prop = _mock_property(with_building=False)
        resp = service.to_response(prop, "standard")

        assert isinstance(resp, PropertyResponse)
        assert resp.building is None

    def test_no_valuation(self) -> None:
        db = MagicMock()
        service = PropertyService(db)
        prop = _mock_property(with_valuation=False)
        resp = service.to_response(prop, "standard")

        assert isinstance(resp, PropertyResponse)
        assert resp.valuation is None

    def test_micro_no_building(self) -> None:
        db = MagicMock()
        service = PropertyService(db)
        prop = _mock_property(with_building=False)
        resp = service.to_response(prop, "micro")

        assert isinstance(resp, PropertyMicroResponse)
        assert resp.beds is None
        assert resp.sqft is None

    def test_quality_confidence_thresholds(self) -> None:
        db = MagicMock()
        service = PropertyService(db)

        # High confidence
        prop = _mock_property()
        prop.quality_score = 0.90
        resp = service.to_response(prop, "standard")
        assert isinstance(resp, PropertyResponse)
        assert resp.data_quality.confidence == "high"

        # Medium confidence
        prop.quality_score = 0.75
        resp = service.to_response(prop, "standard")
        assert isinstance(resp, PropertyResponse)
        assert resp.data_quality.confidence == "medium"

        # Low confidence
        prop.quality_score = 0.5
        resp = service.to_response(prop, "standard")
        assert isinstance(resp, PropertyResponse)
        assert resp.data_quality.confidence == "low"

    def test_provenance(self) -> None:
        db = MagicMock()
        service = PropertyService(db)
        prop = _mock_property()
        resp = service.to_response(prop, "standard")

        assert isinstance(resp, PropertyResponse)
        assert resp.provenance is not None
        assert resp.provenance.source_system == "travis_cad"
        assert resp.provenance.transformation_version == "1.0"

    def test_metadata(self) -> None:
        db = MagicMock()
        service = PropertyService(db)
        prop = _mock_property()
        resp = service.to_response(prop, "standard")

        assert isinstance(resp, PropertyResponse)
        assert resp.metadata["data_sources"] == ["travis_cad"]
        assert resp.metadata["last_updated"] is not None
