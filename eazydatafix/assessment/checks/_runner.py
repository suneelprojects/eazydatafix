from collections.abc import Iterable
from typing import Protocol

import pandas as pd

from eazydatafix.models.validation_result import ValidationResult


class _ValidationCheck(Protocol):
    """
    Internal protocol for checks that produce validation results.
    """

    def evaluate(
        self,
        df: pd.DataFrame,
    ) -> list[ValidationResult]:
        """
        Evaluate a DataFrame and return validation results.
        """


def run_checks(
    checks: Iterable[_ValidationCheck],
    df: pd.DataFrame,
) -> list[ValidationResult]:
    """
    Run checks in order and collect their validation results.
    """

    results: list[ValidationResult] = []

    for check in checks:
        results.extend(
            check.evaluate(df)
        )

    return results
