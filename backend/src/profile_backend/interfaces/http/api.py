from __future__ import annotations

from typing import Literal

from fastapi import FastAPI, HTTPException, Query, Request
from pydantic import BaseModel, Field
from starlette.middleware.sessions import SessionMiddleware

from profile_backend.application.services.google_auth import GoogleAuthService
from profile_backend.application.services.report_pipeline import ReportPipelineService
from profile_backend.application.services.workspace_publication import WorkspacePublicationService
from profile_backend.domain.models import PipelineRequest
from profile_backend.infrastructure.config import settings

app = FastAPI(title=settings.app_name, version="0.1.0")
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.app_session_secret or "development-only-change-me",
    same_site="lax",
    https_only=settings.environment != "development",
)

service = ReportPipelineService()
auth_service = GoogleAuthService()
workspace_service = WorkspacePublicationService()


class BundlePathRequest(BaseModel):
    bundle_path: str


class PipelineRunRequest(BaseModel):
    bundle_input: str
    output_dir: str = Field(default="artifacts/production-run")
    draft_mode: Literal["preview", "live"] = Field(default="preview")


class AnalystRequest(BaseModel):
    analyst_id: str


class PublishWorkspaceRequest(BaseModel):
    analyst_id: str
    bundle_input: str
    output_dir: str = Field(default="artifacts/workspace-publication")
    draft_mode: Literal["preview", "live"] = Field(default="preview")
    publish_document: bool = True
    publish_spreadsheet: bool = True


@app.get("/healthz")
def healthcheck() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}


@app.get("/api/v1/auth/google/start")
def google_oauth_start(request: Request, analyst_id: str = Query(..., min_length=1)) -> dict:
    _require_oauth_runtime_config()
    authorization = auth_service.start(analyst_id)
    request.session["google_oauth_state"] = authorization.state
    request.session["google_oauth_analyst_id"] = analyst_id
    return {
        "analyst_id": analyst_id,
        "authorization_url": authorization.authorization_url,
        "state": authorization.state,
    }


@app.get("/api/v1/auth/google/callback")
def google_oauth_callback(request: Request, state: str, code: str) -> dict:
    _require_oauth_runtime_config()
    expected_state = request.session.get("google_oauth_state")
    analyst_id = request.session.get("google_oauth_analyst_id")
    if not expected_state or not analyst_id:
        raise HTTPException(status_code=400, detail="OAuth session not found or expired.")
    if state != expected_state:
        raise HTTPException(status_code=400, detail="Invalid OAuth state.")

    result = auth_service.complete(analyst_id, state, code)
    request.session.pop("google_oauth_state", None)
    request.session.pop("google_oauth_analyst_id", None)
    return result


@app.get("/api/v1/auth/google/status")
def google_oauth_status(analyst_id: str = Query(..., min_length=1)) -> dict:
    status = auth_service.status(analyst_id)
    return status.__dict__


@app.post("/api/v1/auth/google/revoke")
def google_oauth_revoke(request: AnalystRequest) -> dict:
    _require_oauth_runtime_config()
    return auth_service.revoke(request.analyst_id)


@app.post("/api/v1/bundles/load")
def load_bundle(request: BundlePathRequest) -> dict:
    return service.load_bundle(request.bundle_path)


@app.post("/api/v1/reports/coverage")
def report_coverage(request: BundlePathRequest) -> dict:
    return service.analyze_coverage(request.bundle_path)


@app.post("/api/v1/reports/draft-preview")
def draft_preview(request: BundlePathRequest) -> dict:
    return service.preview_draft(request.bundle_path)


@app.post("/api/v1/reports/output-packages")
def output_packages(request: BundlePathRequest) -> dict:
    return service.build_output_packages(request.bundle_path)


@app.post("/api/v1/workspace/publish")
def publish_workspace_outputs(request: PublishWorkspaceRequest) -> dict:
    _require_oauth_runtime_config()
    try:
        publication = workspace_service.publish(
            analyst_id=request.analyst_id,
            bundle_input=request.bundle_input,
            output_dir=request.output_dir,
            draft_mode=request.draft_mode,
            publish_document=request.publish_document,
            publish_spreadsheet=request.publish_spreadsheet,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return publication.__dict__


@app.post("/api/v1/pipeline/run")
def run_pipeline(request: PipelineRunRequest) -> dict:
    result = service.run(
        PipelineRequest(
            bundle_input=request.bundle_input,
            output_dir=request.output_dir,
            draft_mode=request.draft_mode,
        )
    )
    return {
        "status": result.status,
        "bundle_path": result.bundle_path,
        "output_dir": result.output_dir,
        "artifacts": {
            "bundle_path": result.artifacts.bundle_path,
            "coverage_report": result.artifacts.coverage_report,
            "vertex_request_preview": result.artifacts.vertex_request_preview,
            "draft_output": result.artifacts.draft_output,
            "google_docs_package": result.artifacts.google_docs_package,
            "google_sheets_package": result.artifacts.google_sheets_package,
            "live_draft": result.artifacts.live_draft,
        },
        "used_live_vertex": result.used_live_vertex,
        "notes": result.notes,
    }


def _require_oauth_runtime_config() -> None:
    if not settings.google_oauth_client_id or not settings.google_oauth_client_secret or not settings.google_oauth_redirect_uri:
        raise HTTPException(
            status_code=500,
            detail="Google OAuth is not configured. Set GOOGLE_OAUTH_CLIENT_ID, GOOGLE_OAUTH_CLIENT_SECRET, and GOOGLE_OAUTH_REDIRECT_URI.",
        )
