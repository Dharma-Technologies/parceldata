"""Tests for data quality scoring service."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from app.services.quality import (
    OPTIONAL_FIELDS,
    REQUIRED_FIELDS,
    DataQualityScore,
    calculate_quality_score,
)


def _complete_property() -> dict[str, object]:
    """Return a property dict with all required + optional fields."""
    return {
        "address": "123 Main St",
        "city": "Austin",
        "state": "TX",
        "zip_code": "78701",
        "latitude": 30.2672,
        "longitude": -97.7431,
        "lot_sqft": 8000,
        "property_type": "single_family",
        "bedrooms": 3,
        "bathrooms": 2,
        "sqft": 1800,
        "year_built": 2005,
        "assessed_value": 350000,
        "estimated_value": 400000,
        "zoning": "SF-3",
        "owner_name": "John Doe",
    }


class TestRequiredAndOptionalFields:
    """Test field list definitions."""

    def test_required_fields_count(self) -> None:
        assert len(REQUIRED_FIELDS) == 8

    def test_optional_fields_count(self) -> None:
        assert len(OPTIONAL_FIELDS) == 8

    def test_required_includes_address(self) -> None:
        assert "address" in REQUIRED_FIELDS

    def test_optional_includes_bedrooms(self) -> None:
        assert "bedrooms" in OPTIONAL_FIELDS


class TestCalculateQualityScore:
    """Tests for the main scoring function."""

    def test_complete_property_high_confidence(self) -> None:
        """Complete property gets high confidence."""
        data = _complete_property()
        result = calculate_quality_score(
            data, source_timestamp=datetime.utcnow()
        )
        assert result.confidence == "high"
        assert result.score > 0.85

    def test_empty_property_low_score(self) -> None:
        """Empty property gets low confidence."""
        result = calculate_quality_score({})
        assert result.confidence == "low"
        assert result.completeness == 0.0

    def test_returns_dataclass(self) -> None:
        result = calculate_quality_score({})
        assert isinstance(result, DataQualityScore)

    def test_score_components_sum(self) -> None:
        """Score is weighted sum of components."""
        data = _complete_property()
        result = calculate_quality_score(data)
        expected = (
            result.completeness * 0.25
            + result.accuracy * 0.25
            + result.consistency * 0.20
            + result.timeliness * 0.15
            + result.validity * 0.10
            + result.uniqueness * 0.05
        )
        assert result.score == pytest.approx(round(expected, 3), abs=0.01)

    def test_freshness_hours_recent(self) -> None:
        """Recent data has low freshness_hours."""
        result = calculate_quality_score(
            _complete_property(),
            source_timestamp=datetime.utcnow() - timedelta(hours=1),
        )
        assert result.freshness_hours <= 2
        assert result.timeliness == 1.0

    def test_freshness_hours_old(self) -> None:
        """Old data has high freshness_hours."""
        result = calculate_quality_score(
            _complete_property(),
            source_timestamp=datetime.utcnow() - timedelta(days=100),
        )
        assert result.freshness_hours > 2000
        assert result.timeliness == 0.5

    def test_freshness_one_week(self) -> None:
        result = calculate_quality_score(
            _complete_property(),
            source_timestamp=datetime.utcnow() - timedelta(days=3),
        )
        assert result.timeliness == 0.9

    def test_freshness_one_month(self) -> None:
        result = calculate_quality_score(
            _complete_property(),
            source_timestamp=datetime.utcnow() - timedelta(days=15),
        )
        assert result.timeliness == 0.8

    def test_freshness_three_months(self) -> None:
        result = calculate_quality_score(
            _complete_property(),
            source_timestamp=datetime.utcnow() - timedelta(days=60),
        )
        assert result.timeliness == 0.7

    def test_no_timestamp_default(self) -> None:
        """No source timestamp gives default timeliness."""
        result = calculate_quality_score(_complete_property())
        assert result.timeliness == 0.7
        assert result.freshness_hours == 0

    def test_duplicate_check_affects_uniqueness(self) -> None:
        result = calculate_quality_score(
            _complete_property(), duplicate_check=True
        )
        assert result.uniqueness == 0.95

    def test_no_duplicate_check_full_uniqueness(self) -> None:
        result = calculate_quality_score(
            _complete_property(), duplicate_check=False
        )
        assert result.uniqueness == 1.0


class TestCompleteness:
    """Tests for completeness scoring."""

    def test_all_required_present(self) -> None:
        data = _complete_property()
        result = calculate_quality_score(data)
        assert result.completeness == pytest.approx(1.0)

    def test_partial_required(self) -> None:
        data: dict[str, object] = {
            "address": "123 Main",
            "city": "Austin",
            "state": "TX",
        }
        result = calculate_quality_score(data)
        assert 0.0 < result.completeness < 1.0


class TestAccuracy:
    """Tests for accuracy scoring."""

    def test_valid_zip(self) -> None:
        result = calculate_quality_score({"zip_code": "78701"})
        assert result.accuracy >= 0.8

    def test_invalid_zip(self) -> None:
        result = calculate_quality_score({"zip_code": "ABCDE"})
        assert result.accuracy < 1.0

    def test_valid_state(self) -> None:
        result = calculate_quality_score({"state": "TX"})
        assert result.accuracy >= 0.8

    def test_valid_year_built(self) -> None:
        result = calculate_quality_score({"year_built": 2000})
        assert result.accuracy >= 0.8

    def test_invalid_year_built(self) -> None:
        result = calculate_quality_score({"year_built": 1500})
        assert result.accuracy < 1.0

    def test_valid_coordinates(self) -> None:
        result = calculate_quality_score(
            {"latitude": 30.0, "longitude": -97.0}
        )
        assert result.accuracy >= 0.8

    def test_invalid_coordinates(self) -> None:
        result = calculate_quality_score(
            {"latitude": 200.0, "longitude": -97.0}
        )
        assert result.accuracy < 1.0


class TestConsistency:
    """Tests for consistency scoring."""

    def test_lot_bigger_than_building(self) -> None:
        result = calculate_quality_score(
            {"lot_sqft": 8000, "sqft": 2000}
        )
        assert result.consistency == 1.0

    def test_building_bigger_than_lot(self) -> None:
        """Building > lot is inconsistent."""
        result = calculate_quality_score(
            {"lot_sqft": 1000, "sqft": 5000}
        )
        assert result.consistency < 1.0

    def test_reasonable_price_per_sqft(self) -> None:
        result = calculate_quality_score(
            {"assessed_value": 400000, "sqft": 2000}
        )
        assert result.consistency == 1.0

    def test_unreasonable_price_per_sqft(self) -> None:
        result = calculate_quality_score(
            {"assessed_value": 10000000, "sqft": 500}
        )
        assert result.consistency < 1.0

    def test_no_consistency_fields(self) -> None:
        """Missing consistency fields default to 0.85."""
        result = calculate_quality_score({})
        assert result.consistency == 0.85


class TestConfidence:
    """Tests for confidence levels."""

    def test_high_confidence(self) -> None:
        result = calculate_quality_score(
            _complete_property(),
            source_timestamp=datetime.utcnow(),
        )
        assert result.confidence == "high"

    def test_medium_confidence(self) -> None:
        data: dict[str, object] = {
            "address": "123 Main",
            "city": "Austin",
            "state": "TX",
            "zip_code": "78701",
            "latitude": 30.0,
            "longitude": -97.0,
        }
        result = calculate_quality_score(data)
        assert result.confidence in ("medium", "high")

    def test_low_confidence(self) -> None:
        result = calculate_quality_score({})
        assert result.confidence == "low"
