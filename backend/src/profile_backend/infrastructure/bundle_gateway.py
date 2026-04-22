from __future__ import annotations

from pathlib import Path

from profile_backend.domain.models import ResolvedBundle
from profile_backend.infrastructure.json_storage import JsonFileStorageGateway
from profile_report_automation.extract_assessment_bundle import build_bundle


class ProductionBundleGateway:
    def __init__(self) -> None:
        self._storage = JsonFileStorageGateway()

    def resolve(self, bundle_input: str | Path, output_dir: str | Path) -> ResolvedBundle:
        input_path = Path(bundle_input)
        output_root = Path(output_dir)

        if input_path.is_file():
            return ResolvedBundle(bundle=self._storage.load(input_path), bundle_path=input_path)

        if input_path.is_dir():
            extracted_bundle_path = output_root / "normalized-bundle.json"
            try:
                extracted_bundle = build_bundle(input_path)
                self._storage.save(extracted_bundle_path, extracted_bundle)
            except (FileNotFoundError, ValueError, RuntimeError) as exc:
                raise ValueError(f"Falha ao montar a base de entrada: {exc}") from exc
            return ResolvedBundle(bundle=extracted_bundle, bundle_path=extracted_bundle_path)

        raise FileNotFoundError(f"Bundle input not found: {input_path}")
