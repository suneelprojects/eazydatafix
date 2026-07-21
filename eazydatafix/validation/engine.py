import pandas as pd

from eazydatafix.assessment.checks._runner import run_checks
from eazydatafix.assessment.checks.validity.engine import ValidityEngine
from eazydatafix.models.validation_result import ValidationResult


class ValidationEngine:
    """
    Executes all dataset validations.
    """

    def __init__(self) -> None:

        self._validity_engine = ValidityEngine()

    def validate(
        self,
        df: pd.DataFrame,
    ) -> list[ValidationResult]:

        results: list[ValidationResult] = []

        # Missing Values Validation

        for column in df.columns:

            missing_count = int(df[column].isna().sum())

            results.append(
                ValidationResult(
                    rule="Missing Values",
                    column=column,
                    passed=missing_count == 0,
                    message=(
                        "No missing values found."
                        if missing_count == 0
                        else f"{missing_count} missing value(s) found."
                    ),
                )
            )

        # Validity Checks

        results.extend(
            run_checks(
                [self._validity_engine],
                df,
            )
        )

        return results
