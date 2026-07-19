import pandas as pd

from eazydatafix.assessment.checks.timeliness.future_date_check import (
    FutureDateCheck,
)
from eazydatafix.assessment.checks.timeliness.stale_data_check import (
    StaleDataCheck,
)
from eazydatafix.models.validation_result import ValidationResult


class TimelinessEngine:
    """
    Runs all timeliness checks.
    """

    def __init__(self) -> None:

        self._checks = [
            FutureDateCheck(),
            StaleDataCheck(),
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
