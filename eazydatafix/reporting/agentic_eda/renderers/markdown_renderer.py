import json
from typing import Any

from eazydatafix.models.serialization import to_json_compatible
from eazydatafix.reporting.agentic_eda.renderers.base import (
    AgenticEDAReportRenderer,
    ReportRenderContext,
)

_ANALYSIS_SECTIONS = [
    ("Missing-value analysis", "missing_value_analysis"),
    ("Duplicate review", "duplicate_review"),
    ("Numeric distributions", "numeric_distribution_analysis"),
    ("Outlier analysis", "outlier_analysis"),
    ("Skewness analysis", "skewness_analysis"),
    ("Categorical distributions", "categorical_distribution_analysis"),
    ("Boolean distributions", "boolean_distribution_analysis"),
    ("Class imbalance", "class_imbalance_analysis"),
    ("Correlations", "correlation_review"),
    ("Datetime trends", "datetime_trend_analysis"),
]


class AgenticEDAMarkdownRenderer(AgenticEDAReportRenderer):
    """Renders a readable deterministic Markdown report."""

    format = "markdown"
    filename = "agentic-eda-report.md"

    def render(
        self,
        context: ReportRenderContext,
    ) -> str:
        """Render all report sections in their canonical order."""
        workflow = context.workflow
        lines = [
            "# Agentic EDA Report",
            "",
            "## Report overview",
            "",
            f"- Overall status: `{workflow.overall_status}`",
            f"- Dataset shape: `{workflow.eda_result.shape[0]} × {workflow.eda_result.shape[1]}`",
            f"- Priority findings: `{len(workflow.priority_findings)}`",
            f"- Follow-up actions: `{len(workflow.follow_up_actions)}`",
            "",
            "## Dataset profile",
            "",
            self._json_block(workflow.eda_result.dataset_profile),
            "",
            "## Semantic column roles",
            "",
            self._mapping_table(workflow.eda_result.semantic_roles),
            "",
        ]

        for title, step_name in _ANALYSIS_SECTIONS:
            lines.extend(self._analysis_section(title, step_name, context))

        lines.extend(self._decision_sections(context))
        lines.extend(self._visualisation_section(context))
        lines.extend(self._warnings_section(context))
        lines.extend(
            [
                "## Reproducibility metadata",
                "",
                self._json_block(context.reproducibility_metadata),
                "",
            ]
        )
        return "\n".join(lines).rstrip() + "\n"

    def _analysis_section(
        self,
        title: str,
        step_name: str,
        context: ReportRenderContext,
    ) -> list[str]:
        output = context.step_outputs.get(step_name)
        content = (
            self._json_block(output)
            if output is not None
            else "_This analysis was not executed successfully or was not applicable._"
        )
        return [f"## {title}", "", content, ""]

    def _decision_sections(
        self,
        context: ReportRenderContext,
    ) -> list[str]:
        workflow = context.workflow
        return [
            "## Priority findings",
            "",
            self._records(workflow.priority_findings),
            "",
            "## Follow-up actions",
            "",
            self._records(workflow.follow_up_actions),
            "",
            "## Recommended visualisations",
            "",
            self._records(workflow.recommended_visualisations),
            "",
            "## Unresolved questions",
            "",
            self._records(workflow.unresolved_questions),
            "",
        ]

    def _visualisation_section(
        self,
        context: ReportRenderContext,
    ) -> list[str]:
        lines = ["### Generated visualisation artifacts", ""]

        if not context.generated_visualisations:
            lines.append("_No visualisation artifacts were generated._")
        else:
            for item in context.generated_visualisations:
                label = f"{item.type}: {', '.join(item.target_columns) or 'dataset'}"
                lines.extend([f"![{label}]({item.path})", ""])

        lines.extend(
            ["### Skipped visualisations", "", self._records(context.skipped_visualisations), ""]
        )
        return lines

    @staticmethod
    def _warnings_section(
        context: ReportRenderContext,
    ) -> list[str]:
        warnings = context.workflow.workflow_warnings + context.warnings
        content = "\n".join(f"- {warning}" for warning in warnings) if warnings else "_None._"
        return ["## Workflow warnings", "", content, ""]

    @staticmethod
    def _records(records: list[Any]) -> str:
        if not records:
            return "_None._"

        return "\n\n".join(
            f"```json\n{json.dumps(to_json_compatible(record), indent=2, sort_keys=True)}\n```"
            for record in records
        )

    @staticmethod
    def _mapping_table(mapping: dict[str, str]) -> str:
        if not mapping:
            return "_No columns._"

        rows = ["| Column | Semantic role |", "|---|---|"]
        rows.extend(f"| {column} | {role} |" for column, role in mapping.items())
        return "\n".join(rows)

    @staticmethod
    def _json_block(value: Any) -> str:
        return f"```json\n{json.dumps(to_json_compatible(value), indent=2, sort_keys=True)}\n```"
