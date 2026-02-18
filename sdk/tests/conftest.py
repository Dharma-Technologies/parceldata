"""Test fixtures for ParcelData SDK tests."""

from __future__ import annotations

import pytest


@pytest.fixture()
def api_key() -> str:
    """Test API key."""
    return "pd_test_abc123"


@pytest.fixture()
def base_url() -> str:
    """Test API base URL."""
    return "https://api.parceldata.ai/v1"


@pytest.fixture()
def sample_property_data() -> dict[str, object]:
    """Sample property API response data."""
    return {
        "property_id": "TX-TRAVIS-12345",
        "address": {
            "street": "100 Congress Ave",
            "city": "Austin",
            "state": "TX",
            "zip": "78701",
            "formatted": "100 Congress Ave, Austin, TX 78701",
        },
        "location": {"lat": 30.2672, "lng": -97.7431},
        "parcel": {
            "apn": "12345",
            "lot_sqft": 8500,
            "lot_acres": 0.195,
        },
        "building": {
            "sqft": 2200,
            "bedrooms": 3,
            "bathrooms": 2.5,
            "year_built": 2010,
        },
        "valuation": {
            "assessed_total": 450000,
            "estimated_value": 525000,
        },
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
    }


@pytest.fixture()
def sample_search_data(sample_property_data: dict[str, object]) -> dict[str, object]:
    """Sample search response data."""
    return {
        "results": [sample_property_data],
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


@pytest.fixture()
def sample_batch_data(sample_property_data: dict[str, object]) -> dict[str, object]:
    """Sample batch lookup response data."""
    return {
        "results": [sample_property_data, None],
        "found": 1,
        "not_found": 1,
        "errors": [],
        "data_quality": {
            "score": 0.87,
            "components": {},
            "freshness_hours": 12,
            "sources": ["travis_cad"],
            "confidence": "high",
        },
    }
