from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _env_flag(name: str, default: bool) -> bool:
    raw_value = os.getenv(name, "").strip().lower()
    if not raw_value:
        return default
    return raw_value not in {"0", "false", "no", "off"}


def _env_positive_int(name: str, default: int) -> int:
    raw_value = os.getenv(name, "").strip()
    if not raw_value:
        return default
    try:
        parsed_value = int(raw_value)
    except ValueError:
        return default
    return parsed_value if parsed_value > 0 else default


def _backend_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _repo_root() -> Path:
    candidate = _backend_root().parent
    if (candidate / "docker-compose.yml").exists() or (candidate / ".git").exists():
        return candidate
    return _backend_root()


def _load_repo_env() -> None:
    env_paths: list[Path] = []
    for candidate in (_repo_root() / ".env", _backend_root() / ".env"):
        if candidate not in env_paths:
            env_paths.append(candidate)

    for env_path in env_paths:
        if not env_path.exists():
            continue

        # Keep shell-provided variables authoritative and only backfill from .env.
        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in {"\"", "'"}:
                value = value[1:-1]
            os.environ.setdefault(key, value)


_load_repo_env()


def _resolve_artifacts_root() -> Path:
    raw_value = os.getenv("ARTIFACTS_ROOT", "").strip()
    if raw_value:
        return Path(raw_value).expanduser().resolve()
    return (_repo_root() / "artifacts").resolve()


@dataclass(frozen=True)
class Settings:
    app_name: str = "profile-report-backend"
    environment: str = os.getenv("APP_ENV", "development")
    google_cloud_project: str | None = os.getenv("GOOGLE_CLOUD_PROJECT")
    google_cloud_location: str | None = os.getenv("GOOGLE_CLOUD_LOCATION")
    vertex_model: str = os.getenv("VERTEX_MODEL", "gemini-2.5-flash")
    backend_root: Path = _backend_root()
    repo_root: Path = _repo_root()
    artifacts_root: Path = _resolve_artifacts_root()
    artifact_cleanup_enabled: bool = _env_flag("ARTIFACT_CLEANUP_ENABLED", True)
    artifact_cleanup_interval_minutes: int = _env_positive_int("ARTIFACT_CLEANUP_INTERVAL_MINUTES", 10)
    delivered_artifact_retention_minutes: int = _env_positive_int("DELIVERED_ARTIFACT_RETENTION_MINUTES", 30)
    stale_artifact_retention_hours: int = _env_positive_int("STALE_ARTIFACT_RETENTION_HOURS", 6)


settings = Settings()
