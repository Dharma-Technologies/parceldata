import { apiCall } from "../client/api.js";

interface GetComparablesArgs {
  property_id?: string;
  address?: string;
  radius_miles?: number;
  months?: number;
  limit?: number;
}

export async function getComparables(
  args: Record<string, unknown> | undefined,
) {
  const a = (args ?? {}) as GetComparablesArgs;
  const params: Record<string, string | number | undefined> = {};

  if (a.property_id) {
    params.property_id = a.property_id;
  } else if (a.address) {
    try {
      const lookup = await apiCall<{ property_id: string }>(
        "/v1/properties/address",
        { params: { street: a.address } },
      );
      params.property_id = lookup.property_id;
    } catch {
      return {
        content: [
          {
            type: "text" as const,
            text: JSON.stringify({
              error: "Property not found at provided address",
            }),
          },
        ],
        isError: true,
      };
    }
  } else {
    return {
      content: [
        {
          type: "text" as const,
          text: JSON.stringify({
            error: "Must provide property_id or address",
          }),
        },
      ],
    };
  }

  if (a.radius_miles) params.radius_miles = a.radius_miles;
  if (a.months) params.months = a.months;
  if (a.limit) params.limit = a.limit;

  try {
    const response = await apiCall<unknown>(
      "/v1/analytics/comparables",
      { params },
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
