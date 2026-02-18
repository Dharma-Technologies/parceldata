"""Adapter for Regrid parcel data API."""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import datetime

import httpx

from app.config import settings
from app.services.ingestion.base import ProviderAdapter, RawPropertyRecord


class RegridAdapter(ProviderAdapter):
    """Adapter for Regrid parcel data API."""

    name = "regrid"
    source_type = "parcel_data"
    base_url = "https://app.regrid.com/api/v1"

    def __init__(self, api_key: str | None = None) -> None:
        super().__init__(api_key or settings.regrid_api_key)
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=30.0,
        )

    async def fetch_property(
        self, property_id: str
    ) -> RawPropertyRecord | None:
        """Fetch property by Regrid parcel ID."""
        try:
            response = await self.client.get(f"/parcels/{property_id}")
            response.raise_for_status()
            data: dict[str, object] = response.json()
            return self._to_raw_record(data)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise

    async def fetch_by_address(
        self,
        street: str,
        city: str,
        state: str,
        zip_code: str | None = None,
    ) -> RawPropertyRecord | None:
        """Fetch property by address using Regrid geocoding."""
        address = f"{street}, {city}, {state}"
        if zip_code:
            address += f" {zip_code}"

        response = await self.client.get(
            "/parcels/search",
            params={"address": address, "limit": 1},
        )
        response.raise_for_status()
        body: dict[str, object] = response.json()
        results = body.get("results")
        if isinstance(results, list) and results:
            return self._to_raw_record(results[0])
        return None

    async def fetch_batch(
        self, property_ids: list[str]
    ) -> list[RawPropertyRecord]:
        """Fetch multiple properties."""
        results: list[RawPropertyRecord] = []
        for prop_id in property_ids:
            record = await self.fetch_property(prop_id)
            if record:
                results.append(record)
        return results

    async def stream_region(
        self,
        state: str,
        county: str | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[RawPropertyRecord]:
        """Stream parcels in a region."""
        params: dict[str, str | int] = {"state": state}
        if county:
            params["county"] = county

        offset = 0
        page_size = 100
        count = 0

        while True:
            params["offset"] = offset
            effective_limit = (
                min(page_size, limit - offset) if limit else page_size
            )
            params["limit"] = effective_limit

            response = await self.client.get("/parcels", params=params)
            response.raise_for_status()
            body: dict[str, object] = response.json()

            parcels = body.get("results")
            if not isinstance(parcels, list) or not parcels:
                break

            for parcel in parcels:
                yield self._to_raw_record(parcel)
                count += 1
                if limit and count >= limit:
                    return

            offset += len(parcels)

    def _to_raw_record(self, data: dict[str, object]) -> RawPropertyRecord:
        """Convert Regrid response to RawPropertyRecord."""
        properties = data.get("properties")
        props = properties if isinstance(properties, dict) else {}
        geometry = data.get("geometry")
        geo = geometry if isinstance(geometry, dict) else {}

        # Extract coordinates from geometry
        lat: float | None = None
        lng: float | None = None
        if geo.get("type") == "Point":
            coords = geo.get("coordinates")
            if isinstance(coords, list) and len(coords) >= 2:
                lng_val, lat_val = coords[0], coords[1]
                if isinstance(lng_val, (int, float)) and isinstance(
                    lat_val, (int, float)
                ):
                    lng, lat = float(lng_val), float(lat_val)

        record_id = data.get("id")

        return RawPropertyRecord(
            source_system="regrid",
            source_type="parcel_data",
            source_record_id=str(record_id) if record_id else "",
            extraction_timestamp=datetime.utcnow(),
            raw_data=data,
            parcel_id=str(props.get("parcelnumb", "")) or None,
            address_raw=str(props.get("address", "")) or None,
            latitude=lat,
            longitude=lng,
        )

    def get_coverage_info(self) -> dict[str, object]:
        """Return coverage information for Regrid."""
        return {
            "provider": "Regrid",
            "coverage": "Nationwide (US)",
            "data_types": [
                "parcel_boundaries",
                "ownership",
                "zoning",
                "tax",
            ],
            "update_frequency": "monthly",
        }
