from __future__ import annotations

import json
import os
import subprocess
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

from profile_report_automation._paths import default_artifacts_root, workspace_root


PDF_EXPORT_WORKSHEET_NAME = "Síntese"
DEFAULT_PDF_EXPORT_WORKER_TIMEOUT_SECONDS = 180.0


def get_repo_root() -> Path:
    return workspace_root()


def get_artifacts_root() -> Path:
    raw_value = os.getenv("ARTIFACTS_ROOT", "").strip()
    if raw_value:
        return Path(raw_value).expanduser().resolve()
    return default_artifacts_root()


def get_pdf_export_worker_url() -> str | None:
    raw_value = os.getenv("PDF_EXPORT_WORKER_URL", "").strip()
    return raw_value or None


def get_pdf_export_worker_timeout_seconds() -> float:
    raw_value = os.getenv("PDF_EXPORT_WORKER_TIMEOUT_SECONDS", "").strip()
    if not raw_value:
        return DEFAULT_PDF_EXPORT_WORKER_TIMEOUT_SECONDS

    try:
        timeout_seconds = float(raw_value)
    except ValueError:
        return DEFAULT_PDF_EXPORT_WORKER_TIMEOUT_SECONDS

    return timeout_seconds if timeout_seconds > 0 else DEFAULT_PDF_EXPORT_WORKER_TIMEOUT_SECONDS


def build_artifact_relative_path(path: str | Path, *, artifacts_root: str | Path | None = None) -> str:
    root = _resolve_artifacts_root(artifacts_root)
    candidate = Path(path).expanduser().resolve()
    try:
        relative_path = candidate.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"O caminho precisa permanecer dentro de {root}.") from exc

    if not relative_path.parts:
        raise ValueError("O caminho relativo do artefato nao pode ser vazio.")

    return relative_path.as_posix()


def resolve_artifact_relative_path(relative_path: str, *, artifacts_root: str | Path | None = None) -> Path:
    root = _resolve_artifacts_root(artifacts_root)
    raw_value = str(relative_path or "").strip()
    if not raw_value:
        raise ValueError("O caminho relativo do artefato nao pode ser vazio.")

    candidate_path = Path(raw_value)
    if candidate_path.is_absolute() or candidate_path.drive:
        raise ValueError("Use apenas caminhos relativos dentro do diretorio de artifacts.")

    resolved_path = (root / candidate_path).resolve()
    try:
        resolved_path.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"O caminho precisa permanecer dentro de {root}.") from exc

    return resolved_path


def export_workbook_sheet_via_excel(
    path: str | Path,
    workbook_path: str | Path,
    *,
    worksheet_name: str = PDF_EXPORT_WORKSHEET_NAME,
    raise_on_error: bool = False,
) -> bool:
    script_path = get_repo_root() / "scripts" / "export_excel_sheet_to_pdf.ps1"
    if not script_path.exists():
        if raise_on_error:
            raise RuntimeError(f"Script de exportacao em PDF nao encontrado em {script_path}.")
        return False

    workbook = Path(workbook_path).expanduser().resolve()
    target = Path(path).expanduser().resolve()

    command = [
        "powershell",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(script_path),
        "-WorkbookPath",
        str(workbook),
        "-PdfPath",
        str(target),
        "-WorksheetName",
        worksheet_name,
    ]

    try:
        completed = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        if raise_on_error:
            raise RuntimeError(f"Nao foi possivel iniciar o PowerShell para exportar o PDF: {exc}") from exc
        return False
    except subprocess.CalledProcessError as exc:
        if raise_on_error:
            raise RuntimeError(_extract_subprocess_error_detail(exc)) from exc
        return False

    return target.exists() and target.stat().st_size > 0 and "PDF_EXPORTED" in completed.stdout


def export_workbook_sheet_via_worker(
    path: str | Path,
    workbook_path: str | Path,
    *,
    worksheet_name: str = PDF_EXPORT_WORKSHEET_NAME,
    worker_url: str | None = None,
    worker_timeout_seconds: float | None = None,
    artifacts_root: str | Path | None = None,
) -> bool:
    base_url = (worker_url or get_pdf_export_worker_url() or "").strip()
    if not base_url:
        return False

    timeout_seconds = worker_timeout_seconds or get_pdf_export_worker_timeout_seconds()
    target = Path(path).expanduser().resolve()
    payload = {
        "workbook_artifact_path": build_artifact_relative_path(workbook_path, artifacts_root=artifacts_root),
        "pdf_artifact_path": build_artifact_relative_path(target, artifacts_root=artifacts_root),
        "worksheet_name": worksheet_name,
    }
    request = urllib.request.Request(
        _build_worker_endpoint(base_url, "/api/v1/pdf/export-workbook"),
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            body = response.read()
    except urllib.error.HTTPError as exc:
        detail = _extract_worker_http_error_detail(exc)
        raise RuntimeError(f"Falha ao exportar o PDF via worker do Excel: {detail}") from exc
    except urllib.error.URLError as exc:
        reason = getattr(exc, "reason", exc)
        raise RuntimeError(
            "Nao foi possivel conectar ao worker de PDF do Excel em "
            f"{base_url}. Inicie o worker Windows com Excel ou ajuste PDF_EXPORT_WORKER_URL. Detalhe: {reason}"
        ) from exc
    except TimeoutError as exc:
        raise RuntimeError(
            f"O worker de PDF do Excel em {base_url} excedeu o tempo limite de {timeout_seconds:.0f}s."
        ) from exc

    response_payload = _decode_json_payload(body)
    if isinstance(response_payload, dict):
        status = str(response_payload.get("status") or "").strip().lower()
        if status and status != "ok":
            detail = str(response_payload.get("detail") or "Resposta invalida do worker de PDF.")
            raise RuntimeError(detail)

    if not target.exists() or target.stat().st_size <= 0:
        raise RuntimeError(
            "O worker de PDF respondeu sem erro, mas o arquivo final nao foi encontrado no diretorio de artifacts."
        )

    return True


def _resolve_artifacts_root(artifacts_root: str | Path | None) -> Path:
    root = Path(artifacts_root) if artifacts_root is not None else get_artifacts_root()
    return root.expanduser().resolve()


def _build_worker_endpoint(base_url: str, path: str) -> str:
    normalized_base_url = base_url.rstrip("/") + "/"
    normalized_path = path.lstrip("/")
    return urljoin(normalized_base_url, normalized_path)


def _decode_json_payload(raw_payload: bytes) -> dict[str, Any] | None:
    if not raw_payload:
        return None

    try:
        decoded_payload = raw_payload.decode("utf-8")
    except UnicodeDecodeError:
        return None

    try:
        parsed_payload = json.loads(decoded_payload)
    except json.JSONDecodeError:
        return None

    return parsed_payload if isinstance(parsed_payload, dict) else None


def _extract_worker_http_error_detail(exc: urllib.error.HTTPError) -> str:
    payload = _decode_json_payload(exc.read())
    if payload and payload.get("detail"):
        return str(payload["detail"])
    if exc.reason:
        return str(exc.reason)
    return f"HTTP {exc.code}"


def _extract_subprocess_error_detail(exc: subprocess.CalledProcessError) -> str:
    raw_output = (exc.stderr or exc.stdout or str(exc)).strip()
    if not raw_output:
        return str(exc)

    lines = [line.strip() for line in raw_output.splitlines() if line.strip()]
    return lines[-1] if lines else str(exc)
