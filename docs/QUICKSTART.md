# Quick Start Guide

Get started with ParcelData in under 5 minutes.

## 1. Install the SDK

```bash
pip install parceldata
```

Requires Python 3.10+.

## 2. Get Your API Key

Sign up for a free API key:

```bash
curl -X POST https://api.parceldata.ai/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email": "you@example.com"}'
```

The response includes your API key. Save it securely — it's shown only once.

## 3. Look Up a Property

### Python SDK (async)

```python
import asyncio
from parceldata import ParcelDataClient

async def main():
    client = ParcelDataClient("your-api-key")
    prop = await client.property_lookup("TX-TRAVIS-12345")

    print(f"Address: {prop.address.formatted}")
    print(f"Value: ${prop.valuation.estimated_value:,}")
    print(f"Beds: {prop.building.bedrooms}, Baths: {prop.building.bathrooms}")
    print(f"Quality: {prop.data_quality.score}")

    await client.close()

asyncio.run(main())
```

### Python SDK (sync)

```python
from parceldata import ParcelDataClient

client = ParcelDataClient("your-api-key")
prop = client.property_lookup_sync("TX-TRAVIS-12345")
print(prop.address.formatted)
```

### curl

```bash
curl -H "X-API-Key: your-api-key" \
  https://api.parceldata.ai/v1/properties/TX-TRAVIS-12345?detail=standard
```

## 4. Search Properties

```python
results = await client.property_search({
    "city": "Austin",
    "state": "TX",
    "bedrooms_min": 3,
    "price_max": 600000,
    "limit": 10,
})

for prop in results.results:
    print(f"{prop.address.formatted} - ${prop.valuation.estimated_value:,}")
```

## 5. Batch Lookup

```python
batch = await client.batch_lookup(
    ["TX-TRAVIS-12345", "TX-TRAVIS-67890"],
    tier="micro",
)
print(f"Found: {batch.found}, Not found: {batch.not_found}")
```

## 6. MCP Server Setup

Add ParcelData to your MCP client config:

```json
{
  "mcpServers": {
    "parceldata": {
      "command": "npx",
      "args": ["-y", "@parceldata/mcp"],
      "env": {
        "PARCELDATA_API_KEY": "your-api-key"
      }
    }
  }
}
```

Available MCP tools:
- `property_lookup` — Look up a property by ID, address, or coordinates
- `property_search` — Search with filters (location, price, beds, etc.)
- `get_comparables` — Find comparable properties nearby
- `get_market_trends` — Area market statistics
- `check_zoning` — Zoning details and permitted uses
- `get_permits` — Building permit history
- `get_owner_portfolio` — Owner's other properties
- `estimate_value` — Automated valuation model
- `check_development_feasibility` — Development potential analysis

## Response Tiers

Control response size with the `detail` parameter:

| Tier | Tokens | Use Case |
|------|--------|----------|
| `micro` | ~500-1000 | Lists, summaries |
| `standard` | ~2000-4000 | Property details |
| `extended` | ~8000-16000 | Full analysis |
| `full` | ~32000+ | Complete records |

## Rate Limits

| Tier | Monthly Limit |
|------|---------------|
| Free | 3,000 |
| Pro | 50,000 |
| Business | 500,000 |
| Enterprise | 10,000,000 |

## Next Steps

- [API Reference](API_REFERENCE.md) — Full endpoint documentation
- [OpenAPI Spec](https://api.parceldata.ai/openapi.json) — Machine-readable spec
- [LLM Guide](https://api.parceldata.ai/llms.txt) — Agent-optimized description
