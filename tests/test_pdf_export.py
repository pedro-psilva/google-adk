from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from profile_report_automation.pdf_export import (  # noqa: E402
    build_artifact_relative_path,
    export_workbook_sheet_via_worker,
    resolve_artifact_relative_path,
)


class _FakeResponse:
    def __init__(self, payload: bytes) -> None:
        self._payload = payload

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        return None

    def read(self) -> bytes:
        return self._payload


class PdfExportPathTests(unittest.TestCase):
    def test_build_artifact_relative_path_returns_posix_relative_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            artifacts_root = Path(temp_dir)
            target_path = artifacts_root / "uploads" / "case-1" / "run" / "report.xlsx"
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.touch()

            relative_path = build_artifact_relative_path(target_path, artifacts_root=artifacts_root)

            self.assertEqual(relative_path, "uploads/case-1/run/report.xlsx")

    def test_build_artifact_relative_path_rejects_path_outside_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            artifacts_root = Path(temp_dir) / "artifacts"
            artifacts_root.mkdir(parents=True, exist_ok=True)
            outside_path = Path(temp_dir) / "report.xlsx"
            outside_path.touch()

            with self.assertRaisesRegex(ValueError, "precisa permanecer dentro"):
                build_artifact_relative_path(outside_path, artifacts_root=artifacts_root)

    def test_resolve_artifact_relative_path_rejects_absolute_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            artifacts_root = Path(temp_dir)
            absolute_path = str((artifacts_root / "report.xlsx").resolve())

            with self.assertRaisesRegex(ValueError, "Use apenas caminhos relativos"):
                resolve_artifact_relative_path(absolute_path, artifacts_root=artifacts_root)

    def test_resolve_artifact_relative_path_rejects_escape_attempt(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            artifacts_root = Path(temp_dir) / "artifacts"
            artifacts_root.mkdir(parents=True, exist_ok=True)

            with self.assertRaisesRegex(ValueError, "precisa permanecer dentro"):
                resolve_artifact_relative_path("../fora/report.xlsx", artifacts_root=artifacts_root)


class PdfExportWorkerTests(unittest.TestCase):
    def test_export_workbook_sheet_via_worker_returns_false_without_worker_url(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            artifacts_root = Path(temp_dir)
            workbook_path = artifacts_root / "uploads" / "case-1" / "run" / "report.xlsx"
            workbook_path.parent.mkdir(parents=True, exist_ok=True)
            workbook_path.touch()
            pdf_path = workbook_path.with_suffix(".pdf")

            exported = export_workbook_sheet_via_worker(
                pdf_path,
                workbook_path,
                artifacts_root=artifacts_root,
                worker_url=None,
            )

            self.assertFalse(exported)

    def test_export_workbook_sheet_via_worker_posts_relative_paths_and_accepts_success(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            artifacts_root = Path(temp_dir)
            workbook_path = artifacts_root / "uploads" / "case-1" / "run" / "report.xlsx"
            workbook_path.parent.mkdir(parents=True, exist_ok=True)
            workbook_path.write_bytes(b"xlsx")
            pdf_path = workbook_path.with_suffix(".pdf")

            def fake_urlopen(request, timeout):  # type: ignore[no-untyped-def]
                payload = json.loads(request.data.decode("utf-8"))
                self.assertEqual(payload["workbook_artifact_path"], "uploads/case-1/run/report.xlsx")
                self.assertEqual(payload["pdf_artifact_path"], "uploads/case-1/run/report.pdf")
                self.assertEqual(timeout, 15)
                pdf_path.write_bytes(b"%PDF-1.7")
                return _FakeResponse(b'{"status":"ok"}')

            with patch("urllib.request.urlopen", side_effect=fake_urlopen):
                exported = export_workbook_sheet_via_worker(
                    pdf_path,
                    workbook_path,
                    artifacts_root=artifacts_root,
                    worker_url="http://worker.local:8010",
                    worker_timeout_seconds=15,
                )

            self.assertTrue(exported)
            self.assertTrue(pdf_path.exists())


if __name__ == "__main__":
    unittest.main()
