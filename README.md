# ParcelData

> Real estate data for AI agents

**ParcelData** is an open source real estate data platform built for the agent economy. We aggregate, normalize, and serve property data through a unified API and MCP server.

[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![TypeScript](https://img.shields.io/badge/typescript-5.0+-blue.svg)](https://www.typescriptlang.org/)

## Quick Start

### Install the SDK

```bash
# Python
pip install parceldata

# TypeScript/MCP
npm install @parceldata/mcp
```

### Use the API

```python
from parceldata import ParcelData

pd = ParcelData(api_key="your-key")
property = pd.lookup("123 Main St, Austin, TX")

print(property.zoning)       # "R1 - Single Family"
print(property.lot_sqft)     # 8500
print(property.tax_assessed) # 425000
```

### MCP Integration

```json
{
  "name": "parceldata",
  "tools": ["property_lookup", "property_search", "get_comps", "check_zoning"]
}
```

## Features

- **📡 Universal API** — Every US property. REST, GraphQL, or MCP.
- **🤖 Agent-Native** — Built for MCP. Your agent calls ParcelData like any other tool.
- **🔓 Open Source** — MIT licensed. Self-host with your own data, or use parceldata.ai.
- **📊 Data Quality Scores** — Every response includes confidence scores and freshness.
- **🏢 Commercial + Residential** — 155M+ properties across all property types.
- **🗺️ 13 Data Categories** — Property records, valuations, zoning, permits, environmental, and more.

## Data Categories

| Category | Description |
|----------|-------------|
| Property Records | Ownership, legal description, lot size, building specs |
| Valuations | Assessed value, estimated market value, price history |
| Listings | MLS active/pending/sold, commercial listings |
| Transactions | Deed transfers, sales history, price per sqft |
| Zoning | Zone codes, permitted uses, setbacks, FAR, height limits |
| Permits | Building permits, inspections, status, contractor info |
| Title & Liens | Ownership chain, mortgages, liens, encumbrances |
| Tax | Property tax amounts, rates, payment history |
| Environmental | Flood zones, superfund proximity, hazards |
| Demographics | Census data, income, population, growth trends |
| Schools | District boundaries, ratings, enrollment |
| Market Analytics | Comparables, price trends, days on market |

## Self-Hosting

ParcelData is fully open source. Run your own instance with your own data licenses.

```bash
git clone https://github.com/Dharma-Technologies/parceldata
cd parceldata
cp .env.example .env
# Add your Regrid API key, ATTOM credentials, etc.
docker-compose up -d
```

## Architecture

```
┌─────────────────────────────────────┐
│           Data Sources              │
│  (Regrid, ATTOM, MLS, Census...)    │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│        Data Pipeline                │
│  (Python ETL + Apache Airflow)      │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│        PostgreSQL + PostGIS         │
│        + pgvector                   │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│          API Layer                  │
│  (FastAPI + GraphQL + MCP Server)   │
└─────────────────────────────────────┘
```

## Documentation

- [API Reference](https://docs.parceldata.ai)
- [MCP Tools](https://docs.parceldata.ai/mcp)
- [Self-Hosting Guide](https://docs.parceldata.ai/self-hosting)
- [Data Sources](https://docs.parceldata.ai/data-sources)

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License — see [LICENSE](LICENSE) for details.

## Built By

[Dharma Technologies, Inc.](https://dharma.tech)
