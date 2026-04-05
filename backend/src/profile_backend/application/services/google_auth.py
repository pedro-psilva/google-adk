from __future__ import annotations

from profile_backend.domain.models import OAuthAuthorization, OAuthConnectionStatus
from profile_backend.infrastructure.encrypted_token_store import EncryptedFileUserTokenGateway
from profile_backend.infrastructure.google_oauth import GoogleOAuthGateway


class GoogleAuthService:
    def __init__(self) -> None:
        self._oauth_gateway = GoogleOAuthGateway()
        self._token_gateway = EncryptedFileUserTokenGateway()

    def start(self, analyst_id: str) -> OAuthAuthorization:
        authorization_url, state = self._oauth_gateway.build_authorization_url()
        return OAuthAuthorization(analyst_id=analyst_id, authorization_url=authorization_url, state=state)

    def complete(self, analyst_id: str, state: str, code: str) -> dict:
        result = self._oauth_gateway.exchange_code(state, code)
        payload = {
            "analyst_id": analyst_id,
            "google_user": result["google_user"],
            "scopes": result["scopes"],
            "authorized_user_info": result["authorized_user_info"],
        }
        token_path = self._token_gateway.save(analyst_id, payload)
        return {
            "analyst_id": analyst_id,
            "connected": True,
            "google_user": result["google_user"],
            "scopes": result["scopes"],
            "token_path": str(token_path.resolve()),
        }

    def status(self, analyst_id: str) -> OAuthConnectionStatus:
        stored = self._token_gateway.load(analyst_id)
        if not stored:
            return OAuthConnectionStatus(analyst_id=analyst_id, connected=False)

        return OAuthConnectionStatus(
            analyst_id=analyst_id,
            connected=True,
            email=stored.get("google_user", {}).get("email"),
            scopes=stored.get("scopes", []),
            token_path=str(self._token_gateway.resolve_path(analyst_id).resolve()),
        )

    def revoke(self, analyst_id: str) -> dict:
        stored = self._token_gateway.load(analyst_id)
        if not stored:
            return {"analyst_id": analyst_id, "revoked": False, "reason": "not_connected"}

        token = stored.get("authorized_user_info", {}).get("token")
        if token:
            self._oauth_gateway.revoke(token)
        self._token_gateway.delete(analyst_id)
        return {"analyst_id": analyst_id, "revoked": True}
