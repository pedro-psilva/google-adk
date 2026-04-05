#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend" / "src"))

from profile_backend.application.services.report_pipeline import ReportPipelineService
from profile_report_automation.bundle import save_json
from profile_report_automation.vertex_drafting import build_template_fallback, generate_draft_with_vertex


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare or execute the Vertex AI drafting step.")
    parser.add_argument("bundle_path", help="Path to the normalized bundle JSON")
    parser.add_argument(
        "--mode",
        choices=["preview", "template", "live"],
        default="preview",
        help="preview writes the request, template creates a local fallback, live calls Vertex AI.",
    )
    parser.add_argument("--output", help="Optional output JSON path")
    args = parser.parse_args()

    service = ReportPipelineService()
    bundle = service.load_bundle(args.bundle_path)
    coverage = service.analyze_coverage(args.bundle_path)

    if args.mode == "live":
        payload = generate_draft_with_vertex(bundle, coverage)
    elif args.mode == "template":
        payload = build_template_fallback(bundle, coverage)
    else:
        payload = service.preview_draft(args.bundle_path)

    if args.output:
        save_json(args.output, payload)
        print(f"Wrote {args.mode} payload to {args.output}")
        return

    print(payload)


if __name__ == "__main__":
    main()
