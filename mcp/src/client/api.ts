interface ApiConfig {
  baseUrl: string;
  apiKey: string;
}

const config: ApiConfig = {
  baseUrl: process.env.PARCELDATA_API_URL || "https://api.parceldata.ai",
  apiKey: process.env.PARCELDATA_API_KEY || "",
};

export function getConfig(): ApiConfig {
  return { ...config };
}

export async function apiCall<T>(
  endpoint: string,
  options: {
    method?: "GET" | "POST";
    params?: Record<string, string | number | boolean | undefined>;
    body?: Record<string, unknown>;
  } = {},
): Promise<T> {
  const { method = "GET", params, body } = options;

  let url = `${config.baseUrl}${endpoint}`;

  if (params) {
    const searchParams = new URLSearchParams();
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined) {
        searchParams.set(key, String(value));
      }
    }
    const queryString = searchParams.toString();
    if (queryString) {
      url += `?${queryString}`;
    }
  }

  const headers: Record<string, string> = {
    Authorization: `Bearer ${config.apiKey}`,
    "Content-Type": "application/json",
  };

  const response = await fetch(url, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  if (!response.ok) {
    const error = (await response.json().catch(() => ({
      message: "Unknown error",
    }))) as { message?: string };
    throw new Error(
      `API error: ${error.message || response.statusText}`,
    );
  }

  return response.json() as Promise<T>;
}
