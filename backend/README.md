# Backend

Production-oriented backend for the profile-report automation workflow.

## Main Interfaces

- HTTP API: `profile_backend.interfaces.http.api:app`
- ADK agent: `profile_backend.interfaces.adk.agent:root_agent`
- Docker image: build context `backend/`

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
- The current delivery target for this branch is the generated local `.docx` plus `.pdf` artifacts, without Excel as a runtime dependency.
- The current ADK root agent is a deterministic workflow orchestrator rather than a chat-first agent.
- The runtime writes uploads, normalized bundles, ADK session artifacts, and final files only under `ARTIFACTS_ROOT`.
- The backend Docker image is self-contained inside the `backend/` directory, including the report-generation runtime package.
- Upload roots under `ARTIFACTS_ROOT/uploads` are now lifecycle-tracked and cleaned automatically after delivery or after a stale TTL.
