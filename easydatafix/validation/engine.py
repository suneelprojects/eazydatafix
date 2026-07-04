import pandas as pd

from easydatafix.models.validation_result import ValidationResult


class ValidationEngine:
    """
    Executes validation rules against a dataset.
    """

    def validate(self, df: pd.DataFrame) -> list[ValidationResult]:
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

        return results
