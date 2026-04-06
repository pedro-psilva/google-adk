from __future__ import annotations

import json
import re
import shutil
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from typing import Literal

from fastapi import FastAPI, HTTPException, Query, Request, UploadFile
from fastapi.responses import FileResponse
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


UPLOAD_CATEGORY_LABELS = {
    "neopi_pdf": "NEO PI-R",
    "profiler_pdf": "Perfil comportamental",
    "report_workbook": "Planilha do relatorio",
    "report_pdf": "Relatorio final em PDF",
    "anchors_workbook": "Ancoras e diagnostico cultural",
    "bundle_json": "Bundle normalizado",
}

UPLOAD_MANIFEST_FILENAME = "upload-manifest.json"


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


@app.post("/api/v1/intake/upload")
async def upload_assessment_files(request: Request) -> dict:
    form = await request.form()
    label_value = form.get("label")
    label = label_value if isinstance(label_value, str) else None

    incoming_uploads: list[tuple[UploadFile, str | None]] = []
    for item in form.getlist("files"):
        if hasattr(item, "filename") and hasattr(item, "read"):
            incoming_uploads.append((item, None))

    explicit_upload_fields = [
        ("neopi_file", "neopi_pdf"),
        ("profiler_file", "profiler_pdf"),
        ("anchors_file", "anchors_workbook"),
    ]
    for field_name, category in explicit_upload_fields:
        item = form.get(field_name)
        if hasattr(item, "filename") and hasattr(item, "read"):
            incoming_uploads.append((item, category))

    if not incoming_uploads:
        raise HTTPException(status_code=400, detail="Envie pelo menos um arquivo.")

    upload_id = _build_upload_id(label)
    upload_root = Path("artifacts") / "uploads" / upload_id
    intake_dir = upload_root / "intake"
    run_dir = upload_root / "run"
    intake_dir.mkdir(parents=True, exist_ok=True)
    run_dir.mkdir(parents=True, exist_ok=True)

    stored_files: list[dict[str, object]] = []
    used_names: set[str] = set()

    for index, (file, explicit_category) in enumerate(incoming_uploads, start=1):
        original_name = Path(file.filename or f"arquivo-{index}").name
        stored_name = _dedupe_filename(original_name, used_names)
        used_names.add(stored_name)

        destination = intake_dir / stored_name
        byte_count = await _save_upload_file(file, destination)

        category = explicit_category or _classify_uploaded_file(stored_name)
        if category == "report_workbook":
            _cache_report_template(destination)
        stored_files.append(
            {
                "name": stored_name,
                "original_name": original_name,
                "size_bytes": byte_count,
                "category": category,
                "label": UPLOAD_CATEGORY_LABELS.get(category),
            }
        )

    _write_upload_manifest(intake_dir, stored_files)

    uploaded_json_files = [item for item in stored_files if item["category"] == "bundle_json"]
    bundle_input = intake_dir.resolve()
    storage_mode = "intake_dir"
    if len(stored_files) == 1 and uploaded_json_files:
        bundle_input = (intake_dir / str(uploaded_json_files[0]["name"])).resolve()
        storage_mode = "bundle_json"

    return {
        "upload_id": upload_id,
        "bundle_input": str(bundle_input),
        "output_dir": str(run_dir.resolve()),
        "storage_mode": storage_mode,
        "files": stored_files,
    }


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
    try:
        result = service.run(
            PipelineRequest(
                bundle_input=request.bundle_input,
                output_dir=request.output_dir,
                draft_mode=request.draft_mode,
            )
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "status": result.status,
        "bundle_path": result.bundle_path,
        "output_dir": result.output_dir,
        "artifacts": {
            "bundle_path": result.artifacts.bundle_path,
            "coverage_report": result.artifacts.coverage_report,
            "vertex_request_preview": result.artifacts.vertex_request_preview,
            "draft_output": result.artifacts.draft_output,
            "local_report_xlsx": result.artifacts.local_report_xlsx,
            "local_report_docx": result.artifacts.local_report_docx,
            "local_report_pdf": result.artifacts.local_report_pdf,
            "live_draft": result.artifacts.live_draft,
        },
        "used_live_vertex": result.used_live_vertex,
        "notes": result.notes,
    }


@app.get("/api/v1/files/download")
def download_generated_file(path: str = Query(..., min_length=1)) -> FileResponse:
    resolved_path = Path(path).expanduser().resolve()
    artifacts_root = (Path(__file__).resolve().parents[5] / "artifacts").resolve()

    if not resolved_path.exists() or not resolved_path.is_file():
        raise HTTPException(status_code=404, detail="Arquivo nao encontrado.")
    if not resolved_path.is_relative_to(artifacts_root):
        raise HTTPException(status_code=403, detail="Download fora do diretorio permitido.")

    media_type = {
        ".pdf": "application/pdf",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    }.get(resolved_path.suffix.lower(), "application/octet-stream")

    return FileResponse(path=resolved_path, filename=resolved_path.name, media_type=media_type)


def _require_oauth_runtime_config() -> None:
    if not settings.google_oauth_client_id or not settings.google_oauth_client_secret or not settings.google_oauth_redirect_uri:
        raise HTTPException(
            status_code=500,
            detail="Google OAuth is not configured. Set GOOGLE_OAUTH_CLIENT_ID, GOOGLE_OAUTH_CLIENT_SECRET, and GOOGLE_OAUTH_REDIRECT_URI.",
        )


def _normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    without_marks = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", without_marks).strip().lower()


def _build_upload_id(label: str | None) -> str:
    raw_slug = _normalize_text(label or "analise-perfil")
    slug = re.sub(r"[^a-z0-9]+", "-", raw_slug).strip("-") or "analise-perfil"
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return f"{timestamp}-{slug}-{uuid4().hex[:8]}"


def _dedupe_filename(filename: str, used_names: set[str]) -> str:
    candidate = Path(filename).name or "arquivo"
    if candidate not in used_names:
        return candidate

    stem = Path(candidate).stem
    suffix = Path(candidate).suffix
    index = 2
    while True:
        next_candidate = f"{stem}-{index}{suffix}"
        if next_candidate not in used_names:
            return next_candidate
        index += 1


async def _save_upload_file(file: UploadFile, destination: Path) -> int:
    total = 0
    with destination.open("wb") as target:
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            target.write(chunk)
            total += len(chunk)

    await file.close()
    return total


def _cache_report_template(source_path: Path) -> None:
    template_dir = Path("artifacts") / "templates"
    template_dir.mkdir(parents=True, exist_ok=True)
    cached_template = template_dir / "Relatorio de Analise de Perfil.xlsx"
    shutil.copy2(source_path, cached_template)


def _write_upload_manifest(intake_dir: Path, stored_files: list[dict[str, object]]) -> None:
    files_by_category = {
        str(item["category"]): str(item["name"])
        for item in stored_files
        if item.get("category") and item.get("name")
    }
    manifest_payload = {
        "files": stored_files,
        "files_by_category": files_by_category,
    }
    manifest_path = intake_dir / UPLOAD_MANIFEST_FILENAME
    manifest_path.write_text(json.dumps(manifest_payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _classify_uploaded_file(filename: str) -> str | None:
    normalized = _normalize_text(filename)

    if normalized.endswith(".json"):
        return "bundle_json"
    if "neopi-r" in normalized or "neopi r" in normalized:
        return "neopi_pdf"
    if normalized.endswith("extended.pdf") or "extended" in normalized:
        return "profiler_pdf"
    if "relatorio de analise de perfil.xlsx" in normalized:
        return "report_workbook"
    if "relatorio de analise de perfil.pdf" in normalized:
        return "report_pdf"
    if "iebt innovation.xlsx" in normalized or "ancoras" in normalized or "diagnostico" in normalized:
        return "anchors_workbook"
    return None
