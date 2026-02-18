"""Adapter for US Census Bureau ACS data (free)."""

from __future__ import annotations

from collections.abc import AsyncIterator

import httpx

from app.services.ingestion.base import ProviderAdapter, RawPropertyRecord


class CensusAdapter(ProviderAdapter):
    """Adapter for US Census Bureau ACS data (free).

    Provides demographics, income, and housing data at various
    geographic levels (state, county, tract, block group).
    """

    name = "census"
    source_type = "demographics"
    base_url = "https://api.census.gov/data"

    def __init__(self, api_key: str | None = None) -> None:
        super().__init__(api_key)
        self.client = httpx.AsyncClient(timeout=30.0)

    async def fetch_demographics(
        self,
        state_fips: str,
        county_fips: str | None = None,
        tract: str | None = None,
    ) -> dict[str, str]:
        """Fetch ACS demographics for a geography.

        Args:
            state_fips: 2-digit state FIPS code.
            county_fips: 3-digit county FIPS code.
            tract: Census tract number.

        Returns:
            Dictionary of variable names to values.
        """
        year = 2023
        dataset = f"{year}/acs/acs5"

        variables = [
            "B01003_001E",  # Total population
            "B19013_001E",  # Median household income
            "B25077_001E",  # Median home value
            "B25064_001E",  # Median gross rent
            "B01002_001E",  # Median age
        ]

        # Build geography
        if tract and county_fips:
            geo_for = f"tract:{tract}"
            geo_in = f"state:{state_fips}&in=county:{county_fips}"
        elif county_fips:
            geo_for = f"county:{county_fips}"
            geo_in = f"state:{state_fips}"
        else:
            geo_for = f"state:{state_fips}"
            geo_in = ""

        url = f"{self.base_url}/{dataset}"
        params: dict[str, str] = {
            "get": ",".join(variables),
            "for": geo_for,
        }
        if geo_in:
            params["in"] = geo_in
        if self.api_key:
            params["key"] = self.api_key

        response = await self.client.get(url, params=params)
        response.raise_for_status()
        data: list[list[str]] = response.json()

        # Parse response (first row is headers)
        if len(data) > 1:
            headers = data[0]
            values = data[1]
            return dict(zip(headers, values, strict=False))

        return {}

    async def fetch_property(
        self, property_id: str
    ) -> RawPropertyRecord | None:
        """Not applicable for Census — use fetch_demographics."""
        return None

    async def fetch_by_address(
        self,
        street: str,
        city: str,
        state: str,
        zip_code: str | None = None,
    ) -> RawPropertyRecord | None:
        """Not applicable for Census."""
        return None

    async def fetch_batch(
        self, property_ids: list[str]
    ) -> list[RawPropertyRecord]:
        """Not applicable for Census."""
        return []

    async def stream_region(
        self,
        state: str,
        county: str | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[RawPropertyRecord]:
        """Not applicable for Census."""
        return
        yield  # Make this a generator  # pragma: no cover

    def get_coverage_info(self) -> dict[str, object]:
        """Return coverage information for Census Bureau."""
        return {
            "provider": "US Census Bureau",
            "coverage": "Nationwide (US)",
            "data_types": ["demographics", "income", "housing"],
            "update_frequency": "annual (ACS 5-year)",
            "cost": "free",
        }
