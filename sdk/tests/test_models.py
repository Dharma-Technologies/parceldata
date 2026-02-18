"""Tests for SDK Pydantic response models."""

from __future__ import annotations

from parceldata.models import (
    BatchResults,
    DataQuality,
    GeocodingResult,
    Property,
    PropertySummary,
    Provenance,
    SearchResults,
)


class TestDataQuality:
    def test_create_data_quality(self) -> None:
        dq = DataQuality(score=0.87, confidence="high")
        assert dq.score == 0.87
        assert dq.confidence == "high"
        assert dq.freshness_hours == 0
        assert dq.sources == []

    def test_data_quality_with_components(self) -> None:
        dq = DataQuality(
            score=0.87,
            components={"completeness": 0.92, "accuracy": 0.95},
            freshness_hours=12,
            sources=["travis_cad"],
            confidence="high",
        )
        assert dq.components["completeness"] == 0.92
        assert dq.sources == ["travis_cad"]


class TestProvenance:
    def test_create_provenance(self) -> None:
        p = Provenance(source_system="travis_cad", source_type="county")
        assert p.source_system == "travis_cad"
        assert p.attribution_required is False


class TestProperty:
    def test_create_from_dict(
        self, sample_property_data: dict[str, object],
    ) -> None:
        prop = Property.model_validate(sample_property_data)
        assert prop.property_id == "TX-TRAVIS-12345"
        assert prop.address.city == "Austin"
        assert prop.location.lat == 30.2672
        assert prop.building is not None
        assert prop.building.sqft == 2200
        assert prop.data_quality.score == 0.87

    def test_property_optional_fields(self) -> None:
        prop = Property(
            property_id="TX-001",
            address={"street": "1 Main St"},  # type: ignore[arg-type]
            location={},  # type: ignore[arg-type]
            parcel={},  # type: ignore[arg-type]
            data_quality={"score": 0.5, "confidence": "low"},  # type: ignore[arg-type]
        )
        assert prop.building is None
        assert prop.valuation is None
        assert prop.zoning is None

    def test_property_serialization(
        self, sample_property_data: dict[str, object],
    ) -> None:
        prop = Property.model_validate(sample_property_data)
        data = prop.model_dump()
        assert data["property_id"] == "TX-TRAVIS-12345"
        assert "data_quality" in data


class TestPropertySummary:
    def test_create_summary(self) -> None:
        s = PropertySummary(
            id="TX-001",
            price=450000,
            beds=3,
            baths=2.5,
            sqft=2200,
            addr="100 Congress Ave, Austin, TX",
            data_quality=DataQuality(score=0.87, confidence="high"),
        )
        assert s.id == "TX-001"
        assert s.price == 450000


class TestSearchResults:
    def test_create_search_results(
        self, sample_search_data: dict[str, object],
    ) -> None:
        results = SearchResults.model_validate(sample_search_data)
        assert results.total == 1
        assert len(results.results) == 1
        assert results.has_more is False
        assert results.data_quality.score == 0.87


class TestBatchResults:
    def test_create_batch_results(
        self, sample_batch_data: dict[str, object],
    ) -> None:
        results = BatchResults.model_validate(sample_batch_data)
        assert results.found == 1
        assert results.not_found == 1
        assert results.results[0] is not None
        assert results.results[1] is None


class TestGeocodingResult:
    def test_create_geocoding_result(self) -> None:
        result = GeocodingResult(
            address="100 Congress Ave, Austin, TX 78701",
            lat=30.2672,
            lng=-97.7431,
            property_id="TX-TRAVIS-12345",
            confidence=0.95,
            data_quality=DataQuality(score=0.87, confidence="high"),
        )
        assert result.lat == 30.2672
        assert result.property_id == "TX-TRAVIS-12345"
