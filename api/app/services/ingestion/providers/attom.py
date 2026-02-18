"""Adapter for ATTOM property data API."""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import datetime

import httpx

from app.config import settings
from app.services.ingestion.base import ProviderAdapter, RawPropertyRecord


class ATTOMAdapter(ProviderAdapter):
    """Adapter for ATTOM property data API."""

    name = "attom"
    source_type = "property_records"
    base_url = "https://api.gateway.attomdata.com"

    def __init__(self, api_key: str | None = None) -> None:
        super().__init__(api_key or settings.attom_api_key)
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "apikey": self.api_key or "",
                "Accept": "application/json",
            },
            timeout=30.0,
        )

    async def fetch_property(
        self, property_id: str
    ) -> RawPropertyRecord | None:
        """Fetch property by ATTOM ID."""
        try:
            response = await self.client.get(
                "/propertyapi/v1.0.0/property/detail",
                params={"attomid": property_id},
            )
            response.raise_for_status()
            data: dict[str, object] = response.json()

            properties = data.get("property")
            if isinstance(properties, list) and properties:
                return self._to_raw_record(properties[0])
            return None
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
        """Fetch property by address."""
        address2 = f"{city}, {state}"
        if zip_code:
            address2 += f" {zip_code}"

        response = await self.client.get(
            "/propertyapi/v1.0.0/property/address",
            params={"address1": street, "address2": address2},
        )
        response.raise_for_status()
        data: dict[str, object] = response.json()

        properties = data.get("property")
        if isinstance(properties, list) and properties:
            return self._to_raw_record(properties[0])
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
        """Stream properties in a region via snapshot endpoint."""
        params: dict[str, str] = {"geoid": state}

        response = await self.client.get(
            "/propertyapi/v1.0.0/property/snapshot",
            params=params,
        )
        response.raise_for_status()
        data: dict[str, object] = response.json()

        properties = data.get("property")
        if not isinstance(properties, list):
            return

        for i, prop in enumerate(properties):
            if limit and i >= limit:
                return
            yield self._to_raw_record(prop)

    def _to_raw_record(self, data: object) -> RawPropertyRecord:
        """Convert ATTOM response to RawPropertyRecord."""
        if not isinstance(data, dict):
            data = {}

        address = data.get("address")
        addr = address if isinstance(address, dict) else {}
        location = data.get("location")
        loc = location if isinstance(location, dict) else {}
        identifier = data.get("identifier")
        ident = identifier if isinstance(identifier, dict) else {}

        line1 = str(addr.get("line1", "")).strip()
        line2 = str(addr.get("line2", "")).strip()
        address_raw = f"{line1} {line2}".strip() or None

        lat_val = loc.get("latitude")
        lng_val = loc.get("longitude")
        lat = float(lat_val) if isinstance(lat_val, (int, float)) else None
        lng = float(lng_val) if isinstance(lng_val, (int, float)) else None

        attom_id = ident.get("attomId")
        apn = ident.get("apn")

        return RawPropertyRecord(
            source_system="attom",
            source_type="property_records",
            source_record_id=str(attom_id) if attom_id else "",
            extraction_timestamp=datetime.utcnow(),
            raw_data=data,
            parcel_id=str(apn) if apn else None,
            address_raw=address_raw,
            latitude=lat,
            longitude=lng,
        )

    def get_coverage_info(self) -> dict[str, object]:
        """Return coverage information for ATTOM."""
        return {
            "provider": "ATTOM",
            "coverage": "155M+ US properties",
            "data_types": [
                "ownership",
                "valuation",
                "tax",
                "title",
                "building",
            ],
            "update_frequency": "monthly",
        }
