import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { apiCall, getConfig } from "../src/client/api.js";

describe("API Client", () => {
  const originalFetch = globalThis.fetch;

  beforeEach(() => {
    globalThis.fetch = vi.fn();
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
  });

  describe("getConfig", () => {
    it("returns default config", () => {
      const config = getConfig();
      expect(config.baseUrl).toBe("https://api.parceldata.ai");
      expect(config.apiKey).toBe("");
    });
  });

  describe("apiCall", () => {
    it("makes GET requests by default", async () => {
      const mockResponse = { property_id: "TX-TRAVIS-001" };
      vi.mocked(globalThis.fetch).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      } as Response);

      const result = await apiCall<typeof mockResponse>(
        "/v1/properties/TX-TRAVIS-001",
      );

      expect(result).toEqual(mockResponse);
      expect(globalThis.fetch).toHaveBeenCalledWith(
        "https://api.parceldata.ai/v1/properties/TX-TRAVIS-001",
        expect.objectContaining({ method: "GET" }),
      );
    });

    it("includes authorization header", async () => {
      vi.mocked(globalThis.fetch).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({}),
      } as Response);

      await apiCall("/v1/test");

      const call = vi.mocked(globalThis.fetch).mock.calls[0];
      const options = call[1] as RequestInit;
      const headers = options.headers as Record<string, string>;
      expect(headers["Authorization"]).toMatch(/^Bearer /);
      expect(headers["Content-Type"]).toBe("application/json");
    });

    it("appends query params for GET requests", async () => {
      vi.mocked(globalThis.fetch).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({}),
      } as Response);

      await apiCall("/v1/properties/address", {
        params: { street: "123 Main St", city: "Austin" },
      });

      const url = vi.mocked(globalThis.fetch).mock.calls[0][0] as string;
      expect(url).toContain("street=123+Main+St");
      expect(url).toContain("city=Austin");
    });

    it("skips undefined params", async () => {
      vi.mocked(globalThis.fetch).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({}),
      } as Response);

      await apiCall("/v1/test", {
        params: { a: "1", b: undefined },
      });

      const url = vi.mocked(globalThis.fetch).mock.calls[0][0] as string;
      expect(url).toContain("a=1");
      expect(url).not.toContain("b=");
    });

    it("makes POST requests with body", async () => {
      vi.mocked(globalThis.fetch).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ results: [] }),
      } as Response);

      await apiCall("/v1/properties/search", {
        method: "POST",
        body: { state: "TX", city: "Austin" },
      });

      const call = vi.mocked(globalThis.fetch).mock.calls[0];
      const options = call[1] as RequestInit;
      expect(options.method).toBe("POST");
      expect(options.body).toBe(
        JSON.stringify({ state: "TX", city: "Austin" }),
      );
    });

    it("throws on non-ok response", async () => {
      vi.mocked(globalThis.fetch).mockResolvedValue({
        ok: false,
        statusText: "Not Found",
        json: () => Promise.resolve({ message: "Property not found" }),
      } as Response);

      await expect(
        apiCall("/v1/properties/INVALID"),
      ).rejects.toThrow("API error: Property not found");
    });

    it("handles json parse error on failed response", async () => {
      vi.mocked(globalThis.fetch).mockResolvedValue({
        ok: false,
        statusText: "Internal Server Error",
        json: () => Promise.reject(new Error("parse error")),
      } as Response);

      await expect(apiCall("/v1/test")).rejects.toThrow(
        "API error: Unknown error",
      );
    });
  });
});
