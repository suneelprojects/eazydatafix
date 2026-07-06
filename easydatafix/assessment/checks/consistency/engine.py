import pandas as pd

from easydatafix.assessment.checks.consistency.case_consistency_check import (
    CaseConsistencyCheck,
)
from easydatafix.assessment.checks.consistency.duplicate_text_check import (
    DuplicateTextCheck,
)
from easydatafix.assessment.checks.consistency.whitespace_consistency_check import (
    WhitespaceConsistencyCheck,
)
from easydatafix.models.validation_result import ValidationResult


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
