from __future__ import annotations

from pathlib import Path

from profile_backend.application.ports import (
    BundleGateway,
    CoverageGateway,
    DraftingGateway,
    JsonStorageGateway,
)
from profile_backend.domain.models import PipelineArtifacts, PipelineRequest, PipelineResult
from profile_report_automation.report_exports import export_local_reports
from profile_report_automation.workbook_exports import export_filled_workbook


def run_pipeline(
    request: PipelineRequest,
    *,
    bundle_gateway: BundleGateway,
    coverage_gateway: CoverageGateway,
    drafting_gateway: DraftingGateway,
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

    workbook_report_path = export_filled_workbook(output_dir, resolved_bundle.bundle, coverage, draft)
    local_reports = export_local_reports(
        output_dir,
        resolved_bundle.bundle,
        coverage,
        draft,
        workbook_path=workbook_report_path,
    )

    result = PipelineResult(
        status=coverage.get("summary", {}).get("status", "unknown"),
        bundle_path=str(resolved_bundle.bundle_path.resolve()),
        output_dir=str(output_dir.resolve()),
        artifacts=PipelineArtifacts(
            bundle_path=str(resolved_bundle.bundle_path.resolve()),
            coverage_report=str(coverage_path.resolve()),
            vertex_request_preview=str(preview_path.resolve()),
            draft_output=str(draft_path.resolve()),
            local_report_xlsx=str(Path(workbook_report_path).resolve()),
            local_report_docx=local_reports.get("docx"),
            local_report_pdf=local_reports.get("pdf"),
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
            "local_report_xlsx": result.artifacts.local_report_xlsx,
            "local_report_docx": result.artifacts.local_report_docx,
            "local_report_pdf": result.artifacts.local_report_pdf,
            "live_draft": result.artifacts.live_draft,
        },
        "used_live_vertex": result.used_live_vertex,
        "notes": result.notes,
    }
