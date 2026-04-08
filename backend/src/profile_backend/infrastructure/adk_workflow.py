from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable
from uuid import uuid4

from google.adk.agents.base_agent import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.agents.sequential_agent import SequentialAgent
from google.adk.artifacts import FileArtifactService
from google.adk.events import Event, EventActions
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from profile_backend.application.services.report_pipeline import ReportPipelineService
from profile_backend.domain.models import PipelineRequest

ADK_APP_NAME = "profile-report-pipeline"
LOAD_BUNDLE_APP_NAME = "profile-report-load-bundle"
COVERAGE_APP_NAME = "profile-report-coverage"
DRAFT_PREVIEW_APP_NAME = "profile-report-draft-preview"
ADK_USER_ID = "profile-report-api"

PIPELINE_REQUEST_KEY = "app:pipeline_request"
PIPELINE_RESULT_KEY = "app:pipeline_result"
PIPELINE_RESPONSE_KEY = "app:pipeline_response"
PIPELINE_STATUS_KEY = "app:pipeline_status"
PIPELINE_ERROR_KEY = "app:pipeline_error"
PIPELINE_ARTIFACTS_KEY = "app:artifact_versions"

LOAD_BUNDLE_REQUEST_KEY = "app:load_bundle_request"
LOAD_BUNDLE_RESPONSE_KEY = "app:load_bundle_response"

COVERAGE_REQUEST_KEY = "app:coverage_request"
COVERAGE_RESPONSE_KEY = "app:coverage_response"

DRAFT_PREVIEW_REQUEST_KEY = "app:draft_preview_request"
DRAFT_PREVIEW_RESPONSE_KEY = "app:draft_preview_response"

ADK_ARTIFACTS_ROOT = Path("artifacts") / "adk-sessions"
PIPELINE_ARTIFACT_SERVICE = FileArtifactService(ADK_ARTIFACTS_ROOT)


@dataclass(frozen=True)
class StepExecution:
    message: str | None = None
    state_delta: dict[str, object] = field(default_factory=dict)
    artifacts: dict[str, types.Part] = field(default_factory=dict)


class DeterministicStepAgent(BaseAgent):
    step_handler: Callable[[InvocationContext], StepExecution]

    async def _run_async_impl(self, ctx: InvocationContext):
        existing_error = ctx.session.state.get(PIPELINE_ERROR_KEY)
        if isinstance(existing_error, dict):
            return

        try:
            execution = self.step_handler(ctx)
        except Exception as exc:
            error_payload = _build_error_payload(self.name, exc)
            yield Event(
                invocation_id=ctx.invocation_id,
                author=self.name,
                branch=ctx.branch,
                content=_build_content(error_payload["message"]),
                actions=EventActions(
                    state_delta={
                        PIPELINE_ERROR_KEY: error_payload,
                        PIPELINE_STATUS_KEY: "failed",
                    }
                ),
            )
            return

        artifact_delta = await _save_step_artifacts(ctx, execution.artifacts)
        state_delta = dict(execution.state_delta)
        if artifact_delta:
            merged_versions = dict(ctx.session.state.get(PIPELINE_ARTIFACTS_KEY, {}))
            merged_versions.update(artifact_delta)
            state_delta[PIPELINE_ARTIFACTS_KEY] = merged_versions
        content = _build_content(execution.message) if execution.message else None
        yield Event(
            invocation_id=ctx.invocation_id,
            author=self.name,
            branch=ctx.branch,
            content=content,
            actions=EventActions(
                state_delta=state_delta,
                artifact_delta=artifact_delta,
            ),
        )

    async def _run_live_impl(self, ctx: InvocationContext):
        async for event in self._run_async_impl(ctx):
            yield event


def _build_content(message: str) -> types.Content:
    return types.Content(role="model", parts=[types.Part(text=message)])


def _request_to_dict(request: PipelineRequest) -> dict[str, str]:
    return {
        "bundle_input": request.bundle_input,
        "output_dir": request.output_dir,
        "draft_mode": request.draft_mode,
    }


def _request_from_context(ctx: InvocationContext) -> PipelineRequest:
    payload = ctx.session.state.get(PIPELINE_REQUEST_KEY)
    if not isinstance(payload, dict):
        raise ValueError("Pipeline request not found in ADK session state.")

    return PipelineRequest(
        bundle_input=str(payload["bundle_input"]),
        output_dir=str(payload["output_dir"]),
        draft_mode=str(payload.get("draft_mode", "live")),  # type: ignore[arg-type]
    )


def _serialize_pipeline_result(result: Any) -> dict[str, Any]:
    return {
        "status": result.status,
        "bundle_path": result.bundle_path,
        "output_dir": result.output_dir,
        "artifacts": {
            "bundle_path": result.artifacts.bundle_path,
            "coverage_report": result.artifacts.coverage_report,
            "vertex_request_preview": result.artifacts.vertex_request_preview,
            "draft_output": result.artifacts.draft_output,
            "local_report_xlsx": result.artifacts.local_report_xlsx,
            "local_report_docx": result.artifacts.local_report_docx,
            "local_report_pdf": result.artifacts.local_report_pdf,
            "live_draft": result.artifacts.live_draft,
        },
        "used_live_vertex": result.used_live_vertex,
        "notes": result.notes,
    }


def _bundle_path_request(bundle_path: str) -> dict[str, str]:
    return {"bundle_path": bundle_path}


def _build_error_payload(step_name: str, exc: Exception) -> dict[str, str]:
    detail = str(exc).strip() or exc.__class__.__name__
    return {
        "step": step_name,
        "type": exc.__class__.__name__,
        "message": f"Falha na etapa {step_name}: {detail}",
    }


def _bundle_path_from_context(ctx: InvocationContext, request_key: str, missing_message: str) -> str:
    payload = ctx.session.state.get(request_key)
    if not isinstance(payload, dict) or "bundle_path" not in payload:
        raise ValueError(missing_message)
    bundle_path = str(payload["bundle_path"])
    resolved = Path(bundle_path).expanduser()
    if not resolved.exists():
        raise FileNotFoundError(f"Bundle path not found: {resolved}")
    return bundle_path


def _validate_request_step(ctx: InvocationContext) -> StepExecution:
    request = _request_from_context(ctx)
    bundle_input = Path(request.bundle_input).expanduser()
    if not bundle_input.exists():
        raise FileNotFoundError(f"Bundle input not found: {bundle_input}")

    output_dir = Path(request.output_dir).expanduser()
    output_dir.mkdir(parents=True, exist_ok=True)

    state_delta = {
        PIPELINE_REQUEST_KEY: _request_to_dict(request),
        PIPELINE_STATUS_KEY: "validated",
    }
    message = f"Pedido validado para {bundle_input.name}."
    return StepExecution(message=message, state_delta=state_delta)


def _execute_pipeline_step(ctx: InvocationContext) -> StepExecution:
    request = _request_from_context(ctx)
    result = ReportPipelineService().run(request)
    serialized = _serialize_pipeline_result(result)
    state_delta = {
        PIPELINE_RESULT_KEY: serialized,
        PIPELINE_STATUS_KEY: "executed",
    }
    message = f"Pipeline executado com status {result.status}."
    return StepExecution(message=message, state_delta=state_delta)


def _capture_artifacts_step(ctx: InvocationContext) -> StepExecution:
    request = _request_from_context(ctx)
    result = ctx.session.state.get(PIPELINE_RESULT_KEY)
    if not isinstance(result, dict):
        raise ValueError("Pipeline result missing from ADK session state.")

    artifacts = {
        "pipeline-request.json": types.Part(text=json.dumps(_request_to_dict(request), ensure_ascii=False, indent=2)),
        "pipeline-result.json": types.Part(text=json.dumps(result, ensure_ascii=False, indent=2)),
    }
    state_delta = {
        PIPELINE_STATUS_KEY: "artifacts_captured",
    }
    return StepExecution(
        message="Artefatos da execucao registrados na sessao ADK.",
        state_delta=state_delta,
        artifacts=artifacts,
    )


def _build_response_step(ctx: InvocationContext) -> StepExecution:
    result = ctx.session.state.get(PIPELINE_RESULT_KEY)
    if not isinstance(result, dict):
        raise ValueError("Pipeline result missing from ADK session state.")

    artifact_versions = ctx.session.state.get(PIPELINE_ARTIFACTS_KEY, {})
    if not isinstance(artifact_versions, dict):
        artifact_versions = {}

    response = {
        **result,
        "adk": {
            "app_name": ADK_APP_NAME,
            "session_id": ctx.session.id,
            "user_id": ctx.session.user_id,
            "artifact_versions": artifact_versions,
        },
    }
    return StepExecution(
        message="Resposta final preparada pelo workflow ADK.",
        state_delta={
            PIPELINE_STATUS_KEY: "completed",
            PIPELINE_RESPONSE_KEY: response,
        },
    )


def _load_bundle_step(ctx: InvocationContext) -> StepExecution:
    bundle_path = _bundle_path_from_context(
        ctx,
        LOAD_BUNDLE_REQUEST_KEY,
        "Bundle path not found in ADK session state for load operation.",
    )
    payload = ReportPipelineService().load_bundle(bundle_path)
    return StepExecution(
        message="Bundle carregado pela operacao ADK.",
        state_delta={LOAD_BUNDLE_RESPONSE_KEY: payload},
    )


def _coverage_step(ctx: InvocationContext) -> StepExecution:
    bundle_path = _bundle_path_from_context(
        ctx,
        COVERAGE_REQUEST_KEY,
        "Bundle path not found in ADK session state for coverage operation.",
    )
    payload = ReportPipelineService().analyze_coverage(bundle_path)
    return StepExecution(
        message="Cobertura analisada pela operacao ADK.",
        state_delta={COVERAGE_RESPONSE_KEY: payload},
    )


def _draft_preview_step(ctx: InvocationContext) -> StepExecution:
    bundle_path = _bundle_path_from_context(
        ctx,
        DRAFT_PREVIEW_REQUEST_KEY,
        "Bundle path not found in ADK session state for draft-preview operation.",
    )
    payload = ReportPipelineService().preview_draft(bundle_path)
    return StepExecution(
        message="Preview de rascunho preparado pela operacao ADK.",
        state_delta={DRAFT_PREVIEW_RESPONSE_KEY: payload},
    )


async def _save_step_artifacts(ctx: InvocationContext, artifacts: dict[str, types.Part]) -> dict[str, int]:
    if not artifacts or ctx.artifact_service is None:
        return {}

    saved_versions: dict[str, int] = {}
    for filename, artifact in artifacts.items():
        version = await ctx.artifact_service.save_artifact(
            app_name=ctx.app_name,
            user_id=ctx.user_id,
            session_id=ctx.session.id,
            filename=filename,
            artifact=artifact,
        )
        saved_versions[filename] = version

    return saved_versions


validate_request_agent = DeterministicStepAgent(
    name="validate_request_agent",
    description="Validate pipeline inputs and prepare the output directory.",
    step_handler=_validate_request_step,
)

execute_pipeline_agent = DeterministicStepAgent(
    name="execute_pipeline_agent",
    description="Run the deterministic profile-report pipeline.",
    step_handler=_execute_pipeline_step,
)

capture_artifacts_agent = DeterministicStepAgent(
    name="capture_artifacts_agent",
    description="Register request and response summaries as ADK artifacts.",
    step_handler=_capture_artifacts_step,
)

build_response_agent = DeterministicStepAgent(
    name="build_response_agent",
    description="Build the final API response from the ADK session state.",
    step_handler=_build_response_step,
)


root_agent = SequentialAgent(
    name="profile_report_workflow",
    description="Run the profile-report pipeline as a deterministic ADK workflow.",
    sub_agents=[
        validate_request_agent,
        execute_pipeline_agent,
        capture_artifacts_agent,
        build_response_agent,
    ],
)

load_bundle_root_agent = SequentialAgent(
    name="load_bundle_workflow",
    description="Load a JSON artifact through a deterministic ADK workflow.",
    sub_agents=[
        DeterministicStepAgent(
            name="load_bundle_agent",
            description="Load the requested JSON payload.",
            step_handler=_load_bundle_step,
        )
    ],
)

coverage_root_agent = SequentialAgent(
    name="coverage_workflow",
    description="Analyze coverage through a deterministic ADK workflow.",
    sub_agents=[
        DeterministicStepAgent(
            name="coverage_agent",
            description="Analyze required-signal coverage for a normalized bundle.",
            step_handler=_coverage_step,
        )
    ],
)

draft_preview_root_agent = SequentialAgent(
    name="draft_preview_workflow",
    description="Prepare the draft preview through a deterministic ADK workflow.",
    sub_agents=[
        DeterministicStepAgent(
            name="draft_preview_agent",
            description="Prepare the Vertex preview payload for a normalized bundle.",
            step_handler=_draft_preview_step,
        )
    ],
)


class _AdkJsonOperationRunner:
    def __init__(self, *, app_name: str, agent: BaseAgent, response_key: str) -> None:
        self._app_name = app_name
        self._agent = agent
        self._response_key = response_key

    def run(self, *, state: dict[str, Any], message: str) -> dict[str, Any]:
        session_id = uuid4().hex
        session_service = InMemorySessionService()
        runner = Runner(
            app_name=self._app_name,
            agent=self._agent,
            session_service=session_service,
        )
        asyncio.run(
            session_service.create_session(
                app_name=self._app_name,
                user_id=ADK_USER_ID,
                session_id=session_id,
                state=state,
            )
        )

        list(
            runner.run(
                user_id=ADK_USER_ID,
                session_id=session_id,
                new_message=_build_content(message),
            )
        )

        session = asyncio.run(
            session_service.get_session(
                app_name=self._app_name,
                user_id=ADK_USER_ID,
                session_id=session_id,
            )
        )
        if session is None:
            raise RuntimeError(f"ADK session not found after operation {self._app_name}.")

        response = session.state.get(self._response_key)
        if not isinstance(response, dict):
            error_payload = session.state.get(PIPELINE_ERROR_KEY)
            if isinstance(error_payload, dict) and error_payload.get("message"):
                raise RuntimeError(str(error_payload["message"]))
            raise RuntimeError(f"ADK operation {self._app_name} did not produce a JSON response.")
        return response


class AdkPipelineRunnerService:
    def __init__(self) -> None:
        self._artifact_service = PIPELINE_ARTIFACT_SERVICE

    def run(self, request: PipelineRequest) -> dict[str, Any]:
        session_id = uuid4().hex
        session_service = InMemorySessionService()
        runner = Runner(
            app_name=ADK_APP_NAME,
            agent=root_agent,
            session_service=session_service,
            artifact_service=self._artifact_service,
        )
        asyncio.run(
            session_service.create_session(
                app_name=ADK_APP_NAME,
                user_id=ADK_USER_ID,
                session_id=session_id,
                state={PIPELINE_REQUEST_KEY: _request_to_dict(request)},
            )
        )

        events = list(
            runner.run(
                user_id=ADK_USER_ID,
                session_id=session_id,
                new_message=_build_content("Execute the current profile-report pipeline request."),
            )
        )

        session = asyncio.run(
            session_service.get_session(
                app_name=ADK_APP_NAME,
                user_id=ADK_USER_ID,
                session_id=session_id,
            )
        )
        if session is None:
            raise RuntimeError("ADK session not found after pipeline execution.")

        response = session.state.get(PIPELINE_RESPONSE_KEY)
        if not isinstance(response, dict):
            error_payload = session.state.get(PIPELINE_ERROR_KEY)
            if isinstance(error_payload, dict) and error_payload.get("message"):
                raise RuntimeError(str(error_payload["message"]))
            raise RuntimeError("ADK workflow did not produce a final pipeline response.")

        response["adk"]["events"] = _summarize_events(events)
        return response


class AdkAnalysisRunnerService:
    def __init__(self) -> None:
        self._load_bundle_runner = _AdkJsonOperationRunner(
            app_name=LOAD_BUNDLE_APP_NAME,
            agent=load_bundle_root_agent,
            response_key=LOAD_BUNDLE_RESPONSE_KEY,
        )
        self._coverage_runner = _AdkJsonOperationRunner(
            app_name=COVERAGE_APP_NAME,
            agent=coverage_root_agent,
            response_key=COVERAGE_RESPONSE_KEY,
        )
        self._draft_preview_runner = _AdkJsonOperationRunner(
            app_name=DRAFT_PREVIEW_APP_NAME,
            agent=draft_preview_root_agent,
            response_key=DRAFT_PREVIEW_RESPONSE_KEY,
        )

    def load_bundle(self, bundle_path: str) -> dict[str, Any]:
        return self._load_bundle_runner.run(
            state={LOAD_BUNDLE_REQUEST_KEY: _bundle_path_request(bundle_path)},
            message="Load the requested JSON artifact.",
        )

    def analyze_coverage(self, bundle_path: str) -> dict[str, Any]:
        return self._coverage_runner.run(
            state={COVERAGE_REQUEST_KEY: _bundle_path_request(bundle_path)},
            message="Analyze the coverage for the requested bundle.",
        )

    def preview_draft(self, bundle_path: str) -> dict[str, Any]:
        return self._draft_preview_runner.run(
            state={DRAFT_PREVIEW_REQUEST_KEY: _bundle_path_request(bundle_path)},
            message="Prepare the draft preview for the requested bundle.",
        )


def _summarize_events(events: list[Event]) -> list[dict[str, str]]:
    summary: list[dict[str, str]] = []
    for event in events:
        if event.author == "user":
            continue
        text_parts = []
        if event.content and event.content.parts:
            for part in event.content.parts:
                if getattr(part, "text", None):
                    text_parts.append(str(part.text))
        summary.append(
            {
                "author": event.author,
                "message": " ".join(text_parts).strip(),
            }
        )
    return summary
