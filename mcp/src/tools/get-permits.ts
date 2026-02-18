import { apiCall } from "../client/api.js";

interface GetPermitsArgs {
  property_id?: string;
  address?: string;
  status?: string[];
  permit_type?: string[];
  since_date?: string;
}

export async function getPermits(
  args: Record<string, unknown> | undefined,
) {
  const a = (args ?? {}) as GetPermitsArgs;
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
            text: JSON.stringify({ error: "Property not found" }),
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
    const property = await apiCall<{
      property_id: string;
      permits: Array<{
        permit_number: string;
        type: string;
        description: string;
        status: string;
        issue_date: string;
        valuation: number;
        contractor: string;
      }>;
    }>(`/v1/properties/${propertyId}`, {
      params: { detail: "extended" },
    });

    let permits = property.permits || [];

    if (a.status && a.status.length > 0) {
      permits = permits.filter((p) =>
        a.status!.some((s) =>
          p.status.toLowerCase().includes(s.toLowerCase()),
        ),
      );
    }

    if (a.permit_type && a.permit_type.length > 0) {
      permits = permits.filter((p) =>
        a.permit_type!.some((t) =>
          p.type.toLowerCase().includes(t.toLowerCase()),
        ),
      );
    }

    if (a.since_date) {
      const sinceDate = new Date(a.since_date);
      permits = permits.filter(
        (p) => new Date(p.issue_date) >= sinceDate,
      );
    }

    return {
      content: [
        {
          type: "text" as const,
          text: JSON.stringify(
            {
              property_id: propertyId,
              permit_count: permits.length,
              permits,
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
