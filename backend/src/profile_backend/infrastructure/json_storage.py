from __future__ import annotations

from pathlib import Path
from typing import Any

from profile_report_automation.bundle import load_bundle, save_json


class JsonFileStorageGateway:
    def save(self, path: str | Path, payload: Any) -> Path:
        return save_json(path, payload)

    def load(self, path: str | Path) -> dict[str, Any]:
        return load_bundle(path)
