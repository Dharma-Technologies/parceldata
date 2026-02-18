import { apiCall } from "../client/api.js";

interface PropertyLookupArgs {
  address?: string;
  parcel_id?: string;
  lat?: number;
  lng?: number;
  include?: string[];
  detail?: "micro" | "standard" | "extended" | "full";
}

export async function propertyLookup(
  args: Record<string, unknown> | undefined,
) {
  const a = (args ?? {}) as PropertyLookupArgs;

  let endpoint: string;
  const params: Record<string, string | number | undefined> = {};

  if (a.parcel_id) {
    endpoint = `/v1/properties/${a.parcel_id}`;
  } else if (a.address) {
    endpoint = "/v1/properties/address";
    const parts = a.address.split(",").map((p) => p.trim());
    params.street = parts[0];
    if (parts.length >= 2) {
      params.city = parts[1];
    }
    if (parts.length >= 3) {
      params.state = parts[2].split(" ")[0];
    }
  } else if (a.lat !== undefined && a.lng !== undefined) {
    endpoint = "/v1/properties/coordinates";
    params.lat = a.lat;
    params.lng = a.lng;
  } else {
    return {
      content: [
        {
          type: "text" as const,
          text: JSON.stringify({
            error:
              "Must provide address, parcel_id, or lat/lng coordinates",
          }),
        },
      ],
    };
  }

  if (a.detail) {
    params.detail = a.detail;
  }

  try {
    const property = await apiCall<unknown>(endpoint, { params });

    return {
      content: [
        {
          type: "text" as const,
          text: JSON.stringify(property, null, 2),
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
