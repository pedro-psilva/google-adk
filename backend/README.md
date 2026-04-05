# Backend

Production-oriented backend for the profile-report automation workflow.

## Main Interfaces

- HTTP API: `profile_backend.interfaces.http.api:app`
- ADK agent: `profile_backend.interfaces.adk.agent:root_agent`

## OAuth And Publishing

The backend now assumes Google Workspace publication through user OAuth.

Main HTTP routes:

- `GET /api/v1/auth/google/start?analyst_id=...`
- `GET /api/v1/auth/google/callback?state=...&code=...`
- `GET /api/v1/auth/google/status?analyst_id=...`
- `POST /api/v1/auth/google/revoke`
- `POST /api/v1/workspace/publish`

The OAuth token store is encrypted on disk and keyed by analyst id. In production, replace the file-based store with a managed secret or database-backed repository when appropriate.
Use `python scripts/generate_fernet_key.py` to generate a Fernet key for `GOOGLE_TOKEN_ENCRYPTION_KEY`.

## Notes

- Keep Google SDKs in infrastructure adapters only.
- Keep domain and application logic framework-agnostic.
- Treat the current root-level `profile_report_automation` package as a transitional implementation detail while behavior is migrated inward.
- Default publishing strategy should be user OAuth, so each analyst remains responsible for their own Docs/Sheets files.
- Store user refresh tokens securely on the backend and never leak them into domain logic or frontend internals.
