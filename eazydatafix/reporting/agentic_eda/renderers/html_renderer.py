import html
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

_STYLES = """
:root { color-scheme: light; font-family: Inter, system-ui, sans-serif; }
body { margin: 0; background: #f4f7fb; color: #172033; }
main { width: min(1120px, calc(100% - 32px)); margin: 32px auto 64px; }
header { padding: 28px; color: white; border-radius: 16px;
  background: linear-gradient(135deg, #1d4ed8, #0f766e); }
h1, h2, h3 { margin-top: 0; }
section { margin-top: 20px; padding: 22px; background: white; border-radius: 14px;
  box-shadow: 0 4px 18px rgba(15, 23, 42, .07); }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; }
.card { padding: 14px; border: 1px solid #dbe4f0; border-radius: 10px; overflow-wrap: anywhere; }
.label { color: #64748b; font-size: .82rem; text-transform: uppercase; }
.value { margin-top: 5px; font-size: 1.05rem; font-weight: 650; }
table { width: 100%; border-collapse: collapse; }
th, td { padding: 9px; border-bottom: 1px solid #e2e8f0; text-align: left; }
pre { overflow-x: auto; padding: 14px; border-radius: 8px; background: #0f172a; color: #e2e8f0; }
img { display: block; width: min(100%, 820px); margin: 14px auto; border-radius: 10px; }
.warning { border-left: 4px solid #f59e0b; padding-left: 12px; }
.muted { color: #64748b; }
@media (max-width: 640px) { main { width: min(100% - 18px, 1120px); margin-top: 9px; }
  header, section { border-radius: 10px; padding: 16px; } }
"""


class AgenticEDAHTMLRenderer(AgenticEDAReportRenderer):
    """Renders a standalone responsive HTML report with embedded CSS."""

    format = "html"
    filename = "agentic-eda-report.html"

    def render(
        self,
        context: ReportRenderContext,
    ) -> str:
        """Render all required report sections in canonical order."""
        sections = [
            self._overview(context),
            self._dataset_profile(context),
            self._semantic_roles(context),
        ]
        sections.extend(
            self._analysis_section(title, step_name, context)
            for title, step_name in _ANALYSIS_SECTIONS
        )
        sections.extend(
            [
                self._records_section(
                    "Priority findings",
                    context.workflow.priority_findings,
                ),
                self._records_section(
                    "Follow-up actions",
                    context.workflow.follow_up_actions,
                ),
                self._visualisations(context),
                self._records_section(
                    "Unresolved questions",
                    context.workflow.unresolved_questions,
                ),
                self._warnings(context),
                self._reproducibility(context),
            ]
        )
        title = "Agentic EDA Report"
        return (
            '<!doctype html>\n<html lang="en">\n<head>\n'
            '<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            f"<title>{title}</title>\n<style>{_STYLES}</style>\n</head>\n<body>\n"
            f"<main><header><h1>{title}</h1>"
            "<p>Deterministic, reproducible exploratory data analysis workflow.</p>"
            f"</header>{''.join(sections)}</main>\n</body>\n</html>\n"
        )

    def _overview(
        self,
        context: ReportRenderContext,
    ) -> str:
        workflow = context.workflow
        cards = [
            ("Overall status", workflow.overall_status),
            ("Rows", workflow.eda_result.shape[0]),
            ("Columns", workflow.eda_result.shape[1]),
            ("Priority findings", len(workflow.priority_findings)),
            ("Follow-up actions", len(workflow.follow_up_actions)),
            ("Generated charts", len(context.generated_visualisations)),
        ]
        return self._card_section("Report overview", cards)

    def _dataset_profile(
        self,
        context: ReportRenderContext,
    ) -> str:
        return self._json_section(
            "Dataset profile",
            context.workflow.eda_result.dataset_profile,
        )

    def _semantic_roles(
        self,
        context: ReportRenderContext,
    ) -> str:
        roles = context.workflow.eda_result.semantic_roles
        rows = "".join(
            f"<tr><td>{self._escape(column)}</td><td>{self._escape(role)}</td></tr>"
            for column, role in roles.items()
        )
        table = (
            "<table><thead><tr><th>Column</th><th>Semantic role</th></tr></thead>"
            f"<tbody>{rows}</tbody></table>"
            if rows
            else '<p class="muted">No columns.</p>'
        )
        return f"<section><h2>Semantic column roles</h2>{table}</section>"

    def _analysis_section(
        self,
        title: str,
        step_name: str,
        context: ReportRenderContext,
    ) -> str:
        output = context.step_outputs.get(step_name)

        if output is None:
            return (
                f"<section><h2>{self._escape(title)}</h2>"
                '<p class="muted">This analysis was not executed successfully '
                "or was not applicable.</p></section>"
            )

        return self._json_section(title, output)

    def _records_section(
        self,
        title: str,
        records: list[Any],
    ) -> str:
        if not records:
            content = '<p class="muted">None.</p>'
        else:
            content = (
                '<div class="grid">'
                + "".join(
                    f'<article class="card"><pre>{self._json(record)}</pre></article>'
                    for record in records
                )
                + "</div>"
            )

        return f"<section><h2>{self._escape(title)}</h2>{content}</section>"

    def _visualisations(
        self,
        context: ReportRenderContext,
    ) -> str:
        recommended = self._records_section(
            "Recommended visualisations",
            context.workflow.recommended_visualisations,
        )
        generated = "".join(
            '<article class="card">'
            f"<h3>{self._escape(item.type)}</h3>"
            f"<p>{self._escape(', '.join(item.target_columns) or 'Dataset')}</p>"
            f'<img src="{self._escape(item.path)}" alt="{self._escape(item.type)}">'
            "</article>"
            for item in context.generated_visualisations
        )
        generated_content = (
            f'<div class="grid">{generated}</div>'
            if generated
            else '<p class="muted">No visualisation artifacts were generated.</p>'
        )
        skipped = self._records_section(
            "Skipped visualisations",
            context.skipped_visualisations,
        )
        return (
            recommended
            + f"<section><h2>Generated visualisation artifacts</h2>{generated_content}</section>"
            + skipped
        )

    def _warnings(
        self,
        context: ReportRenderContext,
    ) -> str:
        warnings = context.workflow.workflow_warnings + context.warnings
        content = (
            "".join(f'<p class="warning">{self._escape(item)}</p>' for item in warnings)
            if warnings
            else '<p class="muted">None.</p>'
        )
        return f"<section><h2>Workflow warnings</h2>{content}</section>"

    def _reproducibility(
        self,
        context: ReportRenderContext,
    ) -> str:
        return self._json_section(
            "Reproducibility metadata",
            context.reproducibility_metadata,
        )

    def _card_section(
        self,
        title: str,
        cards: list[tuple[str, Any]],
    ) -> str:
        content = "".join(
            '<article class="card">'
            f'<div class="label">{self._escape(label)}</div>'
            f'<div class="value">{self._escape(value)}</div>'
            "</article>"
            for label, value in cards
        )
        return f'<section><h2>{self._escape(title)}</h2><div class="grid">{content}</div></section>'

    def _json_section(
        self,
        title: str,
        value: Any,
    ) -> str:
        return (
            f"<section><h2>{self._escape(title)}</h2>" f"<pre>{self._json(value)}</pre></section>"
        )

    @staticmethod
    def _escape(value: Any) -> str:
        return html.escape(str(value), quote=True)

    def _json(self, value: Any) -> str:
        rendered = json.dumps(
            to_json_compatible(value),
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )
        return self._escape(rendered)
