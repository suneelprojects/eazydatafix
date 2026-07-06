from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph
from reportlab.platypus import SimpleDocTemplate
from reportlab.platypus import Spacer
from reportlab.platypus import Table
from reportlab.platypus import TableStyle

from easydatafix.models.assessment_report import AssessmentReport


class PdfReport:
    """
    Exports an AssessmentReport as a PDF report.
    """

    @staticmethod
    def export(
        report: AssessmentReport,
        output_file: str,
    ) -> None:

        document = SimpleDocTemplate(output_file)
        styles = getSampleStyleSheet()

        story = []

        # ------------------------------------------------------------------
        # Title
        # ------------------------------------------------------------------

        story.append(
            Paragraph(
                "<b>Easy Data Fix Report</b>",
                styles["Title"],
            )
        )

        story.append(
            Spacer(1, 18)
        )

        # ------------------------------------------------------------------
        # Dataset
        # ------------------------------------------------------------------

        story.append(
            Paragraph(
                "<b>Dataset Information</b>",
                styles["Heading2"],
            )
        )

        dataset_table = Table(
            [
                ["Property", "Value"],
                ["File Name", report.dataset_info.file_name],
                ["Rows", report.dataset_info.rows],
                ["Columns", report.dataset_info.columns],
                [
                    "Memory Usage",
                    f"{report.dataset_info.memory_usage_bytes:,} Bytes",
                ],
            ]
        )

        dataset_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563eb")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                ]
            )
        )

        story.append(dataset_table)

        story.append(Spacer(1, 18))

        # ------------------------------------------------------------------
        # Overall Quality
        # ------------------------------------------------------------------

        story.append(
            Paragraph(
                "<b>Overall Quality</b>",
                styles["Heading2"],
            )
        )

        quality_table = Table(
            [
                ["Metric", "Value"],
                ["Score", f"{report.quality.score:.2f}"],
                ["Grade", report.quality.grade],
            ]
        )

        quality_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563eb")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ]
            )
        )

        story.append(quality_table)

        story.append(Spacer(1, 18))

        # ------------------------------------------------------------------
        # Quality Dimensions
        # ------------------------------------------------------------------

        story.append(
            Paragraph(
                "<b>Quality Dimensions</b>",
                styles["Heading2"],
            )
        )

        dimension_table = Table(
            [
                ["Metric", "Score"],
                ["Completeness", f"{report.quality_dimensions.completeness:.2f}%"],
                ["Uniqueness", f"{report.quality_dimensions.uniqueness:.2f}%"],
                ["Validity", f"{report.quality_dimensions.validity:.2f}%"],
                ["Consistency", f"{report.quality_dimensions.consistency:.2f}%"],
                ["Accuracy", f"{report.quality_dimensions.accuracy:.2f}%"],
                ["Timeliness", f"{report.quality_dimensions.timeliness:.2f}%"],
                ["Overall", f"{report.quality_dimensions.overall:.2f}%"],
            ]
        )

        dimension_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563eb")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ]
            )
        )

        story.append(dimension_table)

        story.append(Spacer(1, 18))

        # ------------------------------------------------------------------
        # Recommendations
        # ------------------------------------------------------------------

        story.append(
            Paragraph(
                "<b>Recommendations</b>",
                styles["Heading2"],
            )
        )

        if not report.recommendations:

            story.append(
                Paragraph(
                    "No recommendations. Dataset looks healthy.",
                    styles["BodyText"],
                )
            )

        else:

            for recommendation in report.recommendations:

                story.append(
                    Paragraph(
                        f"<b>{recommendation.title}</b>",
                        styles["BodyText"],
                    )
                )

                story.append(
                    Paragraph(
                        f"Priority: {recommendation.priority}",
                        styles["BodyText"],
                    )
                )

                story.append(
                    Paragraph(
                        f"Category: {recommendation.category}",
                        styles["BodyText"],
                    )
                )

                story.append(
                    Paragraph(
                        f"Auto Fix: {'Yes' if recommendation.auto_fix_available else 'No'}",
                        styles["BodyText"],
                    )
                )

                story.append(
                    Paragraph(
                        recommendation.description,
                        styles["BodyText"],
                    )
                )

                story.append(
                    Spacer(1, 10)
                )

        # ------------------------------------------------------------------
        # Validations
        # ------------------------------------------------------------------

        story.append(
            Spacer(1, 10)
        )

        story.append(
            Paragraph(
                "<b>Validations</b>",
                styles["Heading2"],
            )
        )

        rows = [
            [
                "Rule",
                "Column",
                "Status",
            ]
        ]

        for validation in report.validations:

            rows.append(
                [
                    validation.rule,
                    validation.column,
                    "PASS"
                    if validation.passed
                    else "FAIL",
                ]
            )

        validation_table = Table(rows)

        validation_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563eb")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                ]
            )
        )

        story.append(validation_table)

        document.build(story)
