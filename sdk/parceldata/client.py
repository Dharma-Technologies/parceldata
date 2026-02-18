"""ParcelData API client with async and sync support."""

from __future__ import annotations

import asyncio
from typing import Any

import httpx

from parceldata.exceptions import (
    AuthenticationError,
    NotFoundError,
    ParcelDataError,
    RateLimitError,
    ValidationError,
)
from parceldata.models import (
    BatchResults,
    GeocodingResult,
    Property,
    SearchResults,
)
from parceldata.types import DetailTier
from parceldata.utils import build_query_params, run_sync

_STATUS_EXCEPTION_MAP: dict[int, type[ParcelDataError]] = {
    401: AuthenticationError,
    404: NotFoundError,
    422: ValidationError,
    429: RateLimitError,
}


class ParcelDataClient:
    """Client for the ParcelData API.

    Args:
        api_key: Your ParcelData API key.
        base_url: API base URL (default: https://api.parceldata.ai/v1).
        timeout: Request timeout in seconds.
        max_retries: Maximum number of retry attempts for failed requests.
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.parceldata.ai/v1",
        timeout: float = 30.0,
        max_retries: int = 3,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "User-Agent": "parceldata-python/0.1.0",
                },
                timeout=self.timeout,
            )
        return self._client

    async def _request(
        self,
        method: str,
        path: str,
        params: dict[str, str] | None = None,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make an API request with retry and error handling."""
        client = await self._get_client()
        last_exc: Exception | None = None

        for attempt in range(self.max_retries):
            try:
                response = await client.request(
                    method, path, params=params, json=json,
                )

                if response.status_code == 429:
                    retry_after = float(
                        response.headers.get("Retry-After", "1"),
                    )
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(retry_after)
                        continue
                    raise RateLimitError(retry_after=retry_after)

                if response.status_code >= 400:
                    exc_class = _STATUS_EXCEPTION_MAP.get(
                        response.status_code, ParcelDataError,
                    )
                    body = response.json()
                    message = body.get("detail", body.get("message", "API error"))
                    raise exc_class(message)

                result: dict[str, Any] = response.json()
                return result

            except httpx.HTTPStatusError as exc:
                last_exc = exc
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(0.5 * (2**attempt))
                    continue
                raise ParcelDataError(str(exc)) from exc
            except (httpx.ConnectError, httpx.TimeoutException) as exc:
                last_exc = exc
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(0.5 * (2**attempt))
                    continue
                raise ParcelDataError(
                    f"Connection failed after {self.max_retries} attempts: {exc}",
                ) from exc

        raise ParcelDataError("Request failed") from last_exc

    async def property_lookup(
        self,
        parcel_id: str,
        tier: DetailTier = "standard",
    ) -> Property:
        """Look up a single property by parcel ID.

        Args:
            parcel_id: The parcel identifier.
            tier: Response detail level (micro/standard/extended/full).

        Returns:
            Property record.
        """
        params = build_query_params(detail=tier)
        data = await self._request("GET", f"/properties/{parcel_id}", params=params)
        return Property.model_validate(data)

    async def property_search(
        self,
        query: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> SearchResults:
        """Search properties with filters.

        Args:
            query: Search filters as a dict.
            **kwargs: Additional search parameters.

        Returns:
            Paginated search results.
        """
        body = {**(query or {}), **kwargs}
        data = await self._request("POST", "/properties/search", json=body)
        return SearchResults.model_validate(data)

    async def get_comps(
        self,
        parcel_id: str,
        radius_miles: float = 1.0,
        limit: int = 10,
    ) -> dict[str, Any]:
        """Get comparable properties.

        Args:
            parcel_id: The subject property ID.
            radius_miles: Search radius in miles.
            limit: Maximum number of comparables.

        Returns:
            Comparables analysis response.
        """
        params = build_query_params(
            property_id=parcel_id,
            radius=str(radius_miles),
            limit=str(limit),
        )
        return await self._request("GET", "/analytics/comparables", params=params)

    async def batch_lookup(
        self,
        parcel_ids: list[str],
        tier: DetailTier = "standard",
    ) -> BatchResults:
        """Batch property lookup (up to 100).

        Args:
            parcel_ids: List of parcel IDs (max 100).
            tier: Response detail level.

        Returns:
            Batch lookup results.
        """
        body = {"property_ids": parcel_ids, "detail": tier}
        data = await self._request("POST", "/properties/batch", json=body)
        return BatchResults.model_validate(data)

    async def geocode(self, address: str) -> GeocodingResult:
        """Geocode an address to lat/lng + parcel.

        Args:
            address: Full address string.

        Returns:
            Geocoding result with coordinates.
        """
        params = build_query_params(address=address)
        data = await self._request(
            "GET", "/properties/address/lookup", params=params,
        )
        return GeocodingResult.model_validate(data)

    def property_lookup_sync(
        self,
        parcel_id: str,
        tier: DetailTier = "standard",
    ) -> Property:
        """Synchronous wrapper for property_lookup."""
        result = run_sync(self.property_lookup(parcel_id, tier=tier))
        return result  # type: ignore[return-value]

    def property_search_sync(
        self,
        query: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> SearchResults:
        """Synchronous wrapper for property_search."""
        result = run_sync(self.property_search(query, **kwargs))
        return result  # type: ignore[return-value]

    def batch_lookup_sync(
        self,
        parcel_ids: list[str],
        tier: DetailTier = "standard",
    ) -> BatchResults:
        """Synchronous wrapper for batch_lookup."""
        result = run_sync(self.batch_lookup(parcel_ids, tier=tier))
        return result  # type: ignore[return-value]

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self) -> ParcelDataClient:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()
