from dataclasses import dataclass

import pandas as pd

from eazydatafix.contracts.check import Check


@dataclass(slots=True)
class UniquenessResult:
    """
    Represents the uniqueness assessment result.
    """

    total_rows: int
    duplicate_rows: int
    uniqueness_score: float


class UniquenessCheck(Check):
    """
    Evaluates dataset uniqueness.
    """

    @property
    def name(self) -> str:
        return "Uniqueness"

    def evaluate(self, df: pd.DataFrame) -> UniquenessResult:
        total_rows = len(df)
        duplicate_rows = int(df.duplicated().sum())

        score = (
            100.0
            if total_rows == 0
            else ((total_rows - duplicate_rows) / total_rows) * 100
        )

        return UniquenessResult(
            total_rows=total_rows,
            duplicate_rows=duplicate_rows,
            uniqueness_score=round(score, 2),
        )
