from __future__ import annotations

from typing import Any

from profile_report_automation.coverage import analyze_coverage


class ProductionCoverageGateway:
    def analyze(self, bundle: dict[str, Any]) -> dict[str, Any]:
        return analyze_coverage(bundle)
