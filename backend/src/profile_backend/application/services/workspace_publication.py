from __future__ import annotations

from pathlib import Path

from profile_backend.application.services.report_pipeline import ReportPipelineService
from profile_backend.domain.models import PipelineRequest, WorkspacePublicationResult
from profile_backend.infrastructure.encrypted_token_store import EncryptedFileUserTokenGateway
from profile_backend.infrastructure.google_oauth import GoogleOAuthGateway
from profile_backend.infrastructure.google_workspace_publisher import GoogleWorkspacePublisher
from profile_backend.infrastructure.json_storage import JsonFileStorageGateway


class WorkspacePublicationService:
    def __init__(self) -> None:
        self._pipeline = ReportPipelineService()
        self._token_gateway = EncryptedFileUserTokenGateway()
        self._oauth_gateway = GoogleOAuthGateway()
        self._publisher = GoogleWorkspacePublisher()
        self._storage = JsonFileStorageGateway()

    def publish(
        self,
        *,
        analyst_id: str,
        bundle_input: str,
        output_dir: str,
        draft_mode: str = "preview",
        publish_document: bool = True,
        publish_spreadsheet: bool = True,
    ) -> WorkspacePublicationResult:
        stored = self._token_gateway.load(analyst_id)
        if not stored:
            raise ValueError(f"Analyst '{analyst_id}' is not connected to Google Workspace.")

        refreshed_authorized_user_info = self._oauth_gateway.refresh_authorized_user_info(
            stored["authorized_user_info"]
        )
        stored["authorized_user_info"] = refreshed_authorized_user_info
        self._token_gateway.save(analyst_id, stored)

        pipeline_result = self._pipeline.run(
            PipelineRequest(bundle_input=bundle_input, output_dir=output_dir, draft_mode=draft_mode)  # type: ignore[arg-type]
        )

        document_id = None
        document_url = None
        spreadsheet_id = None
        spreadsheet_url = None

        if publish_document:
            docs_package = self._storage.load(pipeline_result.artifacts.google_docs_package)
            published_doc = self._publisher.publish_document(refreshed_authorized_user_info, docs_package)
            document_id = published_doc["document_id"]
            document_url = published_doc["document_url"]
            stored["authorized_user_info"] = published_doc["authorized_user_info"]
            self._token_gateway.save(analyst_id, stored)

        if publish_spreadsheet:
            sheets_package = self._storage.load(pipeline_result.artifacts.google_sheets_package)
            published_sheet = self._publisher.publish_spreadsheet(refreshed_authorized_user_info, sheets_package)
            spreadsheet_id = published_sheet["spreadsheet_id"]
            spreadsheet_url = published_sheet["spreadsheet_url"]
            stored["authorized_user_info"] = published_sheet["authorized_user_info"]
            self._token_gateway.save(analyst_id, stored)

        publication = WorkspacePublicationResult(
            analyst_id=analyst_id,
            document_id=document_id,
            document_url=document_url,
            spreadsheet_id=spreadsheet_id,
            spreadsheet_url=spreadsheet_url,
            output_dir=str(Path(output_dir).resolve()),
        )
        self._storage.save(Path(output_dir) / "google-workspace-publication.json", publication.__dict__)
        return publication
