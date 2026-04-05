# Design Rules

## Domain Layer

Keep only business meaning here:

- report signals
- coverage rules
- ranking rules
- report section policies
- publication policies

Avoid:

- cloud SDK imports
- environment variable access
- file parsing details
- HTTP request objects
- Google Docs request payloads

## Application Layer

This layer coordinates business actions:

- extract normalized bundle
- analyze coverage
- prepare draft request
- build publishable report

Use cases should accept and return plain objects or typed DTOs.

## Interface Layer

This layer translates external input and output:

- ADK tool wrappers
- CLI scripts
- future FastAPI routes
- job runners

This layer may call application use cases but should not contain business rules.

## Infrastructure Layer

This layer talks to real systems:

- Vertex AI
- Google ADK runtime concerns
- Google Docs API
- Google Sheets API
- local filesystem
- OCR or PDF readers

This is where retries, auth, rate limiting, and provider-specific payloads belong.

## Testing Rule

- unit tests target domain and application without real credentials
- integration tests target infrastructure adapters
- end-to-end tests target interface plus infrastructure wiring

If a behavior cannot be tested without credentials, it probably lives too close to infrastructure.
