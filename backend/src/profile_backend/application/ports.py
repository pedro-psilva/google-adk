from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol

from profile_backend.domain.models import DraftMode, ResolvedBundle


class BundleGateway(Protocol):
    def resolve(self, bundle_input: str | Path, output_dir: str | Path) -> ResolvedBundle: ...


class CoverageGateway(Protocol):
    def analyze(self, bundle: dict[str, Any]) -> dict[str, Any]: ...


class DraftingGateway(Protocol):
    def build_preview(self, bundle: dict[str, Any], coverage: dict[str, Any]) -> dict[str, Any]: ...

    def build_template(self, bundle: dict[str, Any], coverage: dict[str, Any]) -> dict[str, Any]: ...

    def build_live(self, bundle: dict[str, Any], coverage: dict[str, Any]) -> dict[str, Any]: ...


class JsonStorageGateway(Protocol):
    def save(self, path: str | Path, payload: Any) -> Path: ...

    def load(self, path: str | Path) -> dict[str, Any]: ...
