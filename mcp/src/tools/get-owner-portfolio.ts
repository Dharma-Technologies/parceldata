import { apiCall } from "../client/api.js";

interface GetOwnerPortfolioArgs {
  owner_name?: string;
  state?: string;
  include_related_entities?: boolean;
}

export async function getOwnerPortfolio(
  args: Record<string, unknown> | undefined,
) {
  const a = (args ?? {}) as GetOwnerPortfolioArgs;

  try {
    const response = await apiCall<{
      owner: string;
      property_count: number;
      properties: unknown[];
      related_entities: string[];
    }>("/v1/analytics/owner-portfolio", {
      params: {
        owner_name: a.owner_name,
        state: a.state,
        include_related: a.include_related_entities ? "true" : "false",
      },
    });

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
