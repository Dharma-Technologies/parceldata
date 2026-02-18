"""Adapter for FEMA flood zone data (free)."""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass

import httpx

from app.services.ingestion.base import ProviderAdapter, RawPropertyRecord


@dataclass
class FloodZoneResult:
    """Flood zone determination for a location."""

    flood_zone: str | None
    zone_subtype: str | None
    in_sfha: bool
    base_flood_elevation: float | None


class FEMAAdapter(ProviderAdapter):
    """Adapter for FEMA National Flood Hazard Layer (free).

    Queries the NFHL MapServer to determine flood zone
    designations for geographic coordinates.
    """

    name = "fema"
    source_type = "flood_zones"
    base_url = "https://hazards.fema.gov/gis/nfhl/rest/services"

    def __init__(self, api_key: str | None = None) -> None:
        super().__init__(api_key)  # No API key required
        self.client = httpx.AsyncClient(timeout=30.0)

    async def get_flood_zone(
        self, lat: float, lng: float
    ) -> FloodZoneResult:
        """Get flood zone for a coordinate.

        Args:
            lat: Latitude.
            lng: Longitude.

        Returns:
            FloodZoneResult with zone determination.
        """
        url = f"{self.base_url}/public/NFHL/MapServer/28/query"

        params: dict[str, str] = {
            "geometry": f"{lng},{lat}",
            "geometryType": "esriGeometryPoint",
            "spatialRel": "esriSpatialRelIntersects",
            "outFields": "FLD_ZONE,ZONE_SUBTY,SFHA_TF,STATIC_BFE",
            "returnGeometry": "false",
            "f": "json",
        }

        response = await self.client.get(url, params=params)
        response.raise_for_status()
        data: dict[str, object] = response.json()

        features = data.get("features")
        if isinstance(features, list) and features:
            feature = features[0]
            if isinstance(feature, dict):
                attrs = feature.get("attributes")
                if isinstance(attrs, dict):
                    bfe = attrs.get("STATIC_BFE")
                    return FloodZoneResult(
                        flood_zone=str(attrs.get("FLD_ZONE", ""))
                        or None,
                        zone_subtype=str(attrs.get("ZONE_SUBTY", ""))
                        or None,
                        in_sfha=attrs.get("SFHA_TF") == "T",
                        base_flood_elevation=(
                            float(bfe)
                            if isinstance(bfe, (int, float))
                            else None
                        ),
                    )

        return FloodZoneResult(
            flood_zone="X",
            zone_subtype=None,
            in_sfha=False,
            base_flood_elevation=None,
        )

    async def fetch_property(
        self, property_id: str
    ) -> RawPropertyRecord | None:
        """Not applicable for FEMA — use get_flood_zone."""
        return None

    async def fetch_by_address(
        self,
        street: str,
        city: str,
        state: str,
        zip_code: str | None = None,
    ) -> RawPropertyRecord | None:
        """Not applicable for FEMA."""
        return None

    async def fetch_batch(
        self, property_ids: list[str]
    ) -> list[RawPropertyRecord]:
        """Not applicable for FEMA."""
        return []

    async def stream_region(
        self,
        state: str,
        county: str | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[RawPropertyRecord]:
        """Not applicable for FEMA."""
        return
        yield  # Make this a generator  # pragma: no cover

    def get_coverage_info(self) -> dict[str, object]:
        """Return coverage information for FEMA."""
        return {
            "provider": "FEMA",
            "coverage": "Nationwide (US)",
            "data_types": ["flood_zones", "flood_risk"],
            "update_frequency": "varies by region",
            "cost": "free",
        }
