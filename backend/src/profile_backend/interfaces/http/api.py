from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import re
import shutil
import unicodedata
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from typing import Literal

from fastapi import FastAPI, HTTPException, Query, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from starlette.background import BackgroundTask

from profile_backend.domain.models import PipelineRequest
from profile_backend.interfaces.adk.agent import adk_analysis_runner, adk_pipeline_runner
from profile_backend.infrastructure.artifact_cleanup import (
    cleanup_managed_artifacts,
    initialize_upload_lifecycle,
    mark_upload_delivered,
)
from profile_backend.infrastructure.config import settings
from profile_backend.infrastructure.storage_paths import (
    resolve_bundle_input,
    resolve_download_path,
    resolve_output_dir,
    templates_root,
    uploads_root,
)

LOGGER = logging.getLogger(__name__)


@asynccontextmanager
async def _lifespan(application: FastAPI):  # noqa: ARG001
    """FastAPI lifespan: start artifact cleanup loop on startup, cancel on shutdown."""
    cleanup_task: asyncio.Task | None = None
    if settings.artifact_cleanup_enabled:
        await asyncio.to_thread(cleanup_managed_artifacts)
        cleanup_task = asyncio.create_task(_artifact_cleanup_loop())
        application.state.artifact_cleanup_task = cleanup_task
    yield
    if cleanup_task is not None:
        cleanup_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await cleanup_task


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=_lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_allowed_origins),
    allow_origin_regex=settings.cors_allowed_origin_regex,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)


class BundlePathRequest(BaseModel):
    bundle_path: str


class PipelineRunRequest(BaseModel):
    bundle_input: str
    output_dir: str = Field(default="production-run")
    draft_mode: Literal["preview", "live"] = Field(default="preview")


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
    upload_root = uploads_root() / upload_id
    intake_dir = upload_root / "intake"
    run_dir = upload_root / "run"
    intake_dir.mkdir(parents=True, exist_ok=True)
    run_dir.mkdir(parents=True, exist_ok=True)
    initialize_upload_lifecycle(upload_root, upload_id=upload_id, label=label)

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
    return adk_analysis_runner.load_bundle(request.bundle_path)


@app.post("/api/v1/reports/coverage")
def report_coverage(request: BundlePathRequest) -> dict:
    return adk_analysis_runner.analyze_coverage(request.bundle_path)


@app.post("/api/v1/reports/draft-preview")
def draft_preview(request: BundlePathRequest) -> dict:
    return adk_analysis_runner.preview_draft(request.bundle_path)


@app.post("/api/v1/pipeline/run")
def run_pipeline(request: PipelineRunRequest) -> dict:
    try:
        resolved_bundle_input = resolve_bundle_input(request.bundle_input)
        resolved_output_dir = resolve_output_dir(request.output_dir)
        result = adk_pipeline_runner.run(
            PipelineRequest(
                bundle_input=str(resolved_bundle_input),
                output_dir=str(resolved_output_dir),
                draft_mode=request.draft_mode,
            )
        )
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result


@app.get("/api/v1/files/download")
def download_generated_file(path: str = Query(..., min_length=1)) -> FileResponse:
    try:
        resolved_path = resolve_download_path(path)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc

    if not resolved_path.exists() or not resolved_path.is_file():
        raise HTTPException(status_code=404, detail="Arquivo nao encontrado.")

    media_type = {
        ".pdf": "application/pdf",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    }.get(resolved_path.suffix.lower(), "application/octet-stream")

    return FileResponse(
        path=resolved_path,
        filename=resolved_path.name,
        media_type=media_type,
        background=BackgroundTask(_mark_download_delivered, resolved_path),
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
    template_dir = templates_root()
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


def _mark_download_delivered(path: Path) -> None:
    try:
        mark_upload_delivered(path)
    except Exception:
        LOGGER.exception("Failed to mark delivered artifact for cleanup tracking: %s", path)


async def _artifact_cleanup_loop() -> None:
    interval_seconds = max(60, settings.artifact_cleanup_interval_minutes * 60)
    while True:
        try:
            await asyncio.sleep(interval_seconds)
            await asyncio.to_thread(cleanup_managed_artifacts)
        except asyncio.CancelledError:
            raise
        except Exception:
            LOGGER.exception("Artifact cleanup loop failed")
