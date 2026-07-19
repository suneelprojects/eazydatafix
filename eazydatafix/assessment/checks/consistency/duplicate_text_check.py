import pandas as pd

from eazydatafix.models.validation_result import ValidationResult


class DuplicateTextCheck:
    """
    Detects duplicate text values in string columns.
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
                .str.lower()
            )

            duplicate_count = int(values.duplicated().sum())

            if duplicate_count == 0:

                results.append(
                    ValidationResult(
                        rule="Duplicate Text",
                        column=column,
                        passed=True,
                        message="No duplicate text values found.",
                    )
                )

            else:

                results.append(
                    ValidationResult(
                        rule="Duplicate Text",
                        column=column,
                        passed=False,
                        message=f"{duplicate_count} duplicate value(s) found.",
                    )
                )

        return results
