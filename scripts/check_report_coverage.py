#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend" / "src"))

from profile_backend.interfaces.adk.agent import adk_analysis_runner
from profile_report_automation.bundle import save_json


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze signal coverage inside a normalized report bundle.")
    parser.add_argument("bundle_path", help="Path to the normalized bundle JSON")
    parser.add_argument("--output", help="Optional output path for the coverage report JSON")
    args = parser.parse_args()

    coverage = adk_analysis_runner.analyze_coverage(args.bundle_path)
    if args.output:
        save_json(args.output, coverage)
        print(f"Wrote coverage report to {args.output}")
        return

    print(coverage)


if __name__ == "__main__":
    main()
