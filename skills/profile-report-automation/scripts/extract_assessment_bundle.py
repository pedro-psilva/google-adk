#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "backend" / "src"))

from profile_report_automation.extract_assessment_bundle import main


if __name__ == "__main__":
    main()
