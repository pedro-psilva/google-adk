# Recommended Project Layout

## Default Direction

Dependencies should point inward:

1. `domain`
2. `application`
3. `interfaces`
4. `infrastructure`

The outer layers may depend on the inner layers. The inner layers must not depend on the outer layers.

## Suggested Monorepo Layout

```text
backend/
  src/
    domain/
      entities/
      value_objects/
      services/
      rules/
    application/
      use_cases/
      ports/
      dto/
    interfaces/
      adk/
      cli/
      http/
      jobs/
    infrastructure/
      google/
        vertex/
        adk/
        docs/
        sheets/
      files/
      logging/
      config/
  tests/
    unit/
    integration/

frontend/
  src/
    app/
    features/
    shared/
    api/
  tests/

shared/
  schemas/
  contracts/
```

## Mapping To This Project

The current code can evolve like this:

- `profile_report_automation/coverage.py` becomes application logic or moves into `backend/src/application/use_cases`
- `profile_report_automation/vertex_drafting.py` should split into:
  - application port
  - infrastructure Vertex adapter
- local export adapters should remain in infrastructure and be isolated from the core use cases
- `app/profile_report_agent/agent.py` belongs to an interface layer

## Backend Contracts First

If a UI exists, define backend contracts before building screens:

- bundle intake request
- coverage response
- draft preview response
- pipeline run request

The frontend should consume these contracts through HTTP or another stable API boundary.
