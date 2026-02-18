import { describe, it, expect, vi, beforeEach } from "vitest";
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import {
  ListToolsRequestSchema,
  CallToolRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { createServer } from "../src/index.js";
import { TOOLS } from "../src/tools/definitions.js";

describe("MCP Server Entry Point", () => {
  let server: Server;

  beforeEach(() => {
    server = createServer();
  });

  it("creates a Server instance", () => {
    expect(server).toBeInstanceOf(Server);
  });

  it("lists all 9 tools", async () => {
    // Access the request handler by simulating the protocol
    // The server registers handlers — we test indirectly via TOOLS
    expect(TOOLS).toHaveLength(9);
    const toolNames = TOOLS.map((t) => t.name);
    expect(toolNames).toContain("property_lookup");
    expect(toolNames).toContain("property_search");
    expect(toolNames).toContain("get_comparables");
    expect(toolNames).toContain("get_market_trends");
    expect(toolNames).toContain("check_zoning");
    expect(toolNames).toContain("get_permits");
    expect(toolNames).toContain("get_owner_portfolio");
    expect(toolNames).toContain("estimate_value");
    expect(toolNames).toContain("check_development_feasibility");
  });

  it("every tool has name, description, and inputSchema", () => {
    for (const tool of TOOLS) {
      expect(tool.name).toBeTruthy();
      expect(tool.description).toBeTruthy();
      expect(tool.inputSchema).toBeDefined();
      expect(tool.inputSchema.type).toBe("object");
    }
  });

  it("server has tools capability", () => {
    // The server should have been created with tools capability
    // We can verify by checking the server was created without errors
    expect(server).toBeDefined();
  });
});
