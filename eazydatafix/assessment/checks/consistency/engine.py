import pandas as pd

from eazydatafix.assessment.checks.consistency.case_consistency_check import (
    CaseConsistencyCheck,
)
from eazydatafix.assessment.checks.consistency.duplicate_text_check import (
    DuplicateTextCheck,
)
from eazydatafix.assessment.checks.consistency.whitespace_consistency_check import (
    WhitespaceConsistencyCheck,
)
from eazydatafix.models.validation_result import ValidationResult


class ConsistencyEngine:
    """
    Runs all consistency checks.
    """

    def __init__(self) -> None:

        self._checks = [
            CaseConsistencyCheck(),
            WhitespaceConsistencyCheck(),
            DuplicateTextCheck(),
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
