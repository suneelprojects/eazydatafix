from dataclasses import dataclass

import pandas as pd

from easydatafix.contracts.check import Check


@dataclass(slots=True)
class CompletenessResult:
    """
    Represents the completeness assessment result.
    """

    total_missing_values: int
    completeness_score: float


class CompletenessCheck(Check):
    """
    Evaluates dataset completeness.
    """

    @property
    def name(self) -> str:
        return "Completeness"

    def evaluate(self, df: pd.DataFrame) -> CompletenessResult:
        total_cells = df.shape[0] * df.shape[1]
        missing_values = int(df.isna().sum().sum())

        score = (
            100.0
            if total_cells == 0
            else ((total_cells - missing_values) / total_cells) * 100
        )

        return CompletenessResult(
            total_missing_values=missing_values,
            completeness_score=round(score, 2),
        )
