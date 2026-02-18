"""Address normalization to USPS standard format."""

from __future__ import annotations

from dataclasses import dataclass

import usaddress

STREET_SUFFIXES: dict[str, str] = {
    "avenue": "Ave",
    "ave": "Ave",
    "boulevard": "Blvd",
    "blvd": "Blvd",
    "circle": "Cir",
    "cir": "Cir",
    "court": "Ct",
    "ct": "Ct",
    "drive": "Dr",
    "dr": "Dr",
    "highway": "Hwy",
    "hwy": "Hwy",
    "lane": "Ln",
    "ln": "Ln",
    "parkway": "Pkwy",
    "pkwy": "Pkwy",
    "place": "Pl",
    "pl": "Pl",
    "road": "Rd",
    "rd": "Rd",
    "street": "St",
    "st": "St",
    "terrace": "Ter",
    "ter": "Ter",
    "trail": "Trl",
    "trl": "Trl",
    "way": "Way",
}

DIRECTIONALS: dict[str, str] = {
    "north": "N",
    "n": "N",
    "south": "S",
    "s": "S",
    "east": "E",
    "e": "E",
    "west": "W",
    "w": "W",
    "northeast": "NE",
    "ne": "NE",
    "northwest": "NW",
    "nw": "NW",
    "southeast": "SE",
    "se": "SE",
    "southwest": "SW",
    "sw": "SW",
}

UNIT_TYPES: dict[str, str] = {
    "apartment": "Apt",
    "apt": "Apt",
    "suite": "Ste",
    "ste": "Ste",
    "unit": "Unit",
    "floor": "Fl",
    "fl": "Fl",
    "#": "Apt",
}


@dataclass
class NormalizedAddress:
    """A parsed and USPS-standardized address."""

    street_number: str | None
    street_name: str | None
    street_suffix: str | None
    street_direction: str | None
    unit_type: str | None
    unit_number: str | None
    city: str | None
    state: str | None
    zip_code: str | None
    zip4: str | None
    street_address: str | None
    formatted_address: str | None
    confidence: float


def _empty_address() -> NormalizedAddress:
    """Return an empty NormalizedAddress with zero confidence."""
    return NormalizedAddress(
        street_number=None,
        street_name=None,
        street_suffix=None,
        street_direction=None,
        unit_type=None,
        unit_number=None,
        city=None,
        state=None,
        zip_code=None,
        zip4=None,
        street_address=None,
        formatted_address=None,
        confidence=0.0,
    )


def normalize(raw_address: str) -> NormalizedAddress:
    """Normalize a raw address string to USPS standard format.

    Uses usaddress library for parsing, then applies USPS
    suffix/directional standardization.

    Args:
        raw_address: Free-form address string.

    Returns:
        NormalizedAddress with parsed and standardized components.
    """
    if not raw_address or not raw_address.strip():
        return _empty_address()

    try:
        parsed: dict[str, str]
        parsed, _ = usaddress.tag(raw_address)
    except usaddress.RepeatedLabelError:
        return _empty_address()

    # Extract and standardize components
    street_number = parsed.get("AddressNumber", "").strip() or None

    # Street name (combine parts)
    street_name_parts: list[str] = []
    for key in [
        "StreetNamePreDirectional",
        "StreetNamePreModifier",
        "StreetNamePreType",
        "StreetName",
    ]:
        val = parsed.get(key, "").strip()
        if val:
            street_name_parts.append(val)
    street_name = " ".join(street_name_parts) or None

    # Street suffix
    raw_suffix = parsed.get("StreetNamePostType", "").lower().strip()
    street_suffix = (
        STREET_SUFFIXES.get(raw_suffix, raw_suffix.title())
        if raw_suffix
        else None
    )

    # Direction
    raw_direction = (
        parsed.get("StreetNamePostDirectional", "").lower().strip()
    )
    street_direction: str | None = None
    if raw_direction:
        street_direction = DIRECTIONALS.get(
            raw_direction, raw_direction.upper()
        )

    # Unit
    raw_unit_type = parsed.get("OccupancyType", "").lower().strip()
    unit_type: str | None = None
    if raw_unit_type:
        unit_type = UNIT_TYPES.get(raw_unit_type, raw_unit_type.title())
    unit_number = parsed.get("OccupancyIdentifier", "").strip() or None

    # Location
    city = parsed.get("PlaceName", "").strip().title() or None
    raw_state = parsed.get("StateName", "").strip().upper()
    state = raw_state if len(raw_state) == 2 and raw_state.isalpha() else None

    raw_zip = parsed.get("ZipCode", "").strip()
    zip_code = raw_zip[:5] if len(raw_zip) >= 5 and raw_zip[:5].isdigit() else None
    zip4 = raw_zip[6:10] if len(raw_zip) > 5 else None

    # Build formatted addresses
    street_parts = [
        p for p in [street_number, street_name, street_suffix] if p
    ]
    if street_direction:
        street_parts.append(street_direction)
    street_address = " ".join(street_parts) or None

    if unit_type and unit_number and street_address:
        street_address += f" {unit_type} {unit_number}"

    formatted_parts: list[str] = []
    if street_address:
        formatted_parts.append(street_address)
    if city:
        formatted_parts.append(city)
    if state and formatted_parts:
        formatted_parts[-1] += ","
        formatted_parts.append(state)
    if zip_code:
        formatted_parts.append(zip_code)

    formatted_address = " ".join(formatted_parts) or None

    # Calculate confidence
    confidence = 0.0
    if street_number:
        confidence += 0.2
    if street_name:
        confidence += 0.3
    if city:
        confidence += 0.2
    if state:
        confidence += 0.2
    if zip_code:
        confidence += 0.1

    return NormalizedAddress(
        street_number=street_number,
        street_name=street_name,
        street_suffix=street_suffix,
        street_direction=street_direction,
        unit_type=unit_type,
        unit_number=unit_number,
        city=city,
        state=state,
        zip_code=zip_code,
        zip4=zip4,
        street_address=street_address,
        formatted_address=formatted_address,
        confidence=confidence,
    )
