# Backend

Production-oriented backend for the profile-report automation workflow.

## Main Interfaces

- HTTP API: `profile_backend.interfaces.http.api:app`
- ADK agent: `profile_backend.interfaces.adk.agent:root_agent`

## Main Flow

The active flow is file-based:

Main HTTP routes:

- `POST /api/v1/intake/upload`
- `POST /api/v1/bundles/load`
- `POST /api/v1/reports/coverage`
- `POST /api/v1/reports/draft-preview`
- `POST /api/v1/pipeline/run`
- `GET /api/v1/files/download`

The analysis routes now execute through deterministic ADK workflows:

- `POST /api/v1/bundles/load`
- `POST /api/v1/reports/coverage`
- `POST /api/v1/reports/draft-preview`
- `POST /api/v1/pipeline/run`

`POST /api/v1/pipeline/run` validates the request, runs the deterministic pipeline, records ADK artifacts for the request and response, and then returns the local file outputs.

`POST /api/v1/bundles/load`, `POST /api/v1/reports/coverage`, and `POST /api/v1/reports/draft-preview` run through lightweight ADK workflows without persisting session artifacts to disk.

## Notes

- Keep Vertex SDK usage in infrastructure adapters only.
- Keep domain and application logic framework-agnostic.
- Treat the current root-level `profile_report_automation` package as a transitional implementation detail while behavior is migrated inward.
- The current delivery target is the generated local `.xlsx` file, with optional local `.docx` and `.pdf` artifacts.
- The current ADK root agent is a deterministic workflow orchestrator rather than a chat-first agent.
