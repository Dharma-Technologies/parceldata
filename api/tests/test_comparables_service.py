"""Tests for ComparablesService similarity and valuation logic."""

from __future__ import annotations

from app.services.comparables_service import ComparablesService


class TestSimilarityScore:
    def test_identical_properties(self) -> None:
        score = ComparablesService._calculate_similarity(
            2000, 3, 2005, 2000, 3, 2005,
        )
        assert score == 1.0

    def test_different_sqft(self) -> None:
        score = ComparablesService._calculate_similarity(
            2000, 3, 2005, 2400, 3, 2005,
        )
        # 20% diff = sqft_score 0.0, beds 1.0, year 1.0
        assert score == 0.6

    def test_different_beds(self) -> None:
        score = ComparablesService._calculate_similarity(
            2000, 3, 2005, 2000, 4, 2005,
        )
        # sqft 1.0, beds 0.75, year 1.0
        assert abs(score - 0.925) < 0.01

    def test_different_year(self) -> None:
        score = ComparablesService._calculate_similarity(
            2000, 3, 2005, 2000, 3, 2010,
        )
        # sqft 1.0, beds 1.0, year 0.5
        assert abs(score - 0.85) < 0.01

    def test_completely_different(self) -> None:
        score = ComparablesService._calculate_similarity(
            1000, 2, 1980, 3000, 5, 2020,
        )
        assert score < 0.3

    def test_zero_sqft_no_crash(self) -> None:
        score = ComparablesService._calculate_similarity(
            0, 3, 2005, 2000, 3, 2005,
        )
        assert score >= 0.0
