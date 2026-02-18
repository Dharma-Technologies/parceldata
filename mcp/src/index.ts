import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  ListToolsRequestSchema,
  CallToolRequestSchema,
  ErrorCode,
  McpError,
} from "@modelcontextprotocol/sdk/types.js";
import { propertyLookup } from "./tools/property-lookup.js";
import { propertySearch } from "./tools/property-search.js";
import { getComparables } from "./tools/get-comparables.js";
import { getMarketTrends } from "./tools/get-market-trends.js";
import { checkZoning } from "./tools/check-zoning.js";
import { getPermits } from "./tools/get-permits.js";
import { getOwnerPortfolio } from "./tools/get-owner-portfolio.js";
import { estimateValue } from "./tools/estimate-value.js";
import { checkDevelopmentFeasibility } from "./tools/check-development-feasibility.js";
import { TOOLS } from "./tools/definitions.js";

type ToolHandler = (
  args: Record<string, unknown> | undefined,
) => Promise<{
  content: Array<{ type: "text"; text: string }>;
  isError?: boolean;
}>;

const TOOL_HANDLERS: Record<string, ToolHandler> = {
  property_lookup: propertyLookup,
  property_search: propertySearch,
  get_comparables: getComparables,
  get_market_trends: getMarketTrends,
  check_zoning: checkZoning,
  get_permits: getPermits,
  get_owner_portfolio: getOwnerPortfolio,
  estimate_value: estimateValue,
  check_development_feasibility: checkDevelopmentFeasibility,
};

export function createServer(): Server {
  const server = new Server(
    {
      name: "parceldata",
      version: "0.1.0",
    },
    {
      capabilities: {
        tools: {},
      },
    },
  );

  server.setRequestHandler(ListToolsRequestSchema, async () => {
    return { tools: TOOLS };
  });

  server.setRequestHandler(
    CallToolRequestSchema,
    async (request) => {
      const { name, arguments: args } = request.params;

      const handler = TOOL_HANDLERS[name];
      if (!handler) {
        throw new McpError(
          ErrorCode.MethodNotFound,
          `Unknown tool: ${name}`,
        );
      }

      try {
        return await handler(args);
      } catch (error) {
        if (error instanceof McpError) {
          throw error;
        }
        throw new McpError(
          ErrorCode.InternalError,
          `Tool error: ${error instanceof Error ? error.message : "Unknown error"}`,
        );
      }
    },
  );

  return server;
}

async function main() {
  const server = createServer();
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("ParcelData MCP server running on stdio");
}

main().catch(console.error);
