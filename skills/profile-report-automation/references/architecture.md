# Target Architecture

## Why Google ADK + Vertex AI

Google's official documentation currently describes ADK as a flexible and modular open-source framework for developing and deploying agents, and recommends Vertex AI Agent Engine Runtime for managed deployment:

- ADK overview: https://docs.cloud.google.com/agent-builder/agent-development-kit/overview
- ADK local quickstart: https://google.github.io/adk-docs/get-started/quickstart/
- Vertex AI Agent Engine quickstart: https://docs.cloud.google.com/agent-builder/agent-engine/quickstart-adk

For local development, the ADK quickstart currently documents `pip install google-adk`.
For managed Vertex deployment, the Vertex quickstart currently documents `pip install --upgrade --quiet google-cloud-aiplatform[agent_engines,adk]>=1.112`.

Function calling on Vertex AI is a good fit for this problem because the model returns structured data describing which tool should be called and with which arguments, while the application remains responsible for executing the tool:

- Vertex AI function calling reference: https://docs.cloud.google.com/vertex-ai/generative-ai/docs/model-reference/function-calling

## Recommended System Shape

Use one ADK root agent with deterministic Python tools behind it.

### Tool Layer

Implement tools first. Example tools:

1. `extract_assessment_bundle`

- input: folder path
- output: normalized JSON with scores, categories, and template sections

2. `list_citation_candidates`

- input: normalized JSON
- output: indicators that should probably appear in the final narrative

3. `draft_report_sections`

- input: normalized JSON plus drafting rules
- output: section drafts in structured JSON

4. `assemble_local_report_exports`

- input: approved sections and chart data
- output: local `.xlsx` plus optional `.docx` and `.pdf` files for review

5. `quality_check_report`

- input: normalized JSON plus drafted text
- output: missing signals, unsupported claims, tone warnings

### Agent Layer

Use the root ADK agent mainly for orchestration:

1. intake
2. extraction
3. rule selection
4. draft generation
5. QA
6. local artifact assembly

The agent should not parse spreadsheets or PDFs directly in prompts if a Python tool can do it deterministically.

## MVP Proposal

### Phase 1

- Python extractor for the source bundle
- JSON schema for normalized data
- rule set for non-medium NEO signals
- top-2 ranking for anchors and culture
- coverage checker for overall narrative and conclusion

### Phase 2

- Vertex AI drafting prompt with strict output schema
- tone and citation QA pass
- local workbook filling and local report export for review
- local fallback draft so the downstream pipeline can be tested before cloud credentials are configured

### Phase 3

- Agent Engine deployment
- operator UI or internal web form
- audit trail with source-to-output traceability

## Data Contract For The First MVP

Suggested normalized object:

```json
{
  "person": {},
  "neopi": {
    "domains": [],
    "facets": [],
    "citation_candidates": []
  },
  "profiler": {
    "scores": [],
    "dominant_style": ""
  },
  "career_anchors": {
    "scores": [],
    "top_anchors": []
  },
  "cultural_diagnosis": {
    "scores": [],
    "top_cultures": []
  },
  "report_template": {
    "sections": {}
  }
}
```

## Guardrails

- Keep the system assistive, not autonomous, until the business accepts the failure modes.
- Always keep traceability from each paragraph back to its source indicators.
- Avoid letting the model invent interpretations outside the extracted evidence.
- Treat PDFs and spreadsheets as confidential HR inputs.
