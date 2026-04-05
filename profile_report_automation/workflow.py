from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any

from .bundle import load_bundle, save_json
from .coverage import analyze_coverage
from .google_outputs import build_google_doc_package, build_google_sheets_package
from .vertex_drafting import (
    build_template_fallback,
    generate_draft_with_vertex,
    prepare_vertex_request_preview,
)


def run_local_mvp(
    bundle_input: str | Path,
    output_dir: str | Path,
    *,
    vertex_mode: str = "preview",
) -> dict[str, Any]:
    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)

    bundle, bundle_path = _load_or_extract_bundle(bundle_input, output_root)

    coverage = analyze_coverage(bundle)
    coverage_path = save_json(output_root / "coverage-report.json", coverage)

    vertex_preview = prepare_vertex_request_preview(bundle, coverage)
    vertex_preview_path = save_json(output_root / "vertex-request-preview.json", vertex_preview)

    template_draft = build_template_fallback(bundle, coverage)
    template_draft_path = save_json(output_root / "draft-template.json", template_draft)

    live_draft = None
    live_draft_path = None
    if vertex_mode == "live":
        live_draft = generate_draft_with_vertex(bundle, coverage)
        live_draft_path = save_json(output_root / "draft-vertex.json", live_draft)

    selected_draft = live_draft or template_draft
    docs_package = build_google_doc_package(bundle, coverage, selected_draft)
    docs_package_path = save_json(output_root / "google-docs-package.json", docs_package)

    sheets_package = build_google_sheets_package(bundle, coverage, selected_draft)
    sheets_package_path = save_json(output_root / "google-sheets-package.json", sheets_package)

    summary = {
        "bundle_path": str(bundle_path.resolve()),
        "output_dir": str(output_root.resolve()),
        "artifacts": {
            "coverage_report": str(coverage_path.resolve()),
            "vertex_request_preview": str(vertex_preview_path.resolve()),
            "template_draft": str(template_draft_path.resolve()),
            "live_draft": str(live_draft_path.resolve()) if live_draft_path else None,
            "google_docs_package": str(docs_package_path.resolve()),
            "google_sheets_package": str(sheets_package_path.resolve()),
        },
        "used_live_vertex": bool(live_draft),
        "coverage_status": coverage.get("summary", {}).get("status"),
    }
    save_json(output_root / "run-summary.json", summary)
    return summary


def _load_or_extract_bundle(bundle_input: str | Path, output_root: Path) -> tuple[dict[str, Any], Path]:
    input_path = Path(bundle_input)
    if input_path.is_file():
        return load_bundle(input_path), input_path

    if input_path.is_dir():
        extractor_path = (
            Path(__file__).resolve().parent.parent
            / "skills"
            / "profile-report-automation"
            / "scripts"
            / "extract_assessment_bundle.py"
        )
        extracted_bundle_path = output_root / "normalized-bundle.json"
        subprocess.run(
            [
                sys.executable,
                str(extractor_path),
                str(input_path),
                "--output",
                str(extracted_bundle_path),
            ],
            check=True,
        )
        return load_bundle(extracted_bundle_path), extracted_bundle_path

    raise FileNotFoundError(f"Bundle input not found: {input_path}")
