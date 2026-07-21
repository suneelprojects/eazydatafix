import pandas as pd

from eazydatafix.assessment.checks._runner import run_checks
from eazydatafix.assessment.checks.accuracy.numeric_range_check import (
    NumericRangeCheck,
)
from eazydatafix.models.validation_result import ValidationResult


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
        return run_checks(
            self._checks,
            df,
        )
