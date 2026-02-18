"""Tests for entity resolution pipeline."""

from __future__ import annotations

import pytest

from app.services.entity_resolution import (
    CONFIDENCE_AUTO_MERGE,
    CONFIDENCE_REVIEW,
    MatchCandidate,
    classify_matches,
    haversine_distance,
    resolve_from_candidates,
    score_address_similarity,
    score_match,
)


class TestHaversineDistance:
    """Tests for haversine distance calculation."""

    def test_same_point(self) -> None:
        """Same point gives zero distance."""
        d = haversine_distance(30.0, -97.0, 30.0, -97.0)
        assert d == 0.0

    def test_known_distance(self) -> None:
        """Check a known distance (Austin to Dallas ~290km)."""
        d = haversine_distance(30.2672, -97.7431, 32.7767, -96.7970)
        assert 280_000 < d < 300_000  # ~290 km

    def test_short_distance(self) -> None:
        """Points 100m apart."""
        # ~0.001 degrees ≈ ~111m at equator
        d = haversine_distance(0.0, 0.0, 0.001, 0.0)
        assert 100 < d < 120

    def test_returns_float(self) -> None:
        d = haversine_distance(30.0, -97.0, 31.0, -97.0)
        assert isinstance(d, float)


class TestScoreAddressSimilarity:
    """Tests for address string similarity."""

    def test_identical_addresses(self) -> None:
        sim = score_address_similarity(
            "123 Main St, Austin, TX 78701",
            "123 Main St, Austin, TX 78701",
        )
        assert sim == pytest.approx(1.0)

    def test_normalized_match(self) -> None:
        """Different formats of same address are similar."""
        sim = score_address_similarity(
            "123 Main Street, Austin, TX 78701",
            "123 Main St, Austin, TX 78701",
        )
        assert sim > 0.9

    def test_different_addresses(self) -> None:
        sim = score_address_similarity(
            "123 Main St, Austin, TX",
            "999 Oak Blvd, Dallas, TX",
        )
        assert sim < 0.85

    def test_empty_address(self) -> None:
        sim = score_address_similarity("", "123 Main St")
        assert sim == 0.0


class TestScoreMatch:
    """Tests for the score_match function."""

    def test_exact_parcel_id_match(self) -> None:
        m = score_match(
            input_address=None,
            input_lat=None,
            input_lng=None,
            input_parcel_id="TX-001-ABC",
            candidate_id="prop-1",
            candidate_address=None,
            candidate_lat=None,
            candidate_lng=None,
            candidate_apn="TX-001-ABC",
            match_type="parcel_id",
        )
        assert m.confidence == 1.0
        assert "parcel_id" in m.matched_fields

    def test_close_location(self) -> None:
        m = score_match(
            input_address=None,
            input_lat=30.2672,
            input_lng=-97.7431,
            input_parcel_id=None,
            candidate_id="prop-2",
            candidate_address=None,
            candidate_lat=30.2672,
            candidate_lng=-97.7431,
            candidate_apn=None,
            match_type="geocode",
        )
        assert m.confidence >= 0.9
        assert "location" in m.matched_fields

    def test_medium_distance_location(self) -> None:
        """Points ~30m apart get lower score."""
        m = score_match(
            input_address=None,
            input_lat=30.2672,
            input_lng=-97.7431,
            input_parcel_id=None,
            candidate_id="prop-3",
            candidate_address=None,
            candidate_lat=30.26745,
            candidate_lng=-97.7431,
            candidate_apn=None,
            match_type="geocode",
        )
        assert 0.7 < m.confidence < 0.9

    def test_no_matching_fields(self) -> None:
        m = score_match(
            input_address=None,
            input_lat=None,
            input_lng=None,
            input_parcel_id=None,
            candidate_id="prop-4",
            candidate_address=None,
            candidate_lat=None,
            candidate_lng=None,
            candidate_apn=None,
            match_type="unknown",
        )
        assert m.confidence == 0.0
        assert m.matched_fields == []

    def test_combined_score(self) -> None:
        """Multiple matching fields get averaged."""
        m = score_match(
            input_address="123 Main St, Austin, TX",
            input_lat=30.2672,
            input_lng=-97.7431,
            input_parcel_id="APN-1",
            candidate_id="prop-5",
            candidate_address="123 Main St, Austin, TX",
            candidate_lat=30.2672,
            candidate_lng=-97.7431,
            candidate_apn="APN-1",
            match_type="exact",
        )
        assert m.confidence > 0.9
        assert len(m.matched_fields) >= 2


class TestClassifyMatches:
    """Tests for match classification."""

    def test_auto_merge(self) -> None:
        candidates = [
            MatchCandidate(
                property_id="p1",
                confidence=0.95,
                match_type="exact",
                matched_fields=["parcel_id"],
            )
        ]
        result = classify_matches(candidates)
        assert result.action == "auto_merge"
        assert result.canonical_id == "p1"

    def test_review_zone(self) -> None:
        candidates = [
            MatchCandidate(
                property_id="p2",
                confidence=0.75,
                match_type="fuzzy",
                matched_fields=["address"],
            )
        ]
        result = classify_matches(candidates)
        assert result.action == "review"
        assert result.canonical_id is None

    def test_keep_separate(self) -> None:
        candidates = [
            MatchCandidate(
                property_id="p3",
                confidence=0.4,
                match_type="geocode",
                matched_fields=["location"],
            )
        ]
        result = classify_matches(candidates)
        assert result.action == "keep_separate"
        assert result.canonical_id is None

    def test_empty_candidates(self) -> None:
        result = classify_matches([])
        assert result.action == "keep_separate"
        assert result.confidence == 0.0
        assert result.matches == []

    def test_sorts_by_confidence(self) -> None:
        candidates = [
            MatchCandidate("p1", 0.5, "fuzzy", []),
            MatchCandidate("p2", 0.95, "exact", ["parcel_id"]),
            MatchCandidate("p3", 0.7, "geocode", []),
        ]
        result = classify_matches(candidates)
        assert result.matches[0].property_id == "p2"
        assert result.matches[0].confidence == 0.95

    def test_limits_to_5_matches(self) -> None:
        candidates = [
            MatchCandidate(f"p{i}", 0.9 - i * 0.01, "fuzzy", [])
            for i in range(10)
        ]
        result = classify_matches(candidates)
        assert len(result.matches) == 5


class TestResolveFromCandidates:
    """Tests for resolve_from_candidates."""

    def test_exact_match(self) -> None:
        candidates: list[dict[str, object]] = [
            {
                "id": "prop-1",
                "address": "123 Main St, Austin, TX",
                "latitude": 30.2672,
                "longitude": -97.7431,
                "apn": "TX-001",
                "match_type": "parcel_id",
            }
        ]
        result = resolve_from_candidates(
            address="123 Main St, Austin, TX",
            lat=30.2672,
            lng=-97.7431,
            parcel_id="TX-001",
            candidates=candidates,
        )
        assert result.action == "auto_merge"
        assert result.canonical_id == "prop-1"

    def test_no_candidates(self) -> None:
        result = resolve_from_candidates(
            address="123 Main St",
            lat=30.0,
            lng=-97.0,
            parcel_id=None,
            candidates=[],
        )
        assert result.action == "keep_separate"
        assert result.canonical_id is None

    def test_low_confidence_filtered(self) -> None:
        """Candidates below 0.3 confidence are filtered out."""
        candidates: list[dict[str, object]] = [
            {
                "id": "prop-far",
                "latitude": 40.0,
                "longitude": -80.0,
                "match_type": "geocode",
            }
        ]
        result = resolve_from_candidates(
            address=None,
            lat=30.0,
            lng=-97.0,
            parcel_id=None,
            candidates=candidates,
        )
        assert result.action == "keep_separate"


class TestThresholds:
    """Verify threshold constants."""

    def test_auto_merge_threshold(self) -> None:
        assert CONFIDENCE_AUTO_MERGE == 0.90

    def test_review_threshold(self) -> None:
        assert CONFIDENCE_REVIEW == 0.70
