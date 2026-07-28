from collections.abc import Iterable
from pathlib import Path

from eazydatafix.models.agentic_eda_report_result import (
    GeneratedVisualisation,
    SkippedVisualisation,
)
from eazydatafix.models.agentic_eda_result import AgenticEDAResult
from eazydatafix.reporting.agentic_eda.charts.base import (
    ChartContext,
    ChartDataUnavailableError,
    ChartGenerationResult,
    ChartHandler,
)
from eazydatafix.reporting.agentic_eda.charts.handlers import (
    BoxPlotChartHandler,
    ClassDistributionChartHandler,
    CorrelationHeatmapHandler,
    DatetimeFrequencyChartHandler,
    DistributionBarChartHandler,
    HistogramChartHandler,
    MissingValueChartHandler,
)
from eazydatafix.reporting.agentic_eda.paths import (
    filename_slug,
    safe_artifact_path,
)


class ChartRegistry:
    """Routes visualisation recommendations to deterministic PNG handlers."""

    def __init__(
        self,
        handlers: Iterable[ChartHandler] | None = None,
    ) -> None:
        """
        Initialise the registry with built-in or custom chart handlers.

        Args:
            handlers: Optional iterable replacing the built-in handler set.

        Raises:
            ValueError: If multiple handlers register the same chart type.
        """
        selected = list(handlers) if handlers is not None else default_chart_handlers()
        self._handlers: dict[str, ChartHandler] = {}

        for handler in selected:
            if handler.type in self._handlers:
                raise ValueError(f"Duplicate chart handler registered for '{handler.type}'.")

            self._handlers[handler.type] = handler

    def generate(
        self,
        workflow: AgenticEDAResult,
        context: ChartContext,
        output_directory: Path,
    ) -> ChartGenerationResult:
        """
        Generate only visualisations recommended by the orchestrator.

        Args:
            workflow: Existing deterministic Agentic EDA workflow.
            context: Structured execution outputs and optional validated data.
            output_directory: Validated report output directory.

        Returns:
            Generated and skipped chart records plus non-fatal warnings.
        """
        result = ChartGenerationResult()
        visualisation_directory = safe_artifact_path(output_directory, "visualisations")
        visualisation_directory.mkdir(parents=True, exist_ok=True)

        for index, recommendation in enumerate(workflow.recommended_visualisations, start=1):
            relative_path = self._relative_path(
                index, recommendation.type, recommendation.target_columns
            )
            output_path = safe_artifact_path(output_directory, relative_path)
            handler = self._handlers.get(recommendation.type)

            if handler is None:
                result.skipped.append(
                    SkippedVisualisation(
                        type=recommendation.type,
                        target_columns=list(recommendation.target_columns),
                        reason="No deterministic chart handler is registered for this type.",
                        source_step=recommendation.source_step,
                    )
                )
                continue

            try:
                handler.generate(recommendation, context, output_path)
            except ChartDataUnavailableError as exc:
                result.skipped.append(
                    SkippedVisualisation(
                        type=recommendation.type,
                        target_columns=list(recommendation.target_columns),
                        reason=str(exc),
                        source_step=recommendation.source_step,
                    )
                )
            except Exception as exc:
                reason = f"{type(exc).__name__}: {exc}"
                result.skipped.append(
                    SkippedVisualisation(
                        type=recommendation.type,
                        target_columns=list(recommendation.target_columns),
                        reason=reason,
                        source_step=recommendation.source_step,
                    )
                )
                result.warnings.append(f"Visualisation '{recommendation.type}' failed: {reason}")
            else:
                result.generated.append(
                    GeneratedVisualisation(
                        type=recommendation.type,
                        target_columns=list(recommendation.target_columns),
                        path=relative_path.as_posix(),
                        source_step=recommendation.source_step,
                    )
                )

        return result

    @staticmethod
    def _relative_path(
        index: int,
        chart_type: str,
        columns: list[str],
    ) -> Path:
        column_part = "-".join(filename_slug(column) for column in columns) or "dataset"
        column_part = column_part[:96].rstrip("-") or "dataset"
        filename = f"{index:02d}-{filename_slug(chart_type)}-{column_part}.png"
        return Path("visualisations") / filename


def default_chart_handlers() -> list[ChartHandler]:
    """Build the deterministic chart handlers supported by report export."""
    return [
        MissingValueChartHandler(),
        DistributionBarChartHandler(),
        ClassDistributionChartHandler(),
        HistogramChartHandler(),
        BoxPlotChartHandler(),
        CorrelationHeatmapHandler(),
        DatetimeFrequencyChartHandler(),
    ]
