from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

DraftMode = Literal["preview", "template", "live"]


@dataclass(frozen=True)
class PipelineRequest:
    bundle_input: str
    output_dir: str
    draft_mode: DraftMode = "preview"


@dataclass
class PipelineArtifacts:
    bundle_path: str
    coverage_report: str
    vertex_request_preview: str
    draft_output: str
    local_report_xlsx: str | None = None
    local_report_docx: str | None = None
    local_report_pdf: str | None = None
    live_draft: str | None = None


@dataclass
class PipelineResult:
    status: str
    bundle_path: str
    output_dir: str
    artifacts: PipelineArtifacts
    used_live_vertex: bool = False
    notes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ResolvedBundle:
    bundle: dict[str, Any]
    bundle_path: Path
