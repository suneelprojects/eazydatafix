import pandas as pd

from easydatafix.assessment.checks.accuracy.numeric_range_check import (
    NumericRangeCheck,
)
from easydatafix.models.validation_result import ValidationResult


class AccuracyEngine:
    """
    Runs all accuracy checks.
    """

    def __init__(self) -> None:

        self._checks = [
            NumericRangeCheck(),
        ]

    def evaluate(
        self,
        df: pd.DataFrame,
    ) -> list[ValidationResult]:

        results: list[ValidationResult] = []

        for check in self._checks:
            results.extend(
                check.evaluate(df)
            )

        return results
