from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from profile_backend.domain.models import ResolvedBundle
from profile_backend.infrastructure.json_storage import JsonFileStorageGateway


class ProductionBundleGateway:
    def __init__(self) -> None:
        self._storage = JsonFileStorageGateway()

    def resolve(self, bundle_input: str | Path, output_dir: str | Path) -> ResolvedBundle:
        input_path = Path(bundle_input)
        output_root = Path(output_dir)

        if input_path.is_file():
            return ResolvedBundle(bundle=self._storage.load(input_path), bundle_path=input_path)

        if input_path.is_dir():
            extractor_path = (
                Path(__file__).resolve().parents[4]
                / "skills"
                / "profile-report-automation"
                / "scripts"
                / "extract_assessment_bundle.py"
            )
            extracted_bundle_path = output_root / "normalized-bundle.json"
            try:
                subprocess.run(
                    [
                        sys.executable,
                        str(extractor_path),
                        str(input_path),
                        "--output",
                        str(extracted_bundle_path),
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                )
            except subprocess.CalledProcessError as exc:
                details = (exc.stderr or exc.stdout or str(exc)).strip()
                raise ValueError(f"Falha ao montar a base de entrada: {details}") from exc
            return ResolvedBundle(bundle=self._storage.load(extracted_bundle_path), bundle_path=extracted_bundle_path)

        raise FileNotFoundError(f"Bundle input not found: {input_path}")
