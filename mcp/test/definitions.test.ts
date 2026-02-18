import { describe, it, expect } from "vitest";
import { TOOLS } from "../src/tools/definitions.js";

describe("Tool Definitions", () => {
  it("exports exactly 9 tools", () => {
    expect(TOOLS).toHaveLength(9);
  });

  describe("property_lookup", () => {
    const tool = TOOLS.find((t) => t.name === "property_lookup")!;

    it("has correct name and description", () => {
      expect(tool.name).toBe("property_lookup");
      expect(tool.description).toContain("property data");
    });

    it("accepts address, parcel_id, lat, lng, include, detail", () => {
      const props = tool.inputSchema.properties!;
      expect(props).toHaveProperty("address");
      expect(props).toHaveProperty("parcel_id");
      expect(props).toHaveProperty("lat");
      expect(props).toHaveProperty("lng");
      expect(props).toHaveProperty("include");
      expect(props).toHaveProperty("detail");
    });

    it("has no required fields", () => {
      expect(tool.inputSchema.required).toBeUndefined();
    });
  });

  describe("property_search", () => {
    const tool = TOOLS.find((t) => t.name === "property_search")!;

    it("requires state", () => {
      expect(tool.inputSchema.required).toContain("state");
    });

    it("has search filter properties", () => {
      const props = tool.inputSchema.properties!;
      expect(props).toHaveProperty("city");
      expect(props).toHaveProperty("zip");
      expect(props).toHaveProperty("property_type");
      expect(props).toHaveProperty("bedrooms_min");
      expect(props).toHaveProperty("price_min");
      expect(props).toHaveProperty("price_max");
    });
  });

  describe("get_comparables", () => {
    const tool = TOOLS.find((t) => t.name === "get_comparables")!;

    it("accepts property_id, address, radius_miles, months, limit", () => {
      const props = tool.inputSchema.properties!;
      expect(props).toHaveProperty("property_id");
      expect(props).toHaveProperty("address");
      expect(props).toHaveProperty("radius_miles");
      expect(props).toHaveProperty("months");
      expect(props).toHaveProperty("limit");
    });
  });

  describe("get_market_trends", () => {
    const tool = TOOLS.find((t) => t.name === "get_market_trends")!;

    it("requires state", () => {
      expect(tool.inputSchema.required).toContain("state");
    });

    it("supports period enum", () => {
      const props = tool.inputSchema.properties!;
      const period = props.period as { enum: string[] };
      expect(period.enum).toEqual(["3m", "6m", "12m", "24m", "5y"]);
    });
  });

  describe("check_zoning", () => {
    const tool = TOOLS.find((t) => t.name === "check_zoning")!;

    it("requires proposed_use", () => {
      expect(tool.inputSchema.required).toContain("proposed_use");
    });
  });

  describe("get_permits", () => {
    const tool = TOOLS.find((t) => t.name === "get_permits")!;

    it("has status and permit_type filter arrays", () => {
      const props = tool.inputSchema.properties!;
      expect(props).toHaveProperty("status");
      expect(props).toHaveProperty("permit_type");
      expect(props).toHaveProperty("since_date");
    });
  });

  describe("get_owner_portfolio", () => {
    const tool = TOOLS.find((t) => t.name === "get_owner_portfolio")!;

    it("requires owner_name", () => {
      expect(tool.inputSchema.required).toContain("owner_name");
    });
  });

  describe("estimate_value", () => {
    const tool = TOOLS.find((t) => t.name === "estimate_value")!;

    it("accepts adjustments object", () => {
      const props = tool.inputSchema.properties!;
      expect(props).toHaveProperty("adjustments");
    });
  });

  describe("check_development_feasibility", () => {
    const tool = TOOLS.find(
      (t) => t.name === "check_development_feasibility",
    )!;

    it("requires property_id", () => {
      expect(tool.inputSchema.required).toContain("property_id");
    });

    it("accepts proposed_use", () => {
      const props = tool.inputSchema.properties!;
      expect(props).toHaveProperty("proposed_use");
    });
  });
});
