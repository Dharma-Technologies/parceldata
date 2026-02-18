import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { propertyLookup } from "../src/tools/property-lookup.js";
import { propertySearch } from "../src/tools/property-search.js";
import { getComparables } from "../src/tools/get-comparables.js";
import { getMarketTrends } from "../src/tools/get-market-trends.js";
import { checkZoning } from "../src/tools/check-zoning.js";
import { getPermits } from "../src/tools/get-permits.js";
import { getOwnerPortfolio } from "../src/tools/get-owner-portfolio.js";
import { estimateValue } from "../src/tools/estimate-value.js";
import { checkDevelopmentFeasibility } from "../src/tools/check-development-feasibility.js";

describe("Tool implementations", () => {
  const originalFetch = globalThis.fetch;

  beforeEach(() => {
    globalThis.fetch = vi.fn();
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
  });

  function mockApiSuccess(data: unknown) {
    vi.mocked(globalThis.fetch).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(data),
    } as Response);
  }

  function mockApiError(status: number, message: string) {
    vi.mocked(globalThis.fetch).mockResolvedValue({
      ok: false,
      statusText: "Error",
      json: () => Promise.resolve({ message }),
    } as Response);
  }

  describe("propertyLookup", () => {
    it("returns error when no identifier provided", async () => {
      const result = await propertyLookup({});
      const text = JSON.parse(result.content[0].text);
      expect(text.error).toContain("Must provide");
    });

    it("looks up by parcel_id", async () => {
      const property = { property_id: "TX-TRAVIS-001", address: {} };
      mockApiSuccess(property);

      const result = await propertyLookup({
        parcel_id: "TX-TRAVIS-001",
      });
      const text = JSON.parse(result.content[0].text);
      expect(text.property_id).toBe("TX-TRAVIS-001");
    });

    it("looks up by address", async () => {
      const property = { property_id: "TX-TRAVIS-001" };
      mockApiSuccess(property);

      const result = await propertyLookup({
        address: "123 Main St, Austin, TX 78701",
      });

      const url = vi.mocked(globalThis.fetch).mock.calls[0][0] as string;
      expect(url).toContain("/v1/properties/address");
    });

    it("looks up by coordinates", async () => {
      mockApiSuccess({ property_id: "TX-TRAVIS-001" });

      const result = await propertyLookup({ lat: 30.26, lng: -97.74 });

      const url = vi.mocked(globalThis.fetch).mock.calls[0][0] as string;
      expect(url).toContain("/v1/properties/coordinates");
    });

    it("returns error on API failure", async () => {
      mockApiError(404, "Not found");

      const result = await propertyLookup({
        parcel_id: "INVALID",
      });
      expect(result.isError).toBe(true);
    });

    it("handles undefined args", async () => {
      const result = await propertyLookup(undefined);
      const text = JSON.parse(result.content[0].text);
      expect(text.error).toContain("Must provide");
    });
  });

  describe("propertySearch", () => {
    it("posts search criteria", async () => {
      mockApiSuccess({ results: [], total: 0, has_more: false });

      const result = await propertySearch({ state: "TX", city: "Austin" });
      const text = JSON.parse(result.content[0].text);
      expect(text.total).toBe(0);
      expect(text.results).toEqual([]);
    });

    it("returns error on API failure", async () => {
      mockApiError(500, "Server error");

      const result = await propertySearch({ state: "TX" });
      expect(result.isError).toBe(true);
    });
  });

  describe("getComparables", () => {
    it("returns error when no identifier provided", async () => {
      const result = await getComparables({});
      const text = JSON.parse(result.content[0].text);
      expect(text.error).toContain("Must provide");
    });

    it("fetches comps by property_id", async () => {
      const comps = { comparables: [], subject: {} };
      mockApiSuccess(comps);

      const result = await getComparables({
        property_id: "TX-TRAVIS-001",
        radius_miles: 2,
      });
      expect(result.isError).toBeUndefined();
    });

    it("looks up property first when given address", async () => {
      vi.mocked(globalThis.fetch)
        .mockResolvedValueOnce({
          ok: true,
          json: () =>
            Promise.resolve({ property_id: "TX-TRAVIS-001" }),
        } as Response)
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ comparables: [] }),
        } as Response);

      const result = await getComparables({
        address: "123 Main St",
      });
      expect(globalThis.fetch).toHaveBeenCalledTimes(2);
    });
  });

  describe("getMarketTrends", () => {
    it("fetches trends with params", async () => {
      mockApiSuccess({ median_price: 450000, trend: "up" });

      const result = await getMarketTrends({
        state: "TX",
        zip: "78701",
        period: "12m",
      });
      const text = JSON.parse(result.content[0].text);
      expect(text.median_price).toBe(450000);
    });
  });

  describe("checkZoning", () => {
    it("returns error when no identifier provided", async () => {
      const result = await checkZoning({ proposed_use: "duplex" });
      const text = JSON.parse(result.content[0].text);
      expect(text.error).toContain("Must provide");
    });

    it("checks zoning by property_id", async () => {
      mockApiSuccess({
        property_id: "TX-TRAVIS-001",
        address: { formatted: "123 Main St" },
        zoning: {
          zone_code: "SF-3",
          permitted_uses: ["single_family"],
          conditional_uses: ["duplex"],
          setbacks: { front: 25, rear: 10, side: 5 },
          max_height: 35,
          max_far: 0.4,
        },
      });

      const result = await checkZoning({
        property_id: "TX-TRAVIS-001",
        proposed_use: "single_family",
      });
      const text = JSON.parse(result.content[0].text);
      expect(text.permitted).toBe(true);
      expect(text.permit_type).toBe("by_right");
    });

    it("detects conditional use", async () => {
      mockApiSuccess({
        property_id: "TX-TRAVIS-001",
        address: { formatted: "123 Main St" },
        zoning: {
          zone_code: "SF-3",
          permitted_uses: ["single_family"],
          conditional_uses: ["duplex"],
          setbacks: { front: 25, rear: 10, side: 5 },
          max_height: 35,
          max_far: 0.4,
        },
      });

      const result = await checkZoning({
        property_id: "TX-TRAVIS-001",
        proposed_use: "duplex",
      });
      const text = JSON.parse(result.content[0].text);
      expect(text.permitted).toBe(true);
      expect(text.permit_type).toBe("conditional");
    });

    it("detects prohibited use", async () => {
      mockApiSuccess({
        property_id: "TX-TRAVIS-001",
        address: { formatted: "123 Main St" },
        zoning: {
          zone_code: "SF-3",
          permitted_uses: ["single_family"],
          conditional_uses: [],
          setbacks: { front: 25, rear: 10, side: 5 },
          max_height: 35,
          max_far: 0.4,
        },
      });

      const result = await checkZoning({
        property_id: "TX-TRAVIS-001",
        proposed_use: "commercial",
      });
      const text = JSON.parse(result.content[0].text);
      expect(text.permitted).toBe(false);
      expect(text.permit_type).toBe("prohibited");
    });
  });

  describe("getPermits", () => {
    it("returns error when no identifier provided", async () => {
      const result = await getPermits({});
      const text = JSON.parse(result.content[0].text);
      expect(text.error).toContain("Must provide");
    });

    it("fetches and filters permits", async () => {
      mockApiSuccess({
        property_id: "TX-TRAVIS-001",
        permits: [
          {
            permit_number: "P001",
            type: "building",
            description: "New garage",
            status: "issued",
            issue_date: "2024-01-15",
            valuation: 50000,
            contractor: "ABC",
          },
          {
            permit_number: "P002",
            type: "electrical",
            description: "Panel upgrade",
            status: "finaled",
            issue_date: "2023-06-01",
            valuation: 5000,
            contractor: "XYZ",
          },
        ],
      });

      const result = await getPermits({
        property_id: "TX-TRAVIS-001",
        status: ["issued"],
      });
      const text = JSON.parse(result.content[0].text);
      expect(text.permit_count).toBe(1);
      expect(text.permits[0].permit_number).toBe("P001");
    });

    it("filters permits by type", async () => {
      mockApiSuccess({
        property_id: "TX-TRAVIS-001",
        permits: [
          {
            permit_number: "P001",
            type: "building",
            description: "Garage",
            status: "issued",
            issue_date: "2024-01-15",
            valuation: 50000,
            contractor: "ABC",
          },
          {
            permit_number: "P002",
            type: "electrical",
            description: "Panel",
            status: "issued",
            issue_date: "2024-02-01",
            valuation: 5000,
            contractor: "XYZ",
          },
        ],
      });

      const result = await getPermits({
        property_id: "TX-TRAVIS-001",
        permit_type: ["electrical"],
      });
      const text = JSON.parse(result.content[0].text);
      expect(text.permit_count).toBe(1);
      expect(text.permits[0].type).toBe("electrical");
    });

    it("filters permits by date", async () => {
      mockApiSuccess({
        property_id: "TX-TRAVIS-001",
        permits: [
          {
            permit_number: "P001",
            type: "building",
            description: "Garage",
            status: "issued",
            issue_date: "2024-06-01",
            valuation: 50000,
            contractor: "ABC",
          },
          {
            permit_number: "P002",
            type: "building",
            description: "Old work",
            status: "finaled",
            issue_date: "2020-01-01",
            valuation: 10000,
            contractor: "XYZ",
          },
        ],
      });

      const result = await getPermits({
        property_id: "TX-TRAVIS-001",
        since_date: "2024-01-01",
      });
      const text = JSON.parse(result.content[0].text);
      expect(text.permit_count).toBe(1);
    });
  });

  describe("getOwnerPortfolio", () => {
    it("fetches owner portfolio", async () => {
      mockApiSuccess({
        owner: "John Doe",
        property_count: 3,
        properties: [],
        related_entities: [],
      });

      const result = await getOwnerPortfolio({
        owner_name: "John Doe",
        state: "TX",
      });
      const text = JSON.parse(result.content[0].text);
      expect(text.owner).toBe("John Doe");
    });
  });

  describe("estimateValue", () => {
    it("returns error when no identifier provided", async () => {
      const result = await estimateValue({});
      const text = JSON.parse(result.content[0].text);
      expect(text.error).toContain("Must provide");
    });

    it("fetches valuation by property_id", async () => {
      mockApiSuccess({
        estimated_value: 550000,
        confidence: 0.85,
      });

      const result = await estimateValue({
        property_id: "TX-TRAVIS-001",
      });
      const text = JSON.parse(result.content[0].text);
      expect(text.estimated_value).toBe(550000);
    });
  });

  describe("checkDevelopmentFeasibility", () => {
    it("returns error when no property_id", async () => {
      const result = await checkDevelopmentFeasibility({});
      const text = JSON.parse(result.content[0].text);
      expect(text.error).toContain("property_id is required");
    });

    it("calculates buildable area", async () => {
      mockApiSuccess({
        property_id: "TX-TRAVIS-001",
        address: { formatted: "123 Main St" },
        lot: { sqft: 10000, acres: 0.23 },
        zoning: {
          zone_code: "SF-3",
          zone_description: "Single Family",
          permitted_uses: ["single_family"],
          conditional_uses: ["duplex"],
          max_far: 0.4,
          max_height: 35,
          max_lot_coverage: 0.45,
          setbacks: { front: 25, rear: 10, side: 5 },
        },
      });

      const result = await checkDevelopmentFeasibility({
        property_id: "TX-TRAVIS-001",
        proposed_use: "single_family",
      });
      const text = JSON.parse(result.content[0].text);
      expect(text.buildable.max_building_sqft).toBe(4000); // 10000 * 0.4
      expect(text.buildable.max_footprint_sqft).toBe(4500); // 10000 * 0.45
      expect(text.proposed_use_analysis.permitted).toBe(true);
      expect(text.proposed_use_analysis.permit_type).toBe("by_right");
    });
  });
});
