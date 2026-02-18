"""Base class for data provider adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from datetime import datetime

from pydantic import BaseModel


class RawPropertyRecord(BaseModel):
    """Raw property record from a data provider."""

    source_system: str
    source_type: str
    source_record_id: str
    extraction_timestamp: datetime
    raw_data: dict[str, object]

    # Parsed fields (provider fills what it can)
    parcel_id: str | None = None
    address_raw: str | None = None
    latitude: float | None = None
    longitude: float | None = None


class ProviderAdapter(ABC):
    """Base class for data provider adapters.

    Each adapter wraps a specific data source (Regrid, ATTOM, Census, etc.)
    and normalizes responses into RawPropertyRecord instances for downstream
    processing by the ingestion pipeline.
    """

    name: str
    source_type: str

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key

    @abstractmethod
    async def fetch_property(
        self, property_id: str
    ) -> RawPropertyRecord | None:
        """Fetch a single property by ID."""

    @abstractmethod
    async def fetch_by_address(
        self,
        street: str,
        city: str,
        state: str,
        zip_code: str | None = None,
    ) -> RawPropertyRecord | None:
        """Fetch property by address."""

    @abstractmethod
    async def fetch_batch(
        self,
        property_ids: list[str],
    ) -> list[RawPropertyRecord]:
        """Fetch multiple properties by ID."""

    @abstractmethod
    def stream_region(
        self,
        state: str,
        county: str | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[RawPropertyRecord]:
        """Stream all properties in a region."""

    @abstractmethod
    def get_coverage_info(self) -> dict[str, object]:
        """Return coverage information for this provider."""
