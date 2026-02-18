"""OpenAPI specification configuration for ParcelData API."""

from __future__ import annotations

OPENAPI_TAGS = [
    {
        "name": "Properties",
        "description": "Property lookup, search, and batch operations.",
    },
    {
        "name": "Search",
        "description": "Full-text and filtered property search.",
    },
    {
        "name": "Batch",
        "description": "Batch property lookups (up to 100 per request).",
    },
    {
        "name": "Analytics",
        "description": "Comparable properties and market trend analysis.",
    },
    {
        "name": "Auth",
        "description": "Account signup, API key management.",
    },
    {
        "name": "Account",
        "description": "Usage statistics and billing management.",
    },
    {
        "name": "Webhooks",
        "description": "Stripe webhook receiver for billing events.",
    },
    {
        "name": "Health",
        "description": "API health checks and version info.",
    },
    {
        "name": "Admin",
        "description": "Administrative and operational endpoints.",
    },
]

PROPERTY_RESPONSE_EXAMPLE = {
    "property_id": "TX-TRAVIS-12345",
    "address": {
        "street": "100 Congress Ave",
        "unit": None,
        "city": "Austin",
        "state": "TX",
        "zip": "78701",
        "zip4": None,
        "county": "Travis",
        "formatted": "100 Congress Ave, Austin, TX 78701",
    },
    "location": {"lat": 30.2672, "lng": -97.7431, "geoid": None},
    "parcel": {
        "apn": "12345",
        "legal_description": None,
        "lot_sqft": 8500,
        "lot_acres": 0.195,
        "lot_dimensions": None,
    },
    "building": {
        "sqft": 2200,
        "stories": 2,
        "bedrooms": 3,
        "bathrooms": 2.5,
        "year_built": 2010,
        "construction": "Frame",
        "roof": "Composition",
        "foundation": "Slab",
        "garage": "Attached",
        "garage_spaces": 2,
        "pool": False,
    },
    "valuation": {
        "assessed_total": 450000,
        "assessed_land": 150000,
        "assessed_improvements": 300000,
        "assessed_year": 2025,
        "estimated_value": 525000,
        "estimated_value_low": 490000,
        "estimated_value_high": 560000,
        "price_per_sqft": 238.64,
    },
    "ownership": {
        "owner_name": "Smith, John",
        "owner_type": "individual",
        "owner_occupied": True,
        "acquisition_date": "2018-06-15",
        "acquisition_price": 380000,
        "ownership_length_years": 7.5,
    },
    "zoning": None,
    "listing": None,
    "tax": None,
    "environmental": None,
    "schools": None,
    "hoa": None,
    "data_quality": {
        "score": 0.87,
        "components": {
            "completeness": 0.92,
            "accuracy": 0.95,
            "consistency": 0.88,
            "timeliness": 0.80,
            "validity": 0.99,
            "uniqueness": 0.98,
        },
        "freshness_hours": 12,
        "sources": ["travis_cad", "actris_mls"],
        "confidence": "high",
    },
    "provenance": None,
    "metadata": {},
}

MICRO_RESPONSE_EXAMPLE = {
    "id": "TX-TRAVIS-12345",
    "price": 525000,
    "beds": 3,
    "baths": 2.5,
    "sqft": 2200,
    "addr": "100 Congress Ave, Austin, TX 78701",
    "data_quality": {
        "score": 0.87,
        "components": {},
        "freshness_hours": 12,
        "sources": ["travis_cad"],
        "confidence": "high",
    },
}

ERROR_RESPONSE_EXAMPLE = {
    "detail": "Property not found",
    "data_quality": {
        "score": 0,
        "confidence": "none",
        "message": "No data available",
    },
}

SEARCH_RESPONSE_EXAMPLE = {
    "results": [PROPERTY_RESPONSE_EXAMPLE],
    "total": 1,
    "limit": 25,
    "offset": 0,
    "has_more": False,
    "data_quality": {
        "score": 0.87,
        "components": {},
        "freshness_hours": 12,
        "sources": ["travis_cad"],
        "confidence": "high",
    },
}
