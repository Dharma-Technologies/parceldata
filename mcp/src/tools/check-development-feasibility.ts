import { apiCall } from "../client/api.js";

interface CheckDevelopmentFeasibilityArgs {
  property_id?: string;
  proposed_use?: string;
}

export async function checkDevelopmentFeasibility(
  args: Record<string, unknown> | undefined,
) {
  const a = (args ?? {}) as CheckDevelopmentFeasibilityArgs;

  if (!a.property_id) {
    return {
      content: [
        {
          type: "text" as const,
          text: JSON.stringify({
            error: "property_id is required",
          }),
        },
      ],
    };
  }

  try {
    const property = await apiCall<{
      property_id: string;
      address: { formatted: string };
      lot: { sqft: number; acres: number };
      zoning: {
        zone_code: string;
        zone_description: string;
        permitted_uses: string[];
        conditional_uses: string[];
        max_far: number;
        max_height: number;
        max_lot_coverage: number;
        setbacks: { front: number; rear: number; side: number };
      };
    }>(`/v1/properties/${a.property_id}`, {
      params: { detail: "extended" },
    });

    const zoning = property.zoning;
    const lotSqft = property.lot?.sqft || 0;

    const maxBuildableSqft = lotSqft * (zoning.max_far || 0);
    const maxFootprint = lotSqft * (zoning.max_lot_coverage || 0);

    let usePermitted = false;
    let useType: "by_right" | "conditional" | "prohibited" =
      "prohibited";

    if (a.proposed_use) {
      const use = a.proposed_use.toLowerCase();
      if (
        zoning.permitted_uses?.some((u) =>
          u.toLowerCase().includes(use),
        )
      ) {
        usePermitted = true;
        useType = "by_right";
      } else if (
        zoning.conditional_uses?.some((u) =>
          u.toLowerCase().includes(use),
        )
      ) {
        usePermitted = true;
        useType = "conditional";
      }
    }

    return {
      content: [
        {
          type: "text" as const,
          text: JSON.stringify(
            {
              property_id: a.property_id,
              address: property.address?.formatted,
              lot_sqft: lotSqft,
              zoning: {
                zone_code: zoning.zone_code,
                zone_description: zoning.zone_description,
                max_far: zoning.max_far,
                max_height_ft: zoning.max_height,
                max_lot_coverage: zoning.max_lot_coverage,
                setbacks: zoning.setbacks,
              },
              buildable: {
                max_building_sqft: maxBuildableSqft,
                max_footprint_sqft: maxFootprint,
                max_height_ft: zoning.max_height,
                permitted_uses: zoning.permitted_uses,
                conditional_uses: zoning.conditional_uses,
              },
              ...(a.proposed_use
                ? {
                    proposed_use_analysis: {
                      use: a.proposed_use,
                      permitted: usePermitted,
                      permit_type: useType,
                    },
                  }
                : {}),
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
