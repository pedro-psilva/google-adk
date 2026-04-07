from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _load_repo_env() -> None:
    env_path = Path(__file__).resolve().parents[4] / ".env"
    if not env_path.exists():
        return

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


@dataclass(frozen=True)
class Settings:
    app_name: str = "profile-report-backend"
    environment: str = os.getenv("APP_ENV", "development")
    google_cloud_project: str | None = os.getenv("GOOGLE_CLOUD_PROJECT")
    google_cloud_location: str | None = os.getenv("GOOGLE_CLOUD_LOCATION")
    vertex_model: str = os.getenv("VERTEX_MODEL", "gemini-2.5-flash")


settings = Settings()
