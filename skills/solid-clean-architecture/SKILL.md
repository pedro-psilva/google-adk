---
name: solid-clean-architecture
description: Use when designing or refactoring this project to follow SOLID principles, clean architecture, explicit dependency boundaries, and backend/frontend separation. This skill is for Python services, Google ADK agents, Vertex AI integrations, and any future UI that must stay decoupled from domain and application logic.
---

# Solid Clean Architecture

## When To Use

Use this skill when:

- creating new modules, services, or agents
- refactoring business logic
- deciding where Google SDK code should live
- planning APIs, workers, or UI layers
- introducing a frontend now or later

## Core Rules

- Domain code must not depend on frameworks, SDKs, HTTP clients, cloud credentials, or file formats.
- Application use cases orchestrate behavior but do not talk directly to Vertex AI, Google Docs, Google Sheets, or PDFs.
- Infrastructure adapters implement ports and are the only place where SDKs, environment variables, auth, files, or external APIs are touched.
- Interface layers such as CLI, ADK tools, HTTP routes, jobs, and frontend controllers only translate input and output.
- If the project has a UI now or may have one later, backend and frontend must be separated into distinct applications, even if they stay in one monorepo.

## SOLID Applied Here

- Single Responsibility: each use case does one job, such as `ExtractAssessmentBundle`, `AnalyzeCoverage`, `DraftReport`, or `AssembleWorkspaceOutputs`.
- Open/Closed: add new output channels like Google Docs or PDF through new adapters, not by rewriting core use cases.
- Liskov Substitution: adapters for live Vertex, mocked Vertex, or local fallback drafts should satisfy the same port contract.
- Interface Segregation: keep ports narrow, such as `DraftingGateway`, `DocumentOutputGateway`, `BundleRepository`.
- Dependency Inversion: the application layer depends on abstractions, while infrastructure implements them.

## Project Shape

Read [project-layout.md](references/project-layout.md) for the recommended structure.

For this project, prefer:

- `backend/` for domain, application, ports, API, workers, and adapters
- `frontend/` for the visual interface when introduced
- `shared/` only for neutral contracts or schemas that do not import backend or frontend frameworks

## Google Boundary Rules

Read [credential-boundaries.md](references/credential-boundaries.md) when working with auth, IAM, env vars, or Google SDKs.

- `google.adk`, `google.genai`, `googleapiclient`, and auth code belong in infrastructure adapters only.
- The domain layer should never know whether a draft came from Vertex AI or a local fallback.
- Secrets and credentials are configuration inputs, not business logic.

## Decision Rule For UI

- No UI is required for the current local MVP.
- If a UI is added, create a separate frontend immediately instead of embedding templates or browser logic into the backend.
- The backend should expose stable contracts first, then the frontend should consume them.

## Review Checklist

- Does this file import a framework when it should not?
- Does this use case depend on a concrete SDK instead of a port?
- Can this behavior be tested without Google credentials?
- If a UI is being introduced, is it isolated from backend internals?
- Is the dependency direction always toward the domain core?

## Files

- [project-layout.md](references/project-layout.md)
- [design-rules.md](references/design-rules.md)
- [credential-boundaries.md](references/credential-boundaries.md)
