from __future__ import annotations

from typing import Any

from profile_report_automation.google_outputs import build_google_doc_package, build_google_sheets_package


class ProductionWorkspacePackageGateway:
    def build_docs_package(
        self, bundle: dict[str, Any], coverage: dict[str, Any], draft: dict[str, Any]
    ) -> dict[str, Any]:
        return build_google_doc_package(bundle, coverage, draft)

    def build_sheets_package(
        self, bundle: dict[str, Any], coverage: dict[str, Any], draft: dict[str, Any]
    ) -> dict[str, Any]:
        return build_google_sheets_package(bundle, coverage, draft)
