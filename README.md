# ParcelData

> Real estate data for AI agents

**ParcelData** is an open source real estate data platform built for the agent economy. We aggregate, normalize, and serve property data through a unified API and MCP server.

[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![TypeScript](https://img.shields.io/badge/typescript-5.0+-blue.svg)](https://www.typescriptlang.org/)
[![API Status](https://img.shields.io/badge/API-v1.0.0-green.svg)](https://api.parceldata.ai/openapi.json)

## Quick Start

```bash
pip install parceldata
```

```python
from parceldata import ParcelDataClient

client = ParcelDataClient("your-api-key")
prop = await client.property_lookup("TX-TRAVIS-12345")
print(prop.address.formatted)  # "100 Congress Ave, Austin, TX 78701"
print(prop.data_quality.score)  # 0.87
```

### MCP Integration

```json
{
  "mcpServers": {
    "parceldata": {
      "command": "npx",
      "args": ["-y", "@parceldata/mcp"],
      "env": { "PARCELDATA_API_KEY": "your-api-key" }
    }
  }
}
```

## Features

- **Universal API** — Every US property. REST, GraphQL, or MCP.
- **Agent-Native** — Built for MCP. Your agent calls ParcelData like any other tool.
- **Open Source** — MIT licensed. Self-host with your own data, or use parceldata.ai.
- **Data Quality Scores** — Every response includes confidence scores and freshness.
- **13 Data Categories** — Property records, valuations, zoning, permits, environmental, and more.

## Data Categories

| Category | Description |
|----------|-------------|
| Property Records | Ownership, legal description, lot size, building specs |
| Valuations | Assessed value, estimated market value, price history |
| Listings | MLS active/pending/sold, commercial listings |
| Transactions | Deed transfers, sales history, price per sqft |
| Zoning | Zone codes, permitted uses, setbacks, FAR, height limits |
| Permits | Building permits, inspections, status, contractor info |
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
docker-compose up -d
```

## Architecture

```
Data Sources (Regrid, ATTOM, MLS, Census, FEMA)
         |
    Data Pipeline (Python ETL)
         |
    PostgreSQL + PostGIS + pgvector
         |
    API Layer (FastAPI + GraphQL + MCP)
```

## Documentation

- [Quick Start](docs/QUICKSTART.md)
- [API Reference](docs/API_REFERENCE.md)
- [OpenAPI Spec](https://api.parceldata.ai/openapi.json)
- [Agent-Readable](https://api.parceldata.ai/llms.txt)

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License — see [LICENSE](LICENSE) for details.

## Built By

[Dharma Technologies, Inc.](https://dharma.tech)
