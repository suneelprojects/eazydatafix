import pandas as pd

from eazydatafix.models.validation_result import ValidationResult


class CaseConsistencyCheck:
    """
    Detects inconsistent text casing.
    """

    def evaluate(
        self,
        df: pd.DataFrame,
    ) -> list[ValidationResult]:

        results: list[ValidationResult] = []

        for column in df.columns:

            if not (
                pd.api.types.is_object_dtype(df[column])
                or pd.api.types.is_string_dtype(df[column])
            ):
                continue

            values = (
                df[column]
                .dropna()
                .astype(str)
                .str.strip()
            )

            if values.empty:
                continue

            original = set(values)

            normalized = {
                value.lower()
                for value in original
            }

            if len(original) != len(normalized):

                results.append(
                    ValidationResult(
                        rule="Case Consistency",
                        column=column,
                        passed=False,
                        message="Mixed letter casing detected.",
                    )
                )

            else:

                results.append(
                    ValidationResult(
                        rule="Case Consistency",
                        column=column,
                        passed=True,
                        message="Consistent letter casing.",
                    )
                )

        return results
