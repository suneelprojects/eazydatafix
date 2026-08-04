from collections.abc import Iterable, Sequence
from pathlib import Path

import pandas as pd

from eazydatafix.assessment.eda_validation import (
    load_eda_frame,
    validate_eda_result,
)
from eazydatafix.models.agentic_eda_narrative import AgenticEDANarrative
from eazydatafix.models.agentic_eda_report_result import AgenticEDAReportResult
from eazydatafix.models.agentic_eda_result import AgenticEDAResult
from eazydatafix.narratives.validation import workflow_fingerprint
from eazydatafix.reporting.agentic_eda.charts import ChartContext, ChartRegistry
from eazydatafix.reporting.agentic_eda.paths import safe_artifact_path
from eazydatafix.reporting.agentic_eda.renderers import (
    AgenticEDAHTMLRenderer,
    AgenticEDAJSONRenderer,
    AgenticEDAMarkdownRenderer,
    AgenticEDAReportRenderer,
    ReportRenderContext,
)

_DEFAULT_FORMATS = ("html", "json")
_FORMAT_ORDER = ("html", "json", "markdown")


class AgenticEDAReportExporter:
    """Coordinates deterministic Agentic EDA report and chart generation."""

    def __init__(
        self,
        renderers: Iterable[AgenticEDAReportRenderer] | None = None,
        chart_registry: ChartRegistry | None = None,
    ) -> None:
        """
        Initialise the exporter with built-in or compatible custom components.

        Args:
            renderers: Optional iterable replacing the built-in text renderers.
            chart_registry: Optional chart handler registry.

        Raises:
            ValueError: If multiple renderers use the same format.
        """
        selected_renderers = (
            list(renderers) if renderers is not None else default_report_renderers()
        )
        self._renderers: dict[str, AgenticEDAReportRenderer] = {}

        for renderer in selected_renderers:
            if renderer.format in self._renderers:
                raise ValueError(f"Duplicate Agentic EDA report renderer for '{renderer.format}'.")

            self._renderers[renderer.format] = renderer

        self._chart_registry = chart_registry or ChartRegistry()

    def export(
        self,
        workflow: AgenticEDAResult,
        dataset: str | Path | pd.DataFrame | None = None,
        output_dir: str | Path = "eazydatafix-report",
        formats: Sequence[str] | None = None,
        narrative: AgenticEDANarrative | None = None,
    ) -> AgenticEDAReportResult:
        """
        Export deterministic human-readable and JSON-ready report artifacts.

        Args:
            workflow: Existing result returned by ``run_agentic_eda``.
            dataset: Optional matching dataset used only for raw-data charts.
            output_dir: Dedicated output directory for all generated artifacts.
            formats: Optional subset of ``html``, ``json``, and ``markdown``.

        Returns:
            Structured report artifact metadata.

        Raises:
            TypeError: If workflow, dataset, output_dir, or formats are invalid.
            ValueError: If the output directory, formats, or supplied dataset are invalid.
        """
        if not isinstance(workflow, AgenticEDAResult):
            raise TypeError("export_agentic_eda_report() workflow must be an AgenticEDAResult.")

        if narrative is not None and not isinstance(narrative, AgenticEDANarrative):
            raise TypeError("narrative must be an AgenticEDANarrative or None.")

        if narrative is not None and narrative.workflow_fingerprint != workflow_fingerprint(
            workflow
        ):
            raise ValueError(
                "narrative was generated for a different or modified Agentic EDA workflow."
            )

        selected_formats = self._normalise_formats(formats)
        dataframe = self._validated_dataframe(dataset, workflow)
        output_directory = self._prepare_output_directory(output_dir)
        step_outputs = {
            step.name: step.output
            for step in workflow.execution_result.executed_steps
            if step.status == "success" and step.output is not None
        }
        chart_result = self._chart_registry.generate(
            workflow=workflow,
            context=ChartContext(
                workflow=workflow,
                dataframe=dataframe,
                step_outputs=step_outputs,
            ),
            output_directory=output_directory,
        )
        warnings = list(chart_result.warnings)
        generated_files: list[str] = []
        renderer_failures = 0
        metadata = self._reproducibility_metadata(
            workflow=workflow,
            formats=selected_formats,
            dataset_supplied=dataframe is not None,
            narrative_included=narrative is not None,
        )

        non_json_formats = [
            report_format for report_format in selected_formats if report_format != "json"
        ]

        for report_format in non_json_formats:
            renderer = self._renderers[report_format]
            context = self._render_context(
                workflow=workflow,
                chart_result=chart_result,
                generated_files=self._ordered_generated_files(
                    generated_files + [renderer.filename]
                ),
                warnings=warnings,
                metadata=metadata,
                narrative=narrative,
            )

            if self._render_file(renderer, context, output_directory, warnings):
                generated_files.append(renderer.filename)
            else:
                renderer_failures += 1

        if "json" in selected_formats:
            renderer = self._renderers["json"]
            expected_files = self._ordered_generated_files(generated_files + [renderer.filename])
            context = self._render_context(
                workflow=workflow,
                chart_result=chart_result,
                generated_files=expected_files,
                warnings=warnings,
                metadata=metadata,
                narrative=narrative,
            )

            if self._render_file(renderer, context, output_directory, warnings):
                generated_files.append(renderer.filename)
            else:
                renderer_failures += 1

        generated_files = self._ordered_generated_files(generated_files)
        failure_count = renderer_failures + len(chart_result.warnings)
        status = self._status(
            generated_file_count=len(generated_files),
            failure_count=failure_count,
        )

        return AgenticEDAReportResult(
            output_directory=str(output_directory),
            generated_files=generated_files,
            generated_visualisations=chart_result.generated,
            skipped_visualisations=chart_result.skipped,
            warnings=warnings,
            deterministic_summary=(
                f"Generated {len(generated_files)} report file(s) and "
                f"{len(chart_result.generated)} visualisation(s); "
                f"{len(chart_result.skipped)} visualisation(s) were skipped. "
                f"Report status: {status}."
            ),
            status=status,
        )

    def _normalise_formats(
        self,
        formats: Sequence[str] | None,
    ) -> list[str]:
        if formats is None:
            requested = list(_DEFAULT_FORMATS)
        elif isinstance(formats, (str, bytes)) or not isinstance(formats, Sequence):
            raise TypeError("formats must be a sequence of format names or None.")
        else:
            requested = []

            for value in formats:
                if not isinstance(value, str):
                    raise TypeError("Every report format must be a string.")

                normalised = value.strip().lower()

                if normalised not in requested:
                    requested.append(normalised)

        if not requested:
            raise ValueError("At least one report format must be requested.")

        unsupported = [
            report_format for report_format in requested if report_format not in self._renderers
        ]

        if unsupported:
            raise ValueError(
                "Unsupported Agentic EDA report format(s): "
                + ", ".join(unsupported)
                + ". Supported formats are: "
                + ", ".join(_FORMAT_ORDER)
                + "."
            )

        return [report_format for report_format in _FORMAT_ORDER if report_format in requested]

    @staticmethod
    def _prepare_output_directory(
        output_dir: str | Path,
    ) -> Path:
        if not isinstance(output_dir, (str, Path)):
            raise TypeError("output_dir must be a string or pathlib.Path.")

        if isinstance(output_dir, str) and not output_dir.strip():
            raise ValueError("output_dir must identify a dedicated report directory.")

        output_directory = Path(output_dir).expanduser().resolve()

        if output_directory == Path.cwd().resolve() or output_directory == Path(
            output_directory.anchor
        ):
            raise ValueError("output_dir must identify a dedicated report directory.")

        if output_directory.exists() and not output_directory.is_dir():
            raise ValueError(f"Report output path is not a directory: {output_directory}")

        try:
            output_directory.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise ValueError(
                f"Unable to create report output directory: {output_directory}"
            ) from exc

        return output_directory

    @staticmethod
    def _validated_dataframe(
        dataset: str | Path | pd.DataFrame | None,
        workflow: AgenticEDAResult,
    ) -> pd.DataFrame | None:
        if dataset is None:
            return None

        dataframe = load_eda_frame(dataset)
        validate_eda_result(dataframe, workflow.eda_result)
        return dataframe

    @staticmethod
    def _reproducibility_metadata(
        workflow: AgenticEDAResult,
        formats: list[str],
        dataset_supplied: bool,
        narrative_included: bool,
    ) -> dict[str, object]:
        return {
            "report_schema_version": 1,
            "deterministic": True,
            "workflow_status": workflow.overall_status,
            "dataset_shape": list(workflow.eda_result.shape),
            "column_names": list(workflow.eda_result.column_names),
            "formats": list(formats),
            "dataset_supplied_for_raw_charts": dataset_supplied,
            "optional_ai_narrative_included": narrative_included,
        }

    @staticmethod
    def _render_context(
        workflow: AgenticEDAResult,
        chart_result,
        generated_files: list[str],
        warnings: list[str],
        metadata: dict[str, object],
        narrative: AgenticEDANarrative | None,
    ) -> ReportRenderContext:
        return ReportRenderContext(
            workflow=workflow,
            generated_visualisations=chart_result.generated,
            skipped_visualisations=chart_result.skipped,
            generated_files=generated_files,
            warnings=list(warnings),
            reproducibility_metadata=metadata,
            narrative=narrative,
        )

    @staticmethod
    def _render_file(
        renderer: AgenticEDAReportRenderer,
        context: ReportRenderContext,
        output_directory: Path,
        warnings: list[str],
    ) -> bool:
        output_path = safe_artifact_path(output_directory, renderer.filename)
        temporary_path = output_path.with_name(f".{output_path.name}.tmp")

        try:
            content = renderer.render(context)
            temporary_path.write_text(content, encoding="utf-8")
            temporary_path.replace(output_path)
        except Exception as exc:
            warnings.append(
                f"Report renderer '{renderer.format}' failed: {type(exc).__name__}: {exc}"
            )

            if temporary_path.exists():
                temporary_path.unlink()

            return False

        return True

    @staticmethod
    def _ordered_generated_files(
        generated_files: list[str],
    ) -> list[str]:
        order = {
            renderer.filename: index for index, renderer in enumerate(default_report_renderers())
        }
        return sorted(generated_files, key=lambda filename: order.get(filename, len(order)))

    @staticmethod
    def _status(
        generated_file_count: int,
        failure_count: int,
    ) -> str:
        if not failure_count:
            return "success"

        return "partial_failure" if generated_file_count else "failure"


def default_report_renderers() -> list[AgenticEDAReportRenderer]:
    """Build report renderers in deterministic format order."""
    return [
        AgenticEDAHTMLRenderer(),
        AgenticEDAJSONRenderer(),
        AgenticEDAMarkdownRenderer(),
    ]
