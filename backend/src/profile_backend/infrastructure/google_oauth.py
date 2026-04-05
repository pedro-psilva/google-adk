from __future__ import annotations

from typing import Any

import requests
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleAuthRequest
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

from profile_backend.infrastructure.config import settings

GOOGLE_WORKSPACE_OAUTH_SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/spreadsheets",
]


class GoogleOAuthGateway:
    def build_authorization_url(self) -> tuple[str, str]:
        flow = self._build_flow()
        authorization_url, state = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",
        )
        return authorization_url, state

    def exchange_code(self, state: str, code: str) -> dict[str, Any]:
        flow = self._build_flow(state=state)
        flow.fetch_token(code=code)
        credentials = flow.credentials
        return {
            "authorized_user_info": self._credentials_to_authorized_user_info(credentials),
            "google_user": self._fetch_google_user(credentials),
            "scopes": list(credentials.scopes or GOOGLE_WORKSPACE_OAUTH_SCOPES),
        }

    def refresh_authorized_user_info(self, authorized_user_info: dict[str, Any]) -> dict[str, Any]:
        credentials = Credentials.from_authorized_user_info(
            authorized_user_info,
            GOOGLE_WORKSPACE_OAUTH_SCOPES,
        )
        if credentials.expired and credentials.refresh_token:
            credentials.refresh(GoogleAuthRequest())
        return self._credentials_to_authorized_user_info(credentials)

    def revoke(self, token: str) -> None:
        response = requests.post(
            "https://oauth2.googleapis.com/revoke",
            params={"token": token},
            headers={"content-type": "application/x-www-form-urlencoded"},
            timeout=30,
        )
        response.raise_for_status()

    def _build_flow(self, state: str | None = None) -> Flow:
        _require_oauth_settings()
        client_config = {
            "web": {
                "client_id": settings.google_oauth_client_id,
                "client_secret": settings.google_oauth_client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [settings.google_oauth_redirect_uri],
            }
        }
        flow = Flow.from_client_config(client_config, scopes=GOOGLE_WORKSPACE_OAUTH_SCOPES, state=state)
        flow.redirect_uri = settings.google_oauth_redirect_uri
        return flow

    def _fetch_google_user(self, credentials: Credentials) -> dict[str, Any]:
        oauth2 = build("oauth2", "v2", credentials=credentials, cache_discovery=False)
        return oauth2.userinfo().get().execute()

    def _credentials_to_authorized_user_info(self, credentials: Credentials) -> dict[str, Any]:
        return {
            "client_id": settings.google_oauth_client_id,
            "client_secret": settings.google_oauth_client_secret,
            "refresh_token": credentials.refresh_token,
            "token": credentials.token,
            "token_uri": "https://oauth2.googleapis.com/token",
            "scopes": list(credentials.scopes or GOOGLE_WORKSPACE_OAUTH_SCOPES),
            "expiry": credentials.expiry.isoformat() if credentials.expiry else None,
        }


def _require_oauth_settings() -> None:
    if not settings.google_oauth_client_id or not settings.google_oauth_client_secret or not settings.google_oauth_redirect_uri:
        raise RuntimeError(
            "Missing Google OAuth configuration. Set GOOGLE_OAUTH_CLIENT_ID, GOOGLE_OAUTH_CLIENT_SECRET, and GOOGLE_OAUTH_REDIRECT_URI."
        )
