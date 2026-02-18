import { apiCall } from "../client/api.js";

interface GetMarketTrendsArgs {
  zip?: string;
  city?: string;
  county?: string;
  state?: string;
  property_type?: string;
  period?: "3m" | "6m" | "12m" | "24m" | "5y";
}

export async function getMarketTrends(
  args: Record<string, unknown> | undefined,
) {
  const a = (args ?? {}) as GetMarketTrendsArgs;

  try {
    const response = await apiCall<unknown>(
      "/v1/analytics/market-trends",
      {
        params: {
          zip: a.zip,
          city: a.city,
          county: a.county,
          state: a.state,
          property_type: a.property_type,
          period: a.period,
        },
      },
    );

    return {
      content: [
        {
          type: "text" as const,
          text: JSON.stringify(response, null, 2),
        },
      ],
    };
  } catch (error) {
    return {
      content: [
        {
          type: "text" as const,
          text: JSON.stringify({
            error:
              error instanceof Error ? error.message : "Unknown error",
          }),
        },
      ],
      isError: true,
    };
  }
}
