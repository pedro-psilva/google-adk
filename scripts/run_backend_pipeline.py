#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend" / "src"))

from profile_backend.domain.models import PipelineRequest
from profile_backend.interfaces.adk.agent import adk_pipeline_runner


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the production-oriented ADK pipeline.")
    parser.add_argument("bundle_input", help="Path to a normalized bundle JSON or an intake folder")
    parser.add_argument("--output-dir", default="production-run", help="Where to write generated artifacts")
    parser.add_argument(
        "--draft-mode",
        choices=["preview", "live"],
        default="preview",
        help="preview generates schema/request artifacts; live calls Vertex AI.",
    )
    args = parser.parse_args()

    result = adk_pipeline_runner.run(
        PipelineRequest(bundle_input=args.bundle_input, output_dir=args.output_dir, draft_mode=args.draft_mode)
    )
    print(result)


if __name__ == "__main__":
    main()
