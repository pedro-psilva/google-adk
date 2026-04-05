#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend" / "src"))

from profile_backend.application.services.report_pipeline import ReportPipelineService
from profile_backend.domain.models import PipelineRequest


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the production-oriented backend pipeline.")
    parser.add_argument("bundle_input", help="Path to a normalized bundle JSON or an intake folder")
    parser.add_argument("--output-dir", default="artifacts/production-run", help="Where to write generated artifacts")
    parser.add_argument(
        "--draft-mode",
        choices=["preview", "live"],
        default="preview",
        help="preview generates schema/request artifacts; live calls Vertex AI.",
    )
    args = parser.parse_args()

    result = ReportPipelineService().run(
        PipelineRequest(bundle_input=args.bundle_input, output_dir=args.output_dir, draft_mode=args.draft_mode)
    )
    print(
        {
            "status": result.status,
            "bundle_path": result.bundle_path,
            "output_dir": result.output_dir,
            "used_live_vertex": result.used_live_vertex,
            "artifacts": {
                "coverage_report": result.artifacts.coverage_report,
                "vertex_request_preview": result.artifacts.vertex_request_preview,
                "draft_output": result.artifacts.draft_output,
                "google_docs_package": result.artifacts.google_docs_package,
                "google_sheets_package": result.artifacts.google_sheets_package,
                "live_draft": result.artifacts.live_draft,
            },
        }
    )


if __name__ == "__main__":
    main()
