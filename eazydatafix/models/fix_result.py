from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from eazydatafix.models.assessment_report import AssessmentReport
from eazydatafix.rendering.console import Console


@dataclass(slots=True)
class FixResult:
    """
    Represents the result of an automatic data cleaning operation.
    """

    dataset: pd.DataFrame
    before_report: AssessmentReport
    after_report: AssessmentReport
    applied_fixes: list[str]

    def __repr__(self) -> str:
        """
        Human-friendly representation displayed in Jupyter Notebook
        and interactive Python sessions.
        """

        improvement = (
            self.after_report.quality.score
            - self.before_report.quality.score
        )

        lines = [
            "",
            "✅ EazyDataFix - Fix Completed",
            "=" * 45,
            "",
            "📊 Dataset",
            f"Rows                : {self.dataset.shape[0]}",
            f"Columns             : {self.dataset.shape[1]}",
            "",
            "🏆 Quality Score",
            (
                f"Before              : "
                f"{self.before_report.quality.score:.2f} "
                f"({self.before_report.quality.grade})"
            ),
            (
                f"After               : "
                f"{self.after_report.quality.score:.2f} "
                f"({self.after_report.quality.grade})"
            ),
            f"Improvement         : +{improvement:.2f}",
            "",
            "🔧 Applied Fixes",
        ]

        if self.applied_fixes:
            lines.extend(
                f"✓ {fix}"
                for fix in self.applied_fixes
            )
        else:
            lines.append("No fixes were applied.")

        lines.extend(
            [
                "",
                "💡 Next Steps",
                "result.dataset",
                "result.report()",
                'result.save("clean.csv")',
            ]
        )

        return "\n".join(lines)

    __str__ = __repr__

    def report(self) -> None:
        """
        Display a summary of the cleaning operation.
        """

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
            Console.key_value(
                "Status",
                "No fixes were applied.",
            )
        else:
            for index, fix in enumerate(
                self.applied_fixes,
                start=1,
            ):
                Console.recommendation(
                    index,
                    fix,
                )

        Console.divider()

    def save(
        self,
        path: str | Path,
        *,
        index: bool = False,
        **kwargs: object,
    ) -> None:
        """
        Save the cleaned dataset.
        """

        self.dataset.to_csv(
            path,
            index=index,
            **kwargs,
        )

    # ------------------------------------------------------------------
    # Backward compatibility
    # ------------------------------------------------------------------

    def summary(self) -> None:
        """
        Backward-compatible alias for report().
        """

        self.report()

    def to_csv(
        self,
        file_path: str | Path,
        **kwargs: object,
    ) -> None:
        """
        Backward-compatible alias for save().
        """

        self.save(
            file_path,
            **kwargs,
        )
