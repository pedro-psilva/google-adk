import type {
  AssessmentUploadFiles,
  CoverageResponse,
  DraftResponse,
  HealthResponse,
  PipelineRunInput,
  PipelineResponse,
  UploadedSourceResponse,
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

export function buildDownloadUrl(baseUrl: string, filePath: string) {
  const params = new URLSearchParams({ path: filePath });
  return joinUrl(baseUrl, `/api/v1/files/download?${params.toString()}`);
}

async function request<T>(path: string, init?: RequestInit, baseUrl = ""): Promise<T> {
  const headers = new Headers(init?.headers ?? {});
  if (!(init?.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  let response: Response;
  try {
    response = await fetch(joinUrl(baseUrl, path), {
      ...init,
      headers,
    });
  } catch (caughtError) {
    const message =
      caughtError instanceof Error && caughtError.message
        ? `Nao foi possivel conectar ao backend. Inicie a API local e tente novamente. Detalhe: ${caughtError.message}`
        : "Nao foi possivel conectar ao backend. Inicie a API local e tente novamente.";
    throw new ApiError(message, 0, null);
  }

  const contentType = response.headers.get("content-type") ?? "";
  const payload = contentType.includes("application/json") ? await response.json() : await response.text();

  if (!response.ok) {
    const message =
      typeof payload === "object" && payload && "detail" in payload
        ? String((payload as { detail: string }).detail)
        : typeof payload === "string"
          ? payload
          : "A requisicao ao backend falhou.";
    throw new ApiError(message, response.status, payload);
  }

  return payload as T;
}

export function getHealth(baseUrl: string) {
  return request<HealthResponse>("/healthz", undefined, baseUrl);
}

export function uploadAssessmentFiles(baseUrl: string, files: AssessmentUploadFiles, label?: string) {
  const formData = new FormData();
  if (files.neopi) {
    formData.append("neopi_file", files.neopi, files.neopi.name);
  }
  if (files.profiler) {
    formData.append("profiler_file", files.profiler, files.profiler.name);
  }
  if (files.anchors) {
    formData.append("anchors_file", files.anchors, files.anchors.name);
  }
  if (label?.trim()) {
    formData.append("label", label.trim());
  }

  return request<UploadedSourceResponse>(
    "/api/v1/intake/upload",
    {
      method: "POST",
      body: formData,
    },
    baseUrl,
  );
}

export function loadJsonArtifact<T>(baseUrl: string, bundlePath: string) {
  return request<T>(
    "/api/v1/bundles/load",
    {
      method: "POST",
      body: JSON.stringify({ bundle_path: bundlePath }),
    },
    baseUrl,
  );
}

export function runPipeline(baseUrl: string, input: PipelineRunInput) {
  return request<PipelineResponse>(
    "/api/v1/pipeline/run",
    {
      method: "POST",
      body: JSON.stringify({
        bundle_input: input.bundleInput,
        output_dir: input.outputDir,
        draft_mode: input.draftMode ?? "preview",
      }),
    },
    baseUrl,
  );
}

export type AutomationArtifactsPayload = {
  pipeline: PipelineResponse;
  coverage: CoverageResponse;
  draft: DraftResponse;
};
