---
name: profile-report-automation
description: Use when automating organizational profile reports built from NEOPI-R, Profiler, career anchors, cultural diagnosis, and Excel/PDF templates. This skill helps extract structured data, separate deterministic rules from generative writing, and design human-in-the-loop flows with Python, Google ADK, and Vertex AI.
---

# Profile Report Automation

## When To Use

Use this skill when the task involves one or more of the following inputs:

- NEOPI-R PDF reports
- Profiler behavioral PDFs
- Career anchors spreadsheets
- Cultural diagnosis spreadsheets
- Final profile report spreadsheets or PDFs

It is especially useful when the goal is to reduce manual work in drafting, checking, or assembling the final report.

## Workflow

1. Run [extract_assessment_bundle.py](scripts/extract_assessment_bundle.py) on a folder that contains the source artifacts.
2. Run [check_report_coverage.py](/C:/Users/iebt/OneDrive/Desktop/Workspace/google-adk/scripts/check_report_coverage.py) to compare required signals against the current narrative and conclusion.
3. Run [prepare_vertex_draft.py](/C:/Users/iebt/OneDrive/Desktop/Workspace/google-adk/scripts/prepare_vertex_draft.py) to generate a Vertex request preview, a local fallback draft, or a live draft when credentials are available.
4. Run [run_backend_pipeline.py](/C:/Users/iebt/OneDrive/Desktop/Workspace/google-adk/scripts/run_backend_pipeline.py) to produce the full local artifact set, including the final `.xlsx` and optional `.docx` or `.pdf` exports.
5. Read [discovery.md](references/discovery.md) when you need the current manual process, sample-specific findings, and automation opportunities.
6. Read [architecture.md](references/architecture.md) when you need the target design for Python, Google ADK, and Vertex AI.
7. Split the solution into three layers:
   - Deterministic extraction: file discovery, score parsing, rankings, and chart data.
   - Rule engine and QA: decide what must be cited, ignore medium NEO results by default, and flag structural inconsistencies.
   - Generative writing: rewrite or synthesize text in a respectful corporate tone.

## Rule Priorities

- Prefer structured extraction and business rules before using an LLM.
- For NEOPI-R, treat medium scores as optional by default and prioritize low, high, very low, and very high indicators.
- Keep a human reviewer in the loop before delivery because the report remains interpretive and sensitive.
- Avoid definitive or clinical language in generated text. Use wording such as "indicates", "sugere", or "ponto de atenção".
- When the input has fixed categories, such as anchors or culture types, use lookup tables instead of free-text extraction.

## Implementation Notes

- The extractor script is the local source of truth for early prototyping.
- In production, use ADK to orchestrate the steps and call deterministic Python tools.
- The local ADK entry point lives at [agent.py](/C:/Users/iebt/OneDrive/Desktop/Workspace/google-adk/app/profile_report_agent/agent.py).
- Use Vertex AI structured tool use for:
  - requesting normalized JSON from tools
  - selecting which section templates to fill
  - rewriting text without dropping mandatory indicators
- Treat the local `.xlsx` export as the main delivery target. Keep optional `.docx` or `.pdf` outputs only as supporting artifacts.

## Quick Checks

- Are all expected files present in the intake folder?
- Which steps are deterministic and which are interpretive?
- Which indicators are citation candidates and which can stay implicit?
- Is the final text covering the relevant non-medium signals?
- Are the narrative and charts coming from the same normalized dataset?

## Files

- [extract_assessment_bundle.py](scripts/extract_assessment_bundle.py)
- [check_report_coverage.py](/C:/Users/iebt/OneDrive/Desktop/Workspace/google-adk/scripts/check_report_coverage.py)
- [prepare_vertex_draft.py](/C:/Users/iebt/OneDrive/Desktop/Workspace/google-adk/scripts/prepare_vertex_draft.py)
- [run_backend_pipeline.py](/C:/Users/iebt/OneDrive/Desktop/Workspace/google-adk/scripts/run_backend_pipeline.py)
- [discovery.md](references/discovery.md)
- [architecture.md](references/architecture.md)
