import type { Tool } from "@modelcontextprotocol/sdk/types.js";

export const TOOLS: Tool[] = [
  {
    name: "property_lookup",
    description:
      "Get comprehensive property data by address, parcel ID, or coordinates",
    inputSchema: {
      type: "object",
      properties: {
        address: {
          type: "string",
          description:
            "Full property address (e.g., '123 Main St, Austin, TX 78701')",
        },
        parcel_id: {
          type: "string",
          description: "Dharma parcel ID (e.g., 'TX-TRAVIS-0234567')",
        },
        lat: {
          type: "number",
          description: "Latitude coordinate",
        },
        lng: {
          type: "number",
          description: "Longitude coordinate",
        },
        include: {
          type: "array",
          items: { type: "string" },
          description:
            "Data sections to include: 'basic', 'valuation', 'zoning', 'permits', 'title', 'tax', 'environmental', 'schools', 'hoa', 'demographics', 'all'",
        },
        detail: {
          type: "string",
          enum: ["micro", "standard", "extended", "full"],
          description: "Response detail level for token optimization",
        },
      },
    },
  },
  {
    name: "property_search",
    description:
      "Search for properties matching criteria within a geographic area",
    inputSchema: {
      type: "object",
      properties: {
        city: { type: "string" },
        state: { type: "string" },
        zip: { type: "string" },
        bounds: {
          type: "object",
          properties: {
            north: { type: "number" },
            south: { type: "number" },
            east: { type: "number" },
            west: { type: "number" },
          },
        },
        property_type: {
          type: "array",
          items: {
            type: "string",
            enum: [
              "single_family",
              "condo",
              "townhouse",
              "multi_family",
              "land",
              "commercial",
            ],
          },
        },
        bedrooms_min: { type: "integer" },
        bedrooms_max: { type: "integer" },
        bathrooms_min: { type: "number" },
        sqft_min: { type: "integer" },
        sqft_max: { type: "integer" },
        lot_sqft_min: { type: "integer" },
        year_built_min: { type: "integer" },
        year_built_max: { type: "integer" },
        price_min: { type: "integer" },
        price_max: { type: "integer" },
        listing_status: {
          type: "array",
          items: {
            type: "string",
            enum: ["active", "pending", "sold", "off_market"],
          },
        },
        zoning: {
          type: "array",
          items: { type: "string" },
        },
        limit: { type: "integer" },
      },
      required: ["state"],
    },
  },
  {
    name: "get_comparables",
    description:
      "Find comparable sales for a property to estimate value",
    inputSchema: {
      type: "object",
      properties: {
        property_id: {
          type: "string",
          description: "Dharma parcel ID of subject property",
        },
        address: {
          type: "string",
          description:
            "Address of subject property (alternative to property_id)",
        },
        radius_miles: {
          type: "number",
          description: "Search radius in miles",
        },
        months: {
          type: "integer",
          description: "Look back period in months",
        },
        limit: { type: "integer" },
      },
    },
  },
  {
    name: "get_market_trends",
    description: "Get market statistics and trends for an area",
    inputSchema: {
      type: "object",
      properties: {
        zip: { type: "string" },
        city: { type: "string" },
        county: { type: "string" },
        state: { type: "string" },
        property_type: { type: "string" },
        period: {
          type: "string",
          enum: ["3m", "6m", "12m", "24m", "5y"],
        },
      },
      required: ["state"],
    },
  },
  {
    name: "check_zoning",
    description: "Check if a specific use is permitted at a property",
    inputSchema: {
      type: "object",
      properties: {
        property_id: { type: "string" },
        address: { type: "string" },
        proposed_use: {
          type: "string",
          description:
            "The intended use (e.g., 'single_family', 'duplex', 'retail', 'restaurant', 'adu')",
        },
      },
      required: ["proposed_use"],
    },
  },
  {
    name: "get_permits",
    description:
      "Get permit history and active permits for a property",
    inputSchema: {
      type: "object",
      properties: {
        property_id: { type: "string" },
        address: { type: "string" },
        status: {
          type: "array",
          items: {
            type: "string",
            enum: [
              "issued",
              "in_review",
              "approved",
              "inspection",
              "finaled",
              "expired",
            ],
          },
        },
        permit_type: {
          type: "array",
          items: {
            type: "string",
            enum: [
              "building",
              "electrical",
              "plumbing",
              "mechanical",
              "demolition",
              "grading",
            ],
          },
        },
        since_date: { type: "string" },
      },
    },
  },
  {
    name: "get_owner_portfolio",
    description: "Find all properties owned by a person or entity",
    inputSchema: {
      type: "object",
      properties: {
        owner_name: {
          type: "string",
          description: "Name of owner (person or entity)",
        },
        state: { type: "string" },
        include_related_entities: {
          type: "boolean",
          description:
            "Include properties owned by related LLCs/trusts",
        },
      },
      required: ["owner_name"],
    },
  },
  {
    name: "estimate_value",
    description:
      "Get an automated valuation estimate for a property",
    inputSchema: {
      type: "object",
      properties: {
        property_id: { type: "string" },
        address: { type: "string" },
        adjustments: {
          type: "object",
          properties: {
            condition: {
              type: "string",
              enum: ["poor", "fair", "average", "good", "excellent"],
            },
            recent_renovations: { type: "boolean" },
            renovation_value: { type: "integer" },
          },
        },
      },
    },
  },
  {
    name: "check_development_feasibility",
    description:
      "Given a parcel, return max buildable area based on zoning code — FAR, height limits, setbacks, permitted uses",
    inputSchema: {
      type: "object",
      properties: {
        property_id: {
          type: "string",
          description: "Dharma parcel ID (e.g., 'TX-TRAVIS-0234567')",
        },
        proposed_use: {
          type: "string",
          description:
            "Optional: intended use (e.g., 'single_family', 'multifamily', 'retail')",
        },
      },
      required: ["property_id"],
    },
  },
];
