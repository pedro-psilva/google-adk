from __future__ import annotations

import base64
import hashlib
from pathlib import Path
from typing import Any

from cryptography.fernet import Fernet

from profile_backend.infrastructure.config import settings


class EncryptedFileUserTokenGateway:
    def __init__(self) -> None:
        self._root = Path(settings.google_token_store_dir)
        self._root.mkdir(parents=True, exist_ok=True)

    def save(self, analyst_id: str, payload: dict[str, Any]) -> Path:
        path = self.resolve_path(analyst_id)
        encrypted = self._get_fernet().encrypt(_to_json_bytes(payload))
        path.write_bytes(encrypted)
        return path

    def load(self, analyst_id: str) -> dict[str, Any] | None:
        path = self.resolve_path(analyst_id)
        if not path.exists():
            return None
        decrypted = self._get_fernet().decrypt(path.read_bytes())
        return _from_json_bytes(decrypted)

    def delete(self, analyst_id: str) -> None:
        path = self.resolve_path(analyst_id)
        if path.exists():
            path.unlink()

    def exists(self, analyst_id: str) -> bool:
        return self.resolve_path(analyst_id).exists()

    def resolve_path(self, analyst_id: str) -> Path:
        digest = hashlib.sha256(analyst_id.encode("utf-8")).hexdigest()
        return self._root / f"{digest}.token"

    def _resolve_key(self) -> bytes:
        explicit_key = settings.google_token_encryption_key
        if explicit_key:
            return explicit_key.encode("utf-8")
        if settings.app_session_secret:
            digest = hashlib.sha256(settings.app_session_secret.encode("utf-8")).digest()
            return base64.urlsafe_b64encode(digest)
        raise RuntimeError(
            "Missing GOOGLE_TOKEN_ENCRYPTION_KEY. Set an explicit Fernet key or define APP_SESSION_SECRET."
        )

    def _get_fernet(self) -> Fernet:
        return Fernet(self._resolve_key())


def _to_json_bytes(payload: dict[str, Any]) -> bytes:
    import json

    return json.dumps(payload, ensure_ascii=False).encode("utf-8")


def _from_json_bytes(payload: bytes) -> dict[str, Any]:
    import json

    return json.loads(payload.decode("utf-8"))
