from __future__ import annotations

import os

from google.adk.agents import Agent

from profile_backend.application.services.google_auth import GoogleAuthService
from profile_backend.application.services.report_pipeline import ReportPipelineService
from profile_backend.application.services.workspace_publication import WorkspacePublicationService
from profile_backend.domain.models import PipelineRequest

service = ReportPipelineService()
auth_service = GoogleAuthService()
workspace_service = WorkspacePublicationService()


def load_profile_bundle(bundle_path: str) -> dict:
    """Load a normalized assessment bundle from JSON."""

    return service.load_bundle(bundle_path)


def check_report_coverage(bundle_path: str) -> dict:
    """Compare required signals against the current narrative and conclusion."""

    return service.analyze_coverage(bundle_path)


def preview_vertex_draft(bundle_path: str) -> dict:
    """Prepare the prompt and JSON schema that will be sent to Vertex AI."""

    return service.preview_draft(bundle_path)


def build_workspace_outputs(bundle_path: str) -> dict:
    """Prepare Google Docs and Sheets payloads for backend publishing flows."""

    return service.build_output_packages(bundle_path)


def start_google_oauth(analyst_id: str) -> dict:
    """Generate the Google OAuth authorization URL for an analyst."""

    authorization = auth_service.start(analyst_id)
    return authorization.__dict__


def google_oauth_status(analyst_id: str) -> dict:
    """Check whether an analyst already connected Google Workspace."""

    return auth_service.status(analyst_id).__dict__


def revoke_google_oauth(analyst_id: str) -> dict:
    """Revoke and delete the stored Google Workspace token for an analyst."""

    return auth_service.revoke(analyst_id)


def publish_to_google_workspace(
    analyst_id: str,
    bundle_input: str,
    output_dir: str = "artifacts/workspace-publication",
    draft_mode: str = "preview",
    publish_document: bool = True,
    publish_spreadsheet: bool = True,
) -> dict:
    """Publish the generated outputs to Google Docs and Sheets using the analyst OAuth token."""

    result = workspace_service.publish(
        analyst_id=analyst_id,
        bundle_input=bundle_input,
        output_dir=output_dir,
        draft_mode=draft_mode,
        publish_document=publish_document,
        publish_spreadsheet=publish_spreadsheet,
    )
    return result.__dict__


def run_profile_report_pipeline(
    bundle_input: str, output_dir: str = "artifacts/production-run", draft_mode: str = "preview"
) -> dict:
    """Run the production-oriented pipeline and write artifacts to disk."""

    result = service.run(
        PipelineRequest(bundle_input=bundle_input, output_dir=output_dir, draft_mode=draft_mode)  # type: ignore[arg-type]
    )
    return {
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


root_agent = Agent(
    name="profile_report_agent",
    model=os.getenv("VERTEX_MODEL", "gemini-2.5-flash"),
    description="Orquestra a analise de cobertura, a preparacao de rascunho e os pacotes de saida de forma orientada a producao.",
    instruction=(
        "Voce e um agente backend para automacao de relatorios de perfil. "
        "Use ferramentas deterministicas, siga os contratos do backend e mantenha "
        "as integracoes externas fora da logica de aplicacao."
    ),
    tools=[
        load_profile_bundle,
        check_report_coverage,
        preview_vertex_draft,
        build_workspace_outputs,
        start_google_oauth,
        google_oauth_status,
        revoke_google_oauth,
        publish_to_google_workspace,
        run_profile_report_pipeline,
    ],
)
