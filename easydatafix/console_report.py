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

        Console.title("🛠️ EASY DATA FIX REPORT")

        Console.section("📊 OVERALL QUALITY")

        Console.key_value(
            "Score",
            f"{self._report.quality.score:.2f} / 100",
        )

        Console.key_value(
            "Grade",
            self._report.quality.grade,
        )

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

        Console.section("💡 RECOMMENDATIONS")

        if not self._report.recommendations:

            Console.key_value(
                "Status",
                "No recommendations. Dataset looks healthy. ✅",
            )

        else:

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
                    recommendation.priority,
                    indent=3,
                )

                Console.key_value(
                    "Category",
                    recommendation.category,
                    indent=3,
                )

                Console.key_value(
                    "Auto Fix",
                    "Yes"
                    if recommendation.auto_fix_available
                    else "No",
                    indent=3,
                )

                Console.key_value(
                    "Description",
                    recommendation.description,
                    indent=3,
                )

                Console.blank()

        Console.divider()
