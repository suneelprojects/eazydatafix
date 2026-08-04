import json

from eazydatafix.models.serialization import to_json_compatible
from eazydatafix.reporting.agentic_eda.renderers.base import (
    AgenticEDAReportRenderer,
    ReportRenderContext,
)


class AgenticEDAJSONRenderer(AgenticEDAReportRenderer):
    """Renders workflow and artifact metadata as stable JSON."""

    format = "json"
    filename = "agentic-eda-report.json"

    def render(
        self,
        context: ReportRenderContext,
    ) -> str:
        """Render standard-library JSON with stable keys and indentation."""
        payload = {
            "workflow": context.workflow.to_dict(),
            "grounded_narrative": (
                context.narrative.to_dict() if context.narrative is not None else None
            ),
            "report_artifacts": {
                "output_directory": ".",
                "generated_files": context.generated_files,
                "generated_visualisations": to_json_compatible(context.generated_visualisations),
                "skipped_visualisations": to_json_compatible(context.skipped_visualisations),
                "warnings": context.warnings,
            },
            "reproducibility_metadata": context.reproducibility_metadata,
        }
        return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
