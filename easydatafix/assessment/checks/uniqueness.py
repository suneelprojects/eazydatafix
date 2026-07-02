from dataclasses import dataclass

import pandas as pd


@dataclass(slots=True)
class UniquenessResult:
    """
    Result of uniqueness analysis.
    """

    total_rows: int
    duplicate_rows: int
    uniqueness_score: float


class UniquenessCheck:
    """
    Evaluates dataset uniqueness.
    """

    def evaluate(self, df: pd.DataFrame) -> UniquenessResult:
        total_rows = len(df)
        duplicate_rows = int(df.duplicated().sum())

        score = 100.0

        if total_rows > 0:
            score = ((total_rows - duplicate_rows) / total_rows) * 100

        return UniquenessResult(
            total_rows=total_rows,
            duplicate_rows=duplicate_rows,
            uniqueness_score=round(score, 2),
        )
