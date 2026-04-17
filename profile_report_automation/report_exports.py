from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Any
from uuid import uuid4

from profile_report_automation.regenerated_report_docx import build_regenerated_docx_report
from profile_report_automation.regenerated_report_pdf import build_regenerated_pdf_report


def export_local_reports(
    output_dir: str | Path,
    bundle: dict[str, Any],
    coverage: dict[str, Any],
    draft: dict[str, Any],
) -> dict[str, str]:
    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    base_name = build_report_basename(bundle)
    docx_path = target_dir / f"{base_name}.docx"
    pdf_path = target_dir / f"{base_name}.pdf"

    export_token = uuid4().hex
    temp_docx_path = target_dir / f".{base_name}.{export_token}.docx"
    temp_pdf_path = target_dir / f".{base_name}.{export_token}.pdf"

    try:
        build_docx_report(temp_docx_path, bundle, draft)
        _ensure_generated_file(temp_docx_path, artifact_name="Word")

        build_pdf_report(temp_pdf_path, bundle, draft)
        _ensure_generated_file(temp_pdf_path, artifact_name="PDF")

        temp_docx_path.replace(docx_path)
        temp_pdf_path.replace(pdf_path)
    except Exception:
        _safe_unlink(temp_docx_path)
        _safe_unlink(temp_pdf_path)
        raise

    return {
        "docx": str(docx_path.resolve()),
        "pdf": str(pdf_path.resolve()),
    }


def build_report_basename(bundle: dict[str, Any]) -> str:
    raw_name = str(bundle.get("person", {}).get("name") or "Pessoa avaliada")
    normalized = unicodedata.normalize("NFKD", raw_name)
    without_marks = "".join(character for character in normalized if not unicodedata.combining(character))
    safe_name = re.sub(r'[<>:"/\\\\|?*]+', " ", without_marks)
    safe_name = re.sub(r"\s+", " ", safe_name).strip() or "Pessoa avaliada"
    return f"{safe_name} - Relatorio de Analise de Perfil"


def build_docx_report(path: str | Path, bundle: dict[str, Any], draft: dict[str, Any]) -> None:
    build_regenerated_docx_report(path, bundle, draft)


def build_pdf_report(path: str | Path, bundle: dict[str, Any], draft: dict[str, Any]) -> None:
    build_regenerated_pdf_report(path, bundle, draft)


def _ensure_generated_file(path: Path, *, artifact_name: str) -> None:
    if not path.exists() or path.stat().st_size <= 0:
        raise RuntimeError(f"Falha ao gerar o {artifact_name}: arquivo final ausente ou vazio.")


def _safe_unlink(path: Path) -> None:
    try:
        path.unlink()
    except FileNotFoundError:
        return
