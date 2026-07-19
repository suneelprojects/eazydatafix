from pathlib import Path

from eazydatafix.models.assessment_report import AssessmentReport


class HtmlReport:
    """
    Generates an HTML report from an AssessmentReport.
    """

    @staticmethod
    def export(
        report: AssessmentReport,
        output_file: str,
    ) -> None:

        template_path = (
            Path(__file__).parent
            / "templates"
            / "report.html"
        )

        html = template_path.read_text(
            encoding="utf-8"
        )

        recommendations_html = ""

        priority_colors = {
            "HIGH": "#dc2626",
            "MEDIUM": "#f59e0b",
            "LOW": "#16a34a",
        }

        for recommendation in report.recommendations:

            color = priority_colors.get(
                recommendation.priority.upper(),
                "#2563eb",
            )

            recommendations_html += f"""
<div class="recommendation">
    <h3>{recommendation.title}</h3>

    <p>{recommendation.description}</p>

    <p>
        <strong>Category:</strong>
        {recommendation.category}
    </p>

    <p>
        <strong>Auto Fix:</strong>
        {"Yes" if recommendation.auto_fix_available else "No"}
    </p>

    <span
        class="priority"
        style="background:{color};"
    >
        {recommendation.priority}
    </span>

</div>
"""

        html = (
            html
            .replace(
                "{{file_name}}",
                report.dataset_info.file_name,
            )
            .replace(
                "{{rows}}",
                str(report.dataset_info.rows),
            )
            .replace(
                "{{columns}}",
                str(report.dataset_info.columns),
            )
            .replace(
                "{{memory}}",
                f"{report.dataset_info.memory_usage_bytes:,} Bytes",
            )
            .replace(
                "{{score}}",
                f"{report.quality.score:.2f}",
            )
            .replace(
                "{{grade}}",
                report.quality.grade,
            )
            .replace(
                "{{completeness}}",
                f"{report.quality_dimensions.completeness:.2f}%"
            )
            .replace(
                "{{uniqueness}}",
                f"{report.quality_dimensions.uniqueness:.2f}%"
            )
            .replace(
                "{{validity}}",
                f"{report.quality_dimensions.validity:.2f}%"
            )
            .replace(
                "{{consistency}}",
                f"{report.quality_dimensions.consistency:.2f}%"
            )
            .replace(
                "{{accuracy}}",
                f"{report.quality_dimensions.accuracy:.2f}%"
            )
            .replace(
                "{{timeliness}}",
                f"{report.quality_dimensions.timeliness:.2f}%"
            )
            .replace(
                "{{overall}}",
                f"{report.quality_dimensions.overall:.2f}%"
            )
            .replace(
                "{{recommendations}}",
                recommendations_html,
            )
        )

        Path(output_file).write_text(
            html,
            encoding="utf-8",
        )
