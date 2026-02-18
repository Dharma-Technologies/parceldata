import { apiCall } from "../client/api.js";

export async function propertySearch(
  args: Record<string, unknown> | undefined,
) {
  try {
    const response = await apiCall<{
      results: unknown[];
      total: number;
      has_more: boolean;
    }>("/v1/properties/search", {
      method: "POST",
      body: (args ?? {}) as Record<string, unknown>,
    });

    return {
      content: [
        {
          type: "text" as const,
          text: JSON.stringify(
            {
              total: response.total,
              returned: response.results.length,
              has_more: response.has_more,
              results: response.results,
            },
            null,
            2,
          ),
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
