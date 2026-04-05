export type DraftMode = "preview" | "live";

export interface HealthResponse {
  status: string;
  service: string;
}

export interface OAuthStartResponse {
  analyst_id: string;
  authorization_url: string;
  state: string;
}

export interface OAuthStatusResponse {
  analyst_id: string;
  connected: boolean;
  email?: string | null;
  scopes?: string[];
  token_path?: string | null;
}

export interface PipelineArtifacts {
  bundle_path: string;
  coverage_report: string;
  vertex_request_preview: string;
  draft_output: string;
  google_docs_package: string;
  google_sheets_package: string;
  live_draft?: string | null;
}

export interface PipelineResponse {
  status: string;
  bundle_path: string;
  output_dir: string;
  used_live_vertex: boolean;
  artifacts: PipelineArtifacts;
  notes?: string[];
}

export interface PublishResponse {
  analyst_id: string;
  document_id?: string | null;
  document_url?: string | null;
  spreadsheet_id?: string | null;
  spreadsheet_url?: string | null;
  output_dir?: string | null;
}

export interface StudioFormState {
  apiBaseUrl: string;
  analystId: string;
  bundleInput: string;
  outputDir: string;
  draftMode: DraftMode;
  publishDocument: boolean;
  publishSpreadsheet: boolean;
}
