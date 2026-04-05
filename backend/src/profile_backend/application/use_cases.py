from __future__ import annotations

from pathlib import Path

from profile_backend.application.ports import (
    BundleGateway,
    CoverageGateway,
    DraftingGateway,
    JsonStorageGateway,
    WorkspacePackageGateway,
)
from profile_backend.domain.models import PipelineArtifacts, PipelineRequest, PipelineResult


def run_pipeline(
    request: PipelineRequest,
    *,
    bundle_gateway: BundleGateway,
    coverage_gateway: CoverageGateway,
    drafting_gateway: DraftingGateway,
    workspace_gateway: WorkspacePackageGateway,
    storage_gateway: JsonStorageGateway,
) -> PipelineResult:
    output_dir = Path(request.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    resolved_bundle = bundle_gateway.resolve(request.bundle_input, output_dir)
    coverage = coverage_gateway.analyze(resolved_bundle.bundle)
    coverage_path = storage_gateway.save(output_dir / "coverage-report.json", coverage)

    preview = drafting_gateway.build_preview(resolved_bundle.bundle, coverage)
    preview_path = storage_gateway.save(output_dir / "vertex-request-preview.json", preview)

    if request.draft_mode == "live":
        draft = drafting_gateway.build_live(resolved_bundle.bundle, coverage)
        live_draft_path = storage_gateway.save(output_dir / "draft-vertex.json", draft)
        draft_path = live_draft_path
        used_live_vertex = True
    else:
        draft = drafting_gateway.build_template(resolved_bundle.bundle, coverage)
        draft_path = storage_gateway.save(output_dir / "draft-template.json", draft)
        live_draft_path = None
        used_live_vertex = False

    docs_package = workspace_gateway.build_docs_package(resolved_bundle.bundle, coverage, draft)
    docs_path = storage_gateway.save(output_dir / "google-docs-package.json", docs_package)

    sheets_package = workspace_gateway.build_sheets_package(resolved_bundle.bundle, coverage, draft)
    sheets_path = storage_gateway.save(output_dir / "google-sheets-package.json", sheets_package)

    result = PipelineResult(
        status=coverage.get("summary", {}).get("status", "unknown"),
        bundle_path=str(resolved_bundle.bundle_path.resolve()),
        output_dir=str(output_dir.resolve()),
        artifacts=PipelineArtifacts(
            bundle_path=str(resolved_bundle.bundle_path.resolve()),
            coverage_report=str(coverage_path.resolve()),
            vertex_request_preview=str(preview_path.resolve()),
            draft_output=str(draft_path.resolve()),
            google_docs_package=str(docs_path.resolve()),
            google_sheets_package=str(sheets_path.resolve()),
            live_draft=str(live_draft_path.resolve()) if live_draft_path else None,
        ),
        used_live_vertex=used_live_vertex,
        notes=coverage.get("notes", []),
    )
    storage_gateway.save(output_dir / "run-summary.json", _result_to_dict(result))
    return result


def _result_to_dict(result: PipelineResult) -> dict[str, object]:
    return {
        "status": result.status,
        "bundle_path": result.bundle_path,
        "output_dir": result.output_dir,
        "artifacts": {
            "bundle_path": result.artifacts.bundle_path,
            "coverage_report": result.artifacts.coverage_report,
            "vertex_request_preview": result.artifacts.vertex_request_preview,
            "draft_output": result.artifacts.draft_output,
            "google_docs_package": result.artifacts.google_docs_package,
            "google_sheets_package": result.artifacts.google_sheets_package,
            "live_draft": result.artifacts.live_draft,
        },
        "used_live_vertex": result.used_live_vertex,
        "notes": result.notes,
    }
