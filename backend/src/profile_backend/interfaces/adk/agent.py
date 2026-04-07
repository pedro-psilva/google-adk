from __future__ import annotations

from profile_backend.infrastructure.adk_workflow import (
    AdkAnalysisRunnerService,
    AdkPipelineRunnerService,
    root_agent,
)

adk_analysis_runner = AdkAnalysisRunnerService()
adk_pipeline_runner = AdkPipelineRunnerService()

__all__ = ["adk_analysis_runner", "adk_pipeline_runner", "root_agent"]
