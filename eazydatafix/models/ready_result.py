"""
Ready Result Model

Represents the output returned after preparing a dataset for analysis or machine learning.
"""

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from eazydatafix.console_report import Report

from .assessment_report import AssessmentReport


@dataclass(slots=True)
class ReadyResult:
    """
    Container for dataset preparation results.
    """

    dataset: pd.DataFrame
    assessment: AssessmentReport
    applied_fixes: list[str]
    summary: str

    def save(
        self,
        path: str | Path,
        *,
        index: bool = False,
    ) -> None:
        """
        Save the prepared dataset to a file.

        Args:
            path: Destination file path.
            index: Whether to include the DataFrame index.
        """

        self.dataset.to_csv(
            path,
            index=index,
        )

    def report(self) -> None:
        """
        Display the assessment report for the prepared dataset.
        """

        Report(
            self.assessment,
        ).show()
