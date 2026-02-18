# API Reference

Base URL: `https://api.parceldata.ai/v1`

## Authentication

All endpoints require an API key. Pass it via header:

```
Authorization: Bearer <your-api-key>
X-API-Key: <your-api-key>
```

## Properties

### GET /v1/properties/{property_id}

Look up a single property by parcel ID.

**Parameters:**
- `property_id` (path, required) — The parcel identifier
- `detail` (query, optional) — Response tier: `micro`, `standard`, `extended`, `full` (default: `standard`)
- `select` (query, optional) — Comma-separated fields to include

**Example:**
```bash
curl -H "X-API-Key: YOUR_KEY" \
  "https://api.parceldata.ai/v1/properties/TX-TRAVIS-12345?detail=standard"
```

**Response (200):**
```json
{
  "property_id": "TX-TRAVIS-12345",
  "address": {
    "street": "100 Congress Ave",
    "city": "Austin",
    "state": "TX",
    "zip": "78701",
    "formatted": "100 Congress Ave, Austin, TX 78701"
  },
  "location": { "lat": 30.2672, "lng": -97.7431 },
  "parcel": { "apn": "12345", "lot_sqft": 8500 },
  "building": { "sqft": 2200, "bedrooms": 3, "bathrooms": 2.5, "year_built": 2010 },
  "valuation": { "assessed_total": 450000, "estimated_value": 525000 },
  "data_quality": {
    "score": 0.87,
    "components": { "completeness": 0.92, "accuracy": 0.95 },
    "freshness_hours": 12,
    "sources": ["travis_cad"],
    "confidence": "high"
  }
}
```

### GET /v1/properties/address/lookup

Find a property by address.

**Parameters:**
- `street` (query, required)
- `city` (query, optional)
- `state` (query, optional)
- `zip` (query, optional)

**Example:**
```bash
curl -H "X-API-Key: YOUR_KEY" \
  "https://api.parceldata.ai/v1/properties/address/lookup?street=100+Congress+Ave&city=Austin&state=TX"
```

### GET /v1/properties/coordinates/lookup

Find a property by lat/lng coordinates.

**Parameters:**
- `lat` (query, required) — Latitude
- `lng` (query, required) — Longitude

**Example:**
```bash
curl -H "X-API-Key: YOUR_KEY" \
  "https://api.parceldata.ai/v1/properties/coordinates/lookup?lat=30.2672&lng=-97.7431"
```

## Search

### POST /v1/properties/search

Search properties with filters.

**Body Parameters:**
- `state` — State code (e.g., "TX")
- `city` — City name
- `zip` — ZIP code
- `county` — County name
- `property_type` — Array of property types
- `bedrooms_min`, `bedrooms_max` — Bedroom range
- `bathrooms_min` — Minimum bathrooms
- `sqft_min`, `sqft_max` — Square footage range
- `year_built_min`, `year_built_max` — Year built range
- `price_min`, `price_max` — Price range
- `limit` — Results per page (1-100, default: 25)
- `offset` — Pagination offset

**Example:**
```bash
curl -X POST -H "X-API-Key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  "https://api.parceldata.ai/v1/properties/search" \
  -d '{"city": "Austin", "state": "TX", "bedrooms_min": 3, "limit": 10}'
```

**Response (200):**
```json
{
  "results": [{ "property_id": "...", "address": {...}, ... }],
  "total": 1542,
  "limit": 10,
  "offset": 0,
  "has_more": true,
  "data_quality": { "score": 0.85, "confidence": "high" }
}
```

## Batch

### POST /v1/properties/batch

Look up multiple properties at once (max 100).

**Body:**
```json
{
  "property_ids": ["TX-TRAVIS-12345", "TX-TRAVIS-67890"],
  "detail": "standard"
}
```

**Response (200):**
```json
{
  "results": [{ "property_id": "TX-TRAVIS-12345", ... }, null],
  "found": 1,
  "not_found": 1,
  "errors": [],
  "data_quality": { "score": 0.87, "confidence": "high" }
}
```

## Analytics

### GET /v1/analytics/comparables

Get comparable properties.

**Parameters:**
- `property_id` (query, required) — Subject property ID
- `radius` (query, optional) — Search radius in miles (default: 1.0)
- `limit` (query, optional) — Max comparables (default: 10)

**Example:**
```bash
curl -H "X-API-Key: YOUR_KEY" \
  "https://api.parceldata.ai/v1/analytics/comparables?property_id=TX-TRAVIS-12345&radius=1.0&limit=5"
```

### GET /v1/analytics/market-trends

Get market trend data for an area.

**Parameters:**
- `zip` (query, required) — ZIP code
- `period` (query, optional) — Time period (default: "12m")

**Example:**
```bash
curl -H "X-API-Key: YOUR_KEY" \
  "https://api.parceldata.ai/v1/analytics/market-trends?zip=78701"
```

## Auth

### POST /v1/auth/signup

Create a new account and get an API key.

**Body:**
```json
{ "email": "user@example.com" }
```

### POST /v1/auth/keys

Create a new API key (requires authentication).

### GET /v1/auth/keys

List all API keys for the authenticated account.

### DELETE /v1/auth/keys/{key_id}

Revoke an API key.

## Error Codes

| Status | Meaning |
|--------|---------|
| 200 | Success |
| 401 | Invalid or missing API key |
| 404 | Property not found |
| 422 | Invalid request parameters |
| 429 | Rate limit or quota exceeded |
| 500 | Internal server error |

All error responses include a `data_quality` object:

```json
{
  "detail": "Property not found",
  "data_quality": { "score": 0, "confidence": "none" }
}
```

## Rate Limits

Response headers indicate rate limit status:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 99
X-RateLimit-Reset: 1706745600
X-Usage-Limit: 3000
X-Usage-Remaining: 2999
```

## Data Quality

Every response includes a `data_quality` object:

```json
{
  "score": 0.87,
  "components": {
    "completeness": 0.92,
    "accuracy": 0.95,
    "consistency": 0.88,
    "timeliness": 0.80,
    "validity": 0.99,
    "uniqueness": 0.98
  },
  "freshness_hours": 12,
  "sources": ["travis_cad", "actris_mls"],
  "confidence": "high"
}
```

**Score formula:**
```
score = completeness * 0.25 + accuracy * 0.25 + consistency * 0.20
      + timeliness * 0.15 + validity * 0.10 + uniqueness * 0.05
```

**Confidence levels:**
- `high` — score >= 0.85
- `medium` — score >= 0.65
- `low` — score < 0.65
