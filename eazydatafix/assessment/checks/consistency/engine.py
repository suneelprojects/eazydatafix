import pandas as pd

from eazydatafix.assessment.checks._runner import run_checks
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
        return run_checks(
            self._checks,
            df,
        )
