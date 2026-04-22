from __future__ import annotations

from pathlib import Path


def backend_root() -> Path:
    return Path(__file__).resolve().parents[2]


def workspace_root() -> Path:
    candidate = backend_root().parent
    if (candidate / "docker-compose.yml").exists() or (candidate / ".git").exists():
        return candidate
    return backend_root()


def default_artifacts_root() -> Path:
    return (workspace_root() / "artifacts").resolve()
