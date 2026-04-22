from __future__ import annotations

import json
import logging
import shutil
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from profile_backend.infrastructure.config import settings
from profile_backend.infrastructure.storage_paths import adk_artifacts_root, uploads_root

LOGGER = logging.getLogger(__name__)

UPLOAD_LIFECYCLE_FILENAME = ".upload-lifecycle.json"


@dataclass(frozen=True)
class CleanupSummary:
    uploads_deleted: int = 0
    adk_files_deleted: int = 0
    adk_dirs_pruned: int = 0


def initialize_upload_lifecycle(upload_root: str | Path, *, upload_id: str, label: str | None) -> None:
    root = Path(upload_root)
    payload = _load_upload_lifecycle(root)
    payload.setdefault("upload_id", upload_id)
    payload.setdefault("label", label or "")
    payload.setdefault("created_at", _serialize_timestamp(_utcnow()))
    _write_upload_lifecycle(root, payload)


def mark_upload_delivered(path: str | Path) -> None:
    upload_root = _resolve_upload_root_for_path(path)
    if upload_root is None:
        return

    now = _utcnow()
    payload = _load_upload_lifecycle(upload_root)
    payload.setdefault("upload_id", upload_root.name)
    payload.setdefault("created_at", _serialize_timestamp(_timestamp_from_path(upload_root)))
    payload.setdefault("first_delivered_at", _serialize_timestamp(now))
    payload["last_downloaded_at"] = _serialize_timestamp(now)
    payload["last_downloaded_file"] = Path(path).name
    payload["download_count"] = _coerce_int(payload.get("download_count")) + 1
    _write_upload_lifecycle(upload_root, payload)


def cleanup_managed_artifacts(*, now: datetime | None = None) -> CleanupSummary:
    current_time = now or _utcnow()
    uploads_deleted = _cleanup_upload_roots(current_time)
    adk_files_deleted, adk_dirs_pruned = _cleanup_adk_artifacts(current_time)
    return CleanupSummary(
        uploads_deleted=uploads_deleted,
        adk_files_deleted=adk_files_deleted,
        adk_dirs_pruned=adk_dirs_pruned,
    )


def _cleanup_upload_roots(now: datetime) -> int:
    root = uploads_root()
    if not root.exists():
        return 0

    delivered_cutoff = now - timedelta(minutes=settings.delivered_artifact_retention_minutes)
    stale_cutoff = now - timedelta(hours=settings.stale_artifact_retention_hours)
    deleted_count = 0
    failed_roots: list[Path] = []

    for upload_root in root.iterdir():
        if not upload_root.is_dir():
            continue

        payload = _load_upload_lifecycle(upload_root)
        last_downloaded_at = _parse_timestamp(payload.get("last_downloaded_at"))
        created_at = _parse_timestamp(payload.get("created_at")) or _timestamp_from_path(upload_root)

        should_delete = False
        delete_reason = ""
        if last_downloaded_at is not None and last_downloaded_at <= delivered_cutoff:
            should_delete = True
            delete_reason = "delivery_ttl"
        elif created_at <= stale_cutoff:
            should_delete = True
            delete_reason = "stale_ttl"

        if not should_delete:
            continue

        try:
            shutil.rmtree(upload_root, ignore_errors=False)
        except OSError as exc:
            LOGGER.debug("Failed to remove managed upload artifacts: %s (%s)", upload_root, exc)
            failed_roots.append(upload_root)
            continue

        deleted_count += 1
        LOGGER.info("Removed managed upload artifacts: %s (reason=%s)", upload_root, delete_reason)

    if failed_roots:
        LOGGER.warning(
            "Artifact cleanup skipped %s upload directories that could not be removed. Example: %s",
            len(failed_roots),
            failed_roots[0],
        )

    return deleted_count


def _cleanup_adk_artifacts(now: datetime) -> tuple[int, int]:
    root = adk_artifacts_root()
    if not root.exists():
        return 0, 0

    stale_cutoff = now - timedelta(hours=settings.stale_artifact_retention_hours)
    deleted_files = 0
    failed_files: list[Path] = []

    for file_path in root.rglob("*"):
        if not file_path.is_file():
            continue
        if _timestamp_from_path(file_path) > stale_cutoff:
            continue
        try:
            file_path.unlink(missing_ok=True)
        except OSError as exc:
            LOGGER.debug("Failed to delete stale ADK artifact file: %s (%s)", file_path, exc)
            failed_files.append(file_path)
            continue
        deleted_files += 1

    pruned_directories = 0
    failed_directories: list[Path] = []
    for directory in sorted((path for path in root.rglob("*") if path.is_dir()), key=lambda item: len(item.parts), reverse=True):
        try:
            next(directory.iterdir())
            continue
        except StopIteration:
            try:
                directory.rmdir()
            except OSError as exc:
                LOGGER.debug("Failed to prune ADK artifact directory: %s (%s)", directory, exc)
                failed_directories.append(directory)
                continue
            pruned_directories += 1

    if deleted_files or pruned_directories:
        LOGGER.info(
            "Cleaned ADK artifacts: deleted_files=%s pruned_directories=%s root=%s",
            deleted_files,
            pruned_directories,
            root,
        )

    if failed_files:
        LOGGER.warning(
            "Artifact cleanup skipped %s stale ADK files that could not be deleted. Example: %s",
            len(failed_files),
            failed_files[0],
        )

    if failed_directories:
        LOGGER.warning(
            "Artifact cleanup skipped pruning %s ADK directories. Example: %s",
            len(failed_directories),
            failed_directories[0],
        )

    return deleted_files, pruned_directories


def _resolve_upload_root_for_path(path: str | Path) -> Path | None:
    candidate = Path(path).expanduser().resolve()
    root = uploads_root()
    try:
        relative_path = candidate.relative_to(root)
    except ValueError:
        return None

    if not relative_path.parts:
        return None
    return root / relative_path.parts[0]


def _upload_lifecycle_path(upload_root: Path) -> Path:
    return upload_root / UPLOAD_LIFECYCLE_FILENAME


def _load_upload_lifecycle(upload_root: Path) -> dict[str, Any]:
    lifecycle_path = _upload_lifecycle_path(upload_root)
    if not lifecycle_path.exists():
        return {}

    try:
        payload = json.loads(lifecycle_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}

    return payload if isinstance(payload, dict) else {}


def _write_upload_lifecycle(upload_root: Path, payload: dict[str, Any]) -> None:
    lifecycle_path = _upload_lifecycle_path(upload_root)
    lifecycle_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = lifecycle_path.with_suffix(lifecycle_path.suffix + ".tmp")
    temp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    temp_path.replace(lifecycle_path)


def _parse_timestamp(raw_value: Any) -> datetime | None:
    if not isinstance(raw_value, str) or not raw_value.strip():
        return None

    candidate = raw_value.strip()
    if candidate.endswith("Z"):
        candidate = candidate[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError:
        return None

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _serialize_timestamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat()


def _timestamp_from_path(path: Path) -> datetime:
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _coerce_int(value: Any) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return 0
    return parsed if parsed >= 0 else 0
