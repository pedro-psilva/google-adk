from __future__ import annotations

from typing import Any

from profile_report_automation.vertex_drafting import (
    build_template_fallback,
    generate_draft_with_vertex,
    prepare_vertex_request_preview,
)


class ProductionDraftingGateway:
    def build_preview(self, bundle: dict[str, Any], coverage: dict[str, Any]) -> dict[str, Any]:
        return prepare_vertex_request_preview(bundle, coverage)

    def build_template(self, bundle: dict[str, Any], coverage: dict[str, Any]) -> dict[str, Any]:
        return build_template_fallback(bundle, coverage)

    def build_live(self, bundle: dict[str, Any], coverage: dict[str, Any]) -> dict[str, Any]:
        return generate_draft_with_vertex(bundle, coverage)
