from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    app_name: str = "profile-report-backend"
    environment: str = os.getenv("APP_ENV", "development")
    google_cloud_project: str | None = os.getenv("GOOGLE_CLOUD_PROJECT")
    google_cloud_location: str | None = os.getenv("GOOGLE_CLOUD_LOCATION")
    vertex_model: str = os.getenv("VERTEX_MODEL", "gemini-2.5-flash")
    google_oauth_client_id: str | None = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
    google_oauth_client_secret: str | None = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")
    google_oauth_redirect_uri: str | None = os.getenv("GOOGLE_OAUTH_REDIRECT_URI")
    app_session_secret: str | None = os.getenv("APP_SESSION_SECRET")
    google_token_encryption_key: str | None = os.getenv("GOOGLE_TOKEN_ENCRYPTION_KEY")
    google_token_store_dir: str = os.getenv("GOOGLE_TOKEN_STORE_DIR", "backend/var/oauth_tokens")


settings = Settings()
