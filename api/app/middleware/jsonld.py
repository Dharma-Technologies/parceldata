"""JSON-LD structured data for agent-readable responses."""

from __future__ import annotations

import json
from typing import Any

ORGANIZATION_JSONLD: dict[str, Any] = {
    "@context": "https://schema.org",
    "@type": "Organization",
    "name": "ParcelData.ai",
    "url": "https://parceldata.ai",
    "description": "Clean, universal real estate data for AI agents",
    "email": "hello@dharma.tech",
    "sameAs": [
        "https://github.com/Dharma-Technologies/parceldata",
    ],
}

WEB_API_JSONLD: dict[str, Any] = {
    "@context": "https://schema.org",
    "@type": "WebAPI",
    "name": "ParcelData.ai API",
    "description": (
        "REST API providing clean, normalized US property data "
        "including valuations, ownership, tax, zoning, and spatial data."
    ),
    "url": "https://api.parceldata.ai",
    "documentation": "https://api.parceldata.ai/v1/docs",
    "termsOfService": "https://parceldata.ai/terms",
    "provider": {
        "@type": "Organization",
        "name": "ParcelData.ai",
        "url": "https://parceldata.ai",
    },
}

DATA_CATALOG_JSONLD: dict[str, Any] = {
    "@context": "https://schema.org",
    "@type": "DataCatalog",
    "name": "ParcelData.ai Property Data",
    "description": (
        "Comprehensive US property records including parcel data, "
        "building characteristics, valuations, ownership history, "
        "tax records, zoning, permits, and environmental data."
    ),
    "url": "https://api.parceldata.ai",
    "provider": {
        "@type": "Organization",
        "name": "ParcelData.ai",
    },
    "dataset": [
        {
            "@type": "Dataset",
            "name": "US Property Records",
            "description": "Parcel, building, and valuation data",
        },
        {
            "@type": "Dataset",
            "name": "Ownership & Transaction History",
            "description": "Current and historical ownership records",
        },
        {
            "@type": "Dataset",
            "name": "Zoning & Permits",
            "description": "Zoning classifications and building permits",
        },
        {
            "@type": "Dataset",
            "name": "Environmental & Flood Data",
            "description": "FEMA flood zones, wildfire, earthquake risk",
        },
    ],
}


def get_jsonld_script() -> str:
    """Return JSON-LD script tags for HTML embedding."""
    schemas = [ORGANIZATION_JSONLD, WEB_API_JSONLD, DATA_CATALOG_JSONLD]
    parts: list[str] = []
    for schema in schemas:
        parts.append(
            f'<script type="application/ld+json">'
            f"{json.dumps(schema, separators=(',', ':'))}"
            f"</script>",
        )
    return "\n".join(parts)
