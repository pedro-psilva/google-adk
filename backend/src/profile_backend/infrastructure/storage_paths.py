from __future__ import annotations

from pathlib import Path

from profile_backend.infrastructure.config import settings


def artifacts_root() -> Path:
    return settings.artifacts_root


def uploads_root() -> Path:
    return artifacts_root() / "uploads"


def templates_root() -> Path:
    return artifacts_root() / "templates"


def adk_artifacts_root() -> Path:
    return artifacts_root() / "adk-sessions"


def resolve_output_dir(path: str | Path) -> Path:
    resolved = _resolve_under_artifacts_root(path)
    return resolved


def resolve_download_path(path: str | Path) -> Path:
    resolved = Path(path).expanduser().resolve()
    _ensure_within_root(resolved, artifacts_root())
    return resolved


def resolve_bundle_input(path: str | Path) -> Path:
    candidate = Path(path).expanduser()
    if candidate.is_absolute():
        return candidate.resolve()
    repo_relative = (settings.repo_root / candidate).resolve()
    if repo_relative.exists():
        return repo_relative
    return _resolve_under_artifacts_root(candidate)


def _resolve_under_artifacts_root(path: str | Path) -> Path:
    candidate = Path(path).expanduser()
    if candidate.is_absolute():
        resolved = candidate.resolve()
    else:
        relative = _normalize_artifacts_relative_path(candidate)
        resolved = (artifacts_root() / relative).resolve()
    _ensure_within_root(resolved, artifacts_root())
    return resolved


def _normalize_artifacts_relative_path(path: Path) -> Path:
    if not path.parts:
        return Path()

    first_segment = str(path.parts[0]).lower()
    if first_segment == artifacts_root().name.lower():
        remaining_parts = path.parts[1:]
        return Path(*remaining_parts) if remaining_parts else Path()
    return path


def _ensure_within_root(candidate: Path, root: Path) -> None:
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"O caminho precisa permanecer dentro de {root}.") from exc
