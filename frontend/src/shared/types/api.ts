export type DraftMode = "preview" | "live";
export type JsonCellValue = string | number | boolean | null;
export type AssessmentUploadSlotId = "neopi" | "profiler" | "anchors";
export type AssessmentUploadFiles = Record<AssessmentUploadSlotId, File | null>;

export interface HealthResponse {
  status: string;
  service: string;
}

export interface UploadedAssessmentFile {
  name: string;
  original_name: string;
  size_bytes: number;
  category?: string | null;
  label?: string | null;
}

export interface UploadedSourceResponse {
  upload_id: string;
  bundle_input: string;
  output_dir: string;
  storage_mode: "intake_dir" | "bundle_json";
  files: UploadedAssessmentFile[];
}

export interface PipelineArtifacts {
  bundle_path: string;
  coverage_report: string;
  vertex_request_preview: string;
  draft_output: string;
  local_report_xlsx?: string | null;
  local_report_docx?: string | null;
  local_report_pdf?: string | null;
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

export interface CoverageBucket {
  total: number;
  covered: number;
  missing: number;
  missing_ids: string[];
}

export interface CoverageSummary {
  required_overall: CoverageBucket;
  required_conclusion: CoverageBucket;
  recommended_overall: CoverageBucket;
  recommended_conclusion: CoverageBucket;
  status: string;
}

export interface CoverageMatch {
  covered: boolean;
  matched_patterns: string[];
}

export interface CoverageSignal {
  signal_id: string;
  signal_type: string;
  importance: string;
  name: string;
  source_section: string;
  metadata: Record<string, JsonCellValue | JsonCellValue[] | Record<string, unknown>>;
  coverage: {
    all_sections: CoverageMatch;
    conclusion: CoverageMatch;
    [key: string]: CoverageMatch;
  };
}

export interface NamedSectionCheck {
  expected: string[];
  mentioned: string[];
  missing: string[];
}

export interface CoverageResponse {
  person: Record<string, unknown>;
  summary: CoverageSummary;
  required_signals: CoverageSignal[];
  possible_medium_mentions: CoverageSignal[];
  named_section_checks: Record<string, NamedSectionCheck>;
  notes?: string[];
}

export interface DraftSectionResponse {
  key: string;
  title: string;
  paragraphs?: string[];
  bullets?: string[];
  mandatory_signal_ids?: string[];
}

export interface DraftResponse {
  report_title: string;
  language?: string;
  tone?: string;
  sections: DraftSectionResponse[];
  qa_notes?: string[];
}

export interface StudioFormState {
  apiBaseUrl: string;
  bundleInput: string;
  outputDir: string;
  draftMode: DraftMode;
}
