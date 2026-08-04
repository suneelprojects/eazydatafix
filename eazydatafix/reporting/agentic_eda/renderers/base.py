from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from eazydatafix.models.agentic_eda_narrative import AgenticEDANarrative
from eazydatafix.models.agentic_eda_report_result import (
    GeneratedVisualisation,
    SkippedVisualisation,
)
from eazydatafix.models.agentic_eda_result import AgenticEDAResult


@dataclass(slots=True)
class ReportRenderContext:
    """Provides deterministic workflow and artifact data to report renderers."""

    workflow: AgenticEDAResult
    generated_visualisations: list[GeneratedVisualisation]
    skipped_visualisations: list[SkippedVisualisation]
    generated_files: list[str]
    warnings: list[str]
    reproducibility_metadata: dict[str, Any]
    narrative: AgenticEDANarrative | None

    @property
    def step_outputs(self) -> dict[str, dict[str, Any]]:
        """Return successful execution outputs keyed by step name."""
        return {
            step.name: step.output
            for step in self.workflow.execution_result.executed_steps
            if step.status == "success" and step.output is not None
        }


class AgenticEDAReportRenderer(ABC):
    """Defines a deterministic text report renderer."""

    format: str
    filename: str

    @abstractmethod
    def render(
        self,
        context: ReportRenderContext,
    ) -> str:
        """Render a complete report as text."""
