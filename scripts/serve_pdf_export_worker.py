#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend" / "src"))

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from profile_report_automation.pdf_export import (
    PDF_EXPORT_WORKSHEET_NAME,
    export_workbook_sheet_via_excel,
    get_repo_root,
    resolve_artifact_relative_path,
)


EXPORT_LOCK = threading.Lock()
ARTIFACTS_ROOT = Path(os.getenv("PDF_EXPORT_ARTIFACTS_ROOT") or (get_repo_root() / "artifacts")).expanduser().resolve()
EXPORT_SCRIPT_PATH = get_repo_root() / "scripts" / "export_excel_sheet_to_pdf.ps1"

app = FastAPI(title="profile-report-pdf-export-worker", version="0.1.0")


class ExportWorkbookRequest(BaseModel):
    workbook_artifact_path: str = Field(min_length=1)
    pdf_artifact_path: str = Field(min_length=1)
    worksheet_name: str = Field(default=PDF_EXPORT_WORKSHEET_NAME, min_length=1)


@app.get("/healthz")
def healthcheck() -> dict[str, object]:
    return {
        "status": "ok",
        "service": "profile-report-pdf-export-worker",
        "artifacts_root": str(ARTIFACTS_ROOT),
        "export_script": str(EXPORT_SCRIPT_PATH),
        "export_script_exists": EXPORT_SCRIPT_PATH.exists(),
    }


@app.post("/api/v1/pdf/export-workbook")
def export_workbook_pdf(request: ExportWorkbookRequest) -> dict[str, object]:
    try:
        workbook_path = resolve_artifact_relative_path(
            request.workbook_artifact_path,
            artifacts_root=ARTIFACTS_ROOT,
        )
        pdf_path = resolve_artifact_relative_path(
            request.pdf_artifact_path,
            artifacts_root=ARTIFACTS_ROOT,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if workbook_path.suffix.lower() != ".xlsx":
        raise HTTPException(status_code=400, detail="A planilha de entrada precisa estar em formato .xlsx.")
    if pdf_path.suffix.lower() != ".pdf":
        raise HTTPException(status_code=400, detail="O arquivo de saida precisa ter extensao .pdf.")
    if not workbook_path.exists():
        raise HTTPException(status_code=404, detail=f"Planilha nao encontrada em {workbook_path}.")

    pdf_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with EXPORT_LOCK:
            exported = export_workbook_sheet_via_excel(
                pdf_path,
                workbook_path,
                worksheet_name=request.worksheet_name,
                raise_on_error=True,
            )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    if not exported:
        raise HTTPException(
            status_code=503,
            detail=(
                "Nao foi possivel exportar o PDF pelo Microsoft Excel. "
                "Verifique se o Excel esta instalado e acessivel para COM automation no host Windows."
            ),
        )

    return {
        "status": "ok",
        "workbook_artifact_path": request.workbook_artifact_path,
        "pdf_artifact_path": request.pdf_artifact_path,
        "worksheet_name": request.worksheet_name,
    }


def main() -> None:
    host = os.getenv("PDF_EXPORT_WORKER_HOST", "0.0.0.0")
    port = int(os.getenv("PDF_EXPORT_WORKER_PORT", "8010"))
    uvicorn.run(app, host=host, port=port, reload=False)


if __name__ == "__main__":
    main()
