from dataclasses import dataclass

import pandas as pd

from eazydatafix.models.assessment_report import AssessmentReport
from eazydatafix.rendering.console import Console


@dataclass(slots=True)
class FixResult:
    """
    Represents the result of an automatic data cleaning operation.
    """

    dataframe: pd.DataFrame
    before_report: AssessmentReport
    after_report: AssessmentReport
    applied_fixes: list[str]

    def summary(self) -> None:
        Console.title("🛠️ EASY DATA FIX SUMMARY")

        Console.section("📊 QUALITY IMPROVEMENT")
        Console.key_value(
            "Before Score",
            f"{self.before_report.quality.score:.2f}",
        )
        Console.key_value(
            "After Score",
            f"{self.after_report.quality.score:.2f}",
        )

        improvement = (
            self.after_report.quality.score
            - self.before_report.quality.score
        )

        Console.key_value(
            "Improvement",
            f"+{improvement:.2f}",
        )

        Console.section("✅ APPLIED FIXES")

        if not self.applied_fixes:
            Console.key_value("Status", "No fixes were applied.")
        else:
            for index, fix in enumerate(self.applied_fixes, start=1):
                Console.recommendation(index, fix)

        Console.divider()

    def to_csv(self, file_path: str, **kwargs) -> None:
        """
        Save the cleaned dataset.
        """
        self.dataframe.to_csv(file_path, index=False, **kwargs)
