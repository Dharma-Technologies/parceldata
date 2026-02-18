"""ParcelData Python SDK — Real estate data for AI agents."""

from __future__ import annotations

from parceldata.client import ParcelDataClient
from parceldata.exceptions import (
    AuthenticationError,
    NotFoundError,
    ParcelDataError,
    QuotaExceededError,
    RateLimitError,
    ValidationError,
)
from parceldata.models import (
    BatchResults,
    DataQuality,
    GeocodingResult,
    Property,
    PropertySummary,
    Provenance,
    SearchResults,
)

__version__ = "0.1.0"
__all__ = [
    "ParcelDataClient",
    "AuthenticationError",
    "BatchResults",
    "DataQuality",
    "GeocodingResult",
    "NotFoundError",
    "ParcelDataError",
    "Property",
    "PropertySummary",
    "Provenance",
    "QuotaExceededError",
    "RateLimitError",
    "SearchResults",
    "ValidationError",
]
