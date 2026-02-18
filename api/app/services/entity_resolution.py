"""Cross-source property deduplication pipeline."""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from jellyfish import jaro_winkler_similarity

from app.services.address import normalize


@dataclass
class MatchCandidate:
    """A potential duplicate match with confidence score."""

    property_id: str
    confidence: float
    match_type: str  # exact, fuzzy, geocode
    matched_fields: list[str] = field(default_factory=list)


@dataclass
class EntityResolutionResult:
    """Result of entity resolution for a property."""

    canonical_id: str | None
    confidence: float
    matches: list[MatchCandidate]
    action: str  # auto_merge, review, keep_separate


# Confidence thresholds
CONFIDENCE_AUTO_MERGE = 0.90
CONFIDENCE_REVIEW = 0.70
CONFIDENCE_SEPARATE = 0.50


def haversine_distance(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
) -> float:
    """Calculate distance between two points in meters.

    Args:
        lat1: Latitude of point 1.
        lon1: Longitude of point 1.
        lat2: Latitude of point 2.
        lon2: Longitude of point 2.

    Returns:
        Distance in meters.
    """
    r = 6371000.0  # Earth radius in meters

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return r * c


def score_address_similarity(
    addr1: str,
    addr2: str,
) -> float:
    """Score similarity between two address strings.

    Uses Jaro-Winkler similarity on normalized addresses.

    Args:
        addr1: First address string.
        addr2: Second address string.

    Returns:
        Similarity score between 0 and 1.
    """
    norm1 = normalize(addr1)
    norm2 = normalize(addr2)

    if not norm1.formatted_address or not norm2.formatted_address:
        return 0.0

    return float(
        jaro_winkler_similarity(
            norm1.formatted_address.lower(),
            norm2.formatted_address.lower(),
        )
    )


def score_match(
    input_address: str | None,
    input_lat: float | None,
    input_lng: float | None,
    input_parcel_id: str | None,
    candidate_id: str,
    candidate_address: str | None,
    candidate_lat: float | None,
    candidate_lng: float | None,
    candidate_apn: str | None,
    match_type: str,
) -> MatchCandidate:
    """Score similarity between input data and a candidate property.

    Args:
        input_address: Input address string.
        input_lat: Input latitude.
        input_lng: Input longitude.
        input_parcel_id: Input parcel/APN number.
        candidate_id: Candidate property ID.
        candidate_address: Candidate formatted address.
        candidate_lat: Candidate latitude.
        candidate_lng: Candidate longitude.
        candidate_apn: Candidate APN.
        match_type: How the candidate was found.

    Returns:
        MatchCandidate with computed confidence.
    """
    matched_fields: list[str] = []
    scores: list[float] = []

    # Parcel ID match (highest weight)
    if input_parcel_id and candidate_apn and input_parcel_id == candidate_apn:
            scores.append(1.0)
            matched_fields.append("parcel_id")

    # Address similarity
    if input_address and candidate_address:
        sim = score_address_similarity(input_address, candidate_address)
        if sim > 0.85:
            scores.append(sim)
            matched_fields.append("address")

    # Location proximity
    if (
        input_lat is not None
        and input_lng is not None
        and candidate_lat is not None
        and candidate_lng is not None
    ):
        distance = haversine_distance(
            input_lat, input_lng, candidate_lat, candidate_lng
        )
        if distance < 10:
            scores.append(0.95)
            matched_fields.append("location")
        elif distance < 50:
            scores.append(0.80)
            matched_fields.append("location")

    confidence = sum(scores) / len(scores) if scores else 0.0

    return MatchCandidate(
        property_id=candidate_id,
        confidence=confidence,
        match_type=match_type,
        matched_fields=matched_fields,
    )


def classify_matches(
    candidates: list[MatchCandidate],
) -> EntityResolutionResult:
    """Classify match candidates and determine resolution action.

    Args:
        candidates: List of scored match candidates.

    Returns:
        EntityResolutionResult with action determination.
    """
    if not candidates:
        return EntityResolutionResult(
            canonical_id=None,
            confidence=0.0,
            matches=[],
            action="keep_separate",
        )

    # Sort by confidence descending
    sorted_candidates = sorted(
        candidates, key=lambda x: x.confidence, reverse=True
    )

    best = sorted_candidates[0]

    if best.confidence >= CONFIDENCE_AUTO_MERGE:
        action = "auto_merge"
    elif best.confidence >= CONFIDENCE_REVIEW:
        action = "review"
    else:
        action = "keep_separate"

    return EntityResolutionResult(
        canonical_id=best.property_id if action == "auto_merge" else None,
        confidence=best.confidence,
        matches=sorted_candidates[:5],
        action=action,
    )


def resolve_from_candidates(
    address: str | None,
    lat: float | None,
    lng: float | None,
    parcel_id: str | None,
    candidates: list[dict[str, object]],
) -> EntityResolutionResult:
    """Resolve entity from a list of candidate properties.

    This is a pure function that takes pre-fetched candidates
    and scores them. The DB/search layer is responsible for
    finding candidates.

    Args:
        address: Input address.
        lat: Input latitude.
        lng: Input longitude.
        parcel_id: Input parcel ID.
        candidates: List of dicts with keys:
            id, address, latitude, longitude, apn, match_type.

    Returns:
        EntityResolutionResult.
    """
    scored: list[MatchCandidate] = []

    for cand in candidates:
        match = score_match(
            input_address=address,
            input_lat=lat,
            input_lng=lng,
            input_parcel_id=parcel_id,
            candidate_id=str(cand.get("id", "")),
            candidate_address=str(cand.get("address", ""))
            if cand.get("address")
            else None,
            candidate_lat=float(str(cand["latitude"]))
            if isinstance(cand.get("latitude"), (int, float))
            else None,
            candidate_lng=float(str(cand["longitude"]))
            if isinstance(cand.get("longitude"), (int, float))
            else None,
            candidate_apn=str(cand.get("apn", ""))
            if cand.get("apn")
            else None,
            match_type=str(cand.get("match_type", "unknown")),
        )
        if match.confidence > 0.3:
            scored.append(match)

    return classify_matches(scored)
