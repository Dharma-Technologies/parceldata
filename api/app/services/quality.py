"""Data quality scoring for property records."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

REQUIRED_FIELDS = [
    "address",
    "city",
    "state",
    "zip_code",
    "latitude",
    "longitude",
    "lot_sqft",
    "property_type",
]

OPTIONAL_FIELDS = [
    "bedrooms",
    "bathrooms",
    "sqft",
    "year_built",
    "assessed_value",
    "estimated_value",
    "zoning",
    "owner_name",
]


@dataclass
class DataQualityScore:
    """Calculated data quality metrics for a property record."""

    score: float  # Overall 0-1
    completeness: float
    accuracy: float
    consistency: float
    timeliness: float
    validity: float
    uniqueness: float
    freshness_hours: int
    confidence: str  # low, medium, high


def calculate_quality_score(
    property_data: dict[str, object],
    source_timestamp: datetime | None = None,
    duplicate_check: bool = False,
) -> DataQualityScore:
    """Calculate data quality score for a property record.

    Formula:
        score = (completeness x 0.25) + (accuracy x 0.25) +
                (consistency x 0.20) + (timeliness x 0.15) +
                (validity x 0.10) + (uniqueness x 0.05)

    Args:
        property_data: Dict of property field names to values.
        source_timestamp: When the data was extracted.
        duplicate_check: Whether a duplicate check was performed.

    Returns:
        DataQualityScore with all component scores.
    """
    completeness = _score_completeness(property_data)
    accuracy = _score_accuracy(property_data)
    consistency = _score_consistency(property_data)
    timeliness, freshness_hours = _score_timeliness(source_timestamp)
    validity = _score_validity()
    uniqueness = 1.0 if not duplicate_check else 0.95

    score = (
        completeness * 0.25
        + accuracy * 0.25
        + consistency * 0.20
        + timeliness * 0.15
        + validity * 0.10
        + uniqueness * 0.05
    )

    if score >= 0.85:
        confidence = "high"
    elif score >= 0.70:
        confidence = "medium"
    else:
        confidence = "low"

    return DataQualityScore(
        score=round(score, 3),
        completeness=round(completeness, 3),
        accuracy=round(accuracy, 3),
        consistency=round(consistency, 3),
        timeliness=round(timeliness, 3),
        validity=round(validity, 3),
        uniqueness=round(uniqueness, 3),
        freshness_hours=freshness_hours,
        confidence=confidence,
    )


def _score_completeness(data: dict[str, object]) -> float:
    """Score based on presence of required and optional fields."""
    required_present = sum(
        1 for f in REQUIRED_FIELDS if data.get(f) is not None
    )
    optional_present = sum(
        1 for f in OPTIONAL_FIELDS if data.get(f) is not None
    )

    return (
        (required_present / len(REQUIRED_FIELDS)) * 0.7
        + (optional_present / len(OPTIONAL_FIELDS)) * 0.3
    )


def _score_accuracy(data: dict[str, object]) -> float:
    """Score based on field format validation."""
    checks: list[float] = []

    # ZIP code format
    zip_code = data.get("zip_code")
    if isinstance(zip_code, str) and zip_code:
        checks.append(
            1.0
            if len(zip_code) == 5 and zip_code.isdigit()
            else 0.5
        )

    # State is valid 2-letter code
    state = data.get("state")
    if isinstance(state, str) and state:
        checks.append(
            1.0 if len(state) == 2 and state.isalpha() else 0.5
        )

    # Year built is reasonable
    year_built = data.get("year_built")
    if isinstance(year_built, int):
        checks.append(1.0 if 1800 <= year_built <= 2030 else 0.5)

    # Coordinates are valid
    lat = data.get("latitude")
    lng = data.get("longitude")
    if isinstance(lat, (int, float)) and isinstance(
        lng, (int, float)
    ):
        valid = -90 <= lat <= 90 and -180 <= lng <= 180
        checks.append(1.0 if valid else 0.0)

    return sum(checks) / len(checks) if checks else 0.8


def _score_consistency(data: dict[str, object]) -> float:
    """Score based on cross-field validation."""
    checks: list[float] = []

    lot_sqft = data.get("lot_sqft")
    building_sqft = data.get("sqft")

    # Lot should be >= building sqft
    if (
        isinstance(lot_sqft, (int, float))
        and isinstance(building_sqft, (int, float))
        and lot_sqft > 0
        and building_sqft > 0
    ):
        checks.append(1.0 if lot_sqft >= building_sqft else 0.5)

    # Price per sqft should be reasonable
    assessed = data.get("assessed_value")
    if (
        isinstance(assessed, (int, float))
        and isinstance(building_sqft, (int, float))
        and assessed > 0
        and building_sqft > 0
    ):
        ppsf = assessed / building_sqft
        checks.append(1.0 if 50 <= ppsf <= 2000 else 0.7)

    return sum(checks) / len(checks) if checks else 0.85


def _score_timeliness(
    source_timestamp: datetime | None,
) -> tuple[float, int]:
    """Score based on data freshness.

    Returns:
        Tuple of (timeliness_score, freshness_hours).
    """
    if not source_timestamp:
        return 0.7, 0

    age = datetime.utcnow() - source_timestamp
    freshness_hours = int(age.total_seconds() / 3600)

    if freshness_hours < 24:
        score = 1.0
    elif freshness_hours < 168:  # 1 week
        score = 0.9
    elif freshness_hours < 720:  # 30 days
        score = 0.8
    elif freshness_hours < 2160:  # 90 days
        score = 0.7
    else:
        score = 0.5

    return score, freshness_hours


def _score_validity() -> float:
    """Schema compliance score. Assumed valid if we got this far."""
    return 0.95
