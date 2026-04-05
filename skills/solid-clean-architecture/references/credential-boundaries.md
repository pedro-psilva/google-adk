# Credential Boundaries

## Principle

Credentials are infrastructure concerns.

Do not read environment variables, service-account files, OAuth tokens, or cloud project configuration from domain or application code.

## What Stays Outside The Core

- `GOOGLE_CLOUD_PROJECT`
- `GOOGLE_CLOUD_LOCATION`
- `GOOGLE_APPLICATION_CREDENTIALS`
- OAuth client secrets
- access tokens
- Docs or Sheets scopes
- service account impersonation details

## Recommended Flow

1. Load configuration in infrastructure.
2. Build provider clients in infrastructure.
3. Inject adapters into application use cases through ports.
4. Keep the rest of the system unaware of provider-specific auth details.

## UI Rule

If the frontend needs Google login or document selection:

- the frontend handles user auth and consent UX
- the backend handles server-side execution and provider adapters
- tokens and scopes must not leak into domain logic

For this project, prefer user OAuth over a shared service account when publishing analysis documents, so ownership stays with the responsible analyst.

## Future Backend Interfaces

Even if the first UI is small, the backend should remain able to serve:

- web frontend
- internal admin frontend
- CLI
- batch jobs
- ADK agent tools

This is another reason to keep backend and frontend separate.
