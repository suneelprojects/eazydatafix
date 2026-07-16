from easydatafix.models.assessment_report import AssessmentReport
from easydatafix.rendering.console import Console


class Report:
    """
    Displays assessment results in a user-friendly format.
    """

    def __init__(
        self,
        report: AssessmentReport,
    ):
        self._report = report

    def summary(self) -> None:

        Console.title("🚀 EASYDATAFIX DATA QUALITY REPORT")

        # ------------------------------------------------------------------
        # Dataset Information
        # ------------------------------------------------------------------

        Console.section("📁 DATASET INFORMATION")

        Console.key_value(
            "File Name",
            self._report.dataset_info.file_name,
        )

        Console.key_value(
            "Rows",
            f"{self._report.dataset_info.rows:,}",
        )

        Console.key_value(
            "Columns",
            f"{self._report.dataset_info.columns:,}",
        )

        Console.key_value(
            "Memory Usage",
            Console.format_bytes(
                self._report.dataset_info.memory_usage_bytes
            ),
        )

        # ------------------------------------------------------------------
        # Overall Quality
        # ------------------------------------------------------------------

        Console.section("📊 OVERALL QUALITY")

        Console.key_value(
            "Score",
            f"{self._report.quality.score:.2f} / 100",
        )

        Console.key_value(
            "Grade",
            self._report.quality.grade,
        )

        Console.key_value(
            "Status",
            Console.quality_status(
                self._report.quality.score
            ),
        )

        # ------------------------------------------------------------------
        # Quality Dimensions
        # ------------------------------------------------------------------

        Console.section("📈 QUALITY DIMENSIONS")

        Console.key_value(
            "Completeness",
            f"{self._report.quality_dimensions.completeness:.2f}%",
        )

        Console.key_value(
            "Uniqueness",
            f"{self._report.quality_dimensions.uniqueness:.2f}%",
        )

        Console.key_value(
            "Validity",
            f"{self._report.quality_dimensions.validity:.2f}%",
        )

        Console.key_value(
            "Consistency",
            f"{self._report.quality_dimensions.consistency:.2f}%",
        )

        Console.key_value(
            "Accuracy",
            f"{self._report.quality_dimensions.accuracy:.2f}%",
        )

        Console.key_value(
            "Timeliness",
            f"{self._report.quality_dimensions.timeliness:.2f}%",
        )

        # ------------------------------------------------------------------
        # Recommendations
        # ------------------------------------------------------------------

        Console.section(
            f"💡 RECOMMENDATIONS ({len(self._report.recommendations)})"
        )

        if not self._report.recommendations:

            Console.key_value(
                "Status",
                "No recommendations. Dataset looks healthy. ✅",
            )

        else:

            priority_icons = {
                "HIGH": "🔴 High",
                "MEDIUM": "🟡 Medium",
                "LOW": "🟢 Low",
            }

            for index, recommendation in enumerate(
                self._report.recommendations,
                start=1,
            ):

                Console.recommendation(
                    index,
                    recommendation.title,
                )

                Console.key_value(
                    "Priority",
                    priority_icons.get(
                        recommendation.priority.upper(),
                        recommendation.priority,
                    ),
                    indent=4,
                )

                Console.key_value(
                    "Category",
                    recommendation.category,
                    indent=4,
                )

                Console.key_value(
                    "Auto Fix",
                    "Yes ✅"
                    if recommendation.auto_fix_available
                    else "No",
                    indent=4,
                )

                Console.key_value(
                    "Description",
                    recommendation.description,
                    indent=4,
                )

                Console.blank()

        Console.divider("=")
