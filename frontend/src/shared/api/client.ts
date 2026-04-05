import type {
  HealthResponse,
  OAuthStartResponse,
  OAuthStatusResponse,
  PipelineResponse,
  PublishResponse,
  StudioFormState,
} from "../types/api";

class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly payload: unknown,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

function joinUrl(baseUrl: string, path: string) {
  const normalized = baseUrl.trim().replace(/\/+$/, "");
  return normalized ? `${normalized}${path}` : path;
}

async function request<T>(path: string, init?: RequestInit, baseUrl = ""): Promise<T> {
  const response = await fetch(joinUrl(baseUrl, path), {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });

  const contentType = response.headers.get("content-type") ?? "";
  const payload = contentType.includes("application/json") ? await response.json() : await response.text();

  if (!response.ok) {
    const message =
      typeof payload === "object" && payload && "detail" in payload
        ? String((payload as { detail: string }).detail)
        : typeof payload === "string"
          ? payload
          : "A requisição ao backend falhou.";
    throw new ApiError(message, response.status, payload);
  }

  return payload as T;
}

export function getHealth(baseUrl: string) {
  return request<HealthResponse>("/healthz", undefined, baseUrl);
}

export function getOAuthStatus(baseUrl: string, analystId: string) {
  const params = new URLSearchParams({ analyst_id: analystId });
  return request<OAuthStatusResponse>(`/api/v1/auth/google/status?${params.toString()}`, undefined, baseUrl);
}

export function startOAuth(baseUrl: string, analystId: string) {
  const params = new URLSearchParams({ analyst_id: analystId });
  return request<OAuthStartResponse>(`/api/v1/auth/google/start?${params.toString()}`, undefined, baseUrl);
}

export function runPipeline(baseUrl: string, form: StudioFormState) {
  return request<PipelineResponse>(
    "/api/v1/pipeline/run",
    {
      method: "POST",
      body: JSON.stringify({
        bundle_input: form.bundleInput,
        output_dir: form.outputDir,
        draft_mode: form.draftMode,
      }),
    },
    baseUrl,
  );
}

export function publishWorkspace(baseUrl: string, form: StudioFormState) {
  return request<PublishResponse>(
    "/api/v1/workspace/publish",
    {
      method: "POST",
      body: JSON.stringify({
        analyst_id: form.analystId,
        bundle_input: form.bundleInput,
        output_dir: form.outputDir,
        draft_mode: form.draftMode,
        publish_document: form.publishDocument,
        publish_spreadsheet: form.publishSpreadsheet,
      }),
    },
    baseUrl,
  );
}
