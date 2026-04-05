from __future__ import annotations

from profile_backend.application.use_cases import run_pipeline
from profile_backend.domain.models import PipelineRequest
from profile_backend.infrastructure.bundle_gateway import ProductionBundleGateway
from profile_backend.infrastructure.coverage_gateway import ProductionCoverageGateway
from profile_backend.infrastructure.drafting_gateway import ProductionDraftingGateway
from profile_backend.infrastructure.json_storage import JsonFileStorageGateway
from profile_backend.infrastructure.workspace_gateway import ProductionWorkspacePackageGateway


class ReportPipelineService:
    def __init__(self) -> None:
        self._bundle_gateway = ProductionBundleGateway()
        self._coverage_gateway = ProductionCoverageGateway()
        self._drafting_gateway = ProductionDraftingGateway()
        self._workspace_gateway = ProductionWorkspacePackageGateway()
        self._storage_gateway = JsonFileStorageGateway()

    def run(self, request: PipelineRequest):
        return run_pipeline(
            request,
            bundle_gateway=self._bundle_gateway,
            coverage_gateway=self._coverage_gateway,
            drafting_gateway=self._drafting_gateway,
            workspace_gateway=self._workspace_gateway,
            storage_gateway=self._storage_gateway,
        )

    def load_bundle(self, bundle_path: str):
        return self._storage_gateway.load(bundle_path)

    def analyze_coverage(self, bundle_path: str):
        return self._coverage_gateway.analyze(self._storage_gateway.load(bundle_path))

    def preview_draft(self, bundle_path: str):
        bundle = self._storage_gateway.load(bundle_path)
        coverage = self._coverage_gateway.analyze(bundle)
        return self._drafting_gateway.build_preview(bundle, coverage)

    def build_output_packages(self, bundle_path: str):
        bundle = self._storage_gateway.load(bundle_path)
        coverage = self._coverage_gateway.analyze(bundle)
        draft = self._drafting_gateway.build_template(bundle, coverage)
        return {
            "google_docs": self._workspace_gateway.build_docs_package(bundle, coverage, draft),
            "google_sheets": self._workspace_gateway.build_sheets_package(bundle, coverage, draft),
        }
