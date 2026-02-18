import { apiCall } from "../client/api.js";

interface EstimateValueArgs {
  property_id?: string;
  address?: string;
  adjustments?: {
    condition?: string;
    recent_renovations?: boolean;
    renovation_value?: number;
  };
}

export async function estimateValue(
  args: Record<string, unknown> | undefined,
) {
  const a = (args ?? {}) as EstimateValueArgs;
  let propertyId = a.property_id;

  if (!propertyId && a.address) {
    try {
      const lookup = await apiCall<{ property_id: string }>(
        "/v1/properties/address",
        { params: { street: a.address } },
      );
      propertyId = lookup.property_id;
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
  }

  if (!propertyId) {
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

  try {
    const response = await apiCall<unknown>(
      `/v1/analytics/valuation/${propertyId}`,
      {
        method: "POST",
        body: a.adjustments
          ? { adjustments: a.adjustments }
          : {},
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
