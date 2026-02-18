import { apiCall } from "../client/api.js";

interface CheckZoningArgs {
  property_id?: string;
  address?: string;
  proposed_use?: string;
}

export async function checkZoning(
  args: Record<string, unknown> | undefined,
) {
  const a = (args ?? {}) as CheckZoningArgs;
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
    const property = await apiCall<{
      property_id: string;
      address: { formatted: string };
      zoning: {
        zone_code: string;
        permitted_uses: string[];
        conditional_uses: string[];
        setbacks: { front: number; rear: number; side: number };
        max_height: number;
        max_far: number;
      };
    }>(`/v1/properties/${propertyId}`, {
      params: { detail: "standard" },
    });

    const zoning = property.zoning;
    const use = (a.proposed_use ?? "").toLowerCase();

    let permitted = false;
    let permitType: "by_right" | "conditional" | "variance" | "prohibited" =
      "prohibited";

    if (
      zoning.permitted_uses?.some((u) =>
        u.toLowerCase().includes(use),
      )
    ) {
      permitted = true;
      permitType = "by_right";
    } else if (
      zoning.conditional_uses?.some((u) =>
        u.toLowerCase().includes(use),
      )
    ) {
      permitted = true;
      permitType = "conditional";
    }

    return {
      content: [
        {
          type: "text" as const,
          text: JSON.stringify(
            {
              property_id: property.property_id,
              address: property.address.formatted,
              current_zoning: zoning.zone_code,
              proposed_use: a.proposed_use,
              permitted,
              permit_type: permitType,
              requirements: {
                max_height_ft: zoning.max_height,
                setback_rear_ft: zoning.setbacks?.rear,
                setback_side_ft: zoning.setbacks?.side,
              },
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
