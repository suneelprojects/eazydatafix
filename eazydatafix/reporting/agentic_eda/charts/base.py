from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd

from eazydatafix.models.agentic_eda_report_result import (
    GeneratedVisualisation,
    SkippedVisualisation,
)
from eazydatafix.models.agentic_eda_result import (
    AgenticEDAResult,
    VisualisationRecommendation,
)


class ChartDataUnavailableError(ValueError):
    """Raised when a recommended chart cannot be generated honestly."""


@dataclass(slots=True)
class ChartContext:
    """Provides immutable workflow outputs and an optional copied DataFrame."""

    workflow: AgenticEDAResult
    dataframe: pd.DataFrame | None
    step_outputs: dict[str, dict[str, Any]]


@dataclass(slots=True)
class ChartGenerationResult:
    """Collects generated, skipped, and failed chart outcomes."""

    generated: list[GeneratedVisualisation] = field(default_factory=list)
    skipped: list[SkippedVisualisation] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class ChartHandler(ABC):
    """Defines a deterministic handler for one visualisation recommendation."""

    type: str

    @abstractmethod
    def generate(
        self,
        recommendation: VisualisationRecommendation,
        context: ChartContext,
        output_path: Path,
    ) -> None:
        """Generate one PNG artifact or raise ChartDataUnavailableError."""

    @staticmethod
    def save_figure(
        figure: Any,
        output_path: Path,
    ) -> None:
        """Save a PNG atomically and always close its matplotlib figure."""
        import matplotlib

        matplotlib.use("Agg", force=True)
        import matplotlib.pyplot as plt

        temporary_path = output_path.with_name(f".{output_path.stem}.tmp.png")

        try:
            figure.savefig(
                temporary_path,
                format="png",
                bbox_inches="tight",
                dpi=120,
                metadata={"Software": "EazyDataFix"},
            )
            temporary_path.replace(output_path)
        finally:
            plt.close(figure)

            if temporary_path.exists():
                temporary_path.unlink()

    @staticmethod
    def pyplot() -> Any:
        """Return matplotlib pyplot configured for non-interactive rendering."""
        import matplotlib

        matplotlib.use("Agg", force=True)
        import matplotlib.pyplot as plt

        return plt
