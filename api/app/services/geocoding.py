"""Geocoding with multiple provider fallback."""

from __future__ import annotations

from dataclasses import dataclass

import httpx
import structlog

logger = structlog.get_logger()


@dataclass
class GeocodingResult:
    """Result from a geocoding operation."""

    latitude: float
    longitude: float
    accuracy: str  # rooftop, parcel, street, city
    source: str
    confidence: float


class GeocodingService:
    """Geocoding with multiple provider fallback.

    Tries providers in order: Census Bureau (free, US), Nominatim (free, global).
    """

    def __init__(self) -> None:
        self.client = httpx.AsyncClient(timeout=10.0)

    async def geocode(
        self,
        address: str,
        city: str | None = None,
        state: str | None = None,
        zip_code: str | None = None,
    ) -> GeocodingResult | None:
        """Geocode an address using multiple providers with fallback.

        Args:
            address: Street address.
            city: City name.
            state: State code.
            zip_code: ZIP code.

        Returns:
            GeocodingResult or None if all providers fail.
        """
        full_address = address
        if city:
            full_address += f", {city}"
        if state:
            full_address += f", {state}"
        if zip_code:
            full_address += f" {zip_code}"

        # Try Census Geocoder first (free, high quality for US)
        result = await self._census_geocode(full_address)
        if result:
            return result

        # Fallback to Nominatim (free, global)
        result = await self._nominatim_geocode(full_address)
        if result:
            return result

        return None

    async def _census_geocode(
        self, address: str
    ) -> GeocodingResult | None:
        """Use Census Bureau geocoder (free, US only)."""
        try:
            url = "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"
            params = {
                "address": address,
                "benchmark": "Public_AR_Current",
                "format": "json",
            }

            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data: dict[str, object] = response.json()

            result = data.get("result")
            if not isinstance(result, dict):
                return None

            matches = result.get("addressMatches")
            if not isinstance(matches, list) or not matches:
                return None

            match = matches[0]
            if not isinstance(match, dict):
                return None

            coords = match.get("coordinates")
            if not isinstance(coords, dict):
                return None

            lat_val = coords.get("y")
            lng_val = coords.get("x")
            if not isinstance(lat_val, (int, float)) or not isinstance(
                lng_val, (int, float)
            ):
                return None

            return GeocodingResult(
                latitude=float(lat_val),
                longitude=float(lng_val),
                accuracy="rooftop",
                source="census",
                confidence=0.95,
            )
        except Exception:
            logger.debug("Census geocoding failed", address=address)
            return None

    async def _nominatim_geocode(
        self, address: str
    ) -> GeocodingResult | None:
        """Use OpenStreetMap Nominatim (free, global)."""
        try:
            url = "https://nominatim.openstreetmap.org/search"
            params: dict[str, str | int] = {
                "q": address,
                "format": "json",
                "limit": 1,
            }
            headers = {"User-Agent": "ParcelData/0.1"}

            response = await self.client.get(
                url, params=params, headers=headers
            )
            response.raise_for_status()
            results: list[dict[str, object]] = response.json()

            if not results:
                return None

            result = results[0]
            lat_str = result.get("lat")
            lon_str = result.get("lon")
            if lat_str is None or lon_str is None:
                return None

            return GeocodingResult(
                latitude=float(str(lat_str)),
                longitude=float(str(lon_str)),
                accuracy="street",
                source="nominatim",
                confidence=0.8,
            )
        except Exception:
            logger.debug("Nominatim geocoding failed", address=address)
            return None

    async def reverse_geocode(
        self,
        lat: float,
        lng: float,
    ) -> dict[str, str | None] | None:
        """Reverse geocode coordinates to address."""
        try:
            url = "https://nominatim.openstreetmap.org/reverse"
            params: dict[str, str | float] = {
                "lat": lat,
                "lon": lng,
                "format": "json",
            }
            headers = {"User-Agent": "ParcelData/0.1"}

            response = await self.client.get(
                url, params=params, headers=headers
            )
            response.raise_for_status()
            data: dict[str, object] = response.json()
            addr = data.get("address")
            addr_dict = addr if isinstance(addr, dict) else {}

            return {
                "address": str(data.get("display_name", "")),
                "house_number": str(addr_dict.get("house_number", ""))
                or None,
                "road": str(addr_dict.get("road", "")) or None,
                "city": str(addr_dict.get("city", "")) or None,
                "state": str(addr_dict.get("state", "")) or None,
                "postcode": str(addr_dict.get("postcode", "")) or None,
            }
        except Exception:
            logger.debug(
                "Reverse geocoding failed", lat=lat, lng=lng
            )
            return None
