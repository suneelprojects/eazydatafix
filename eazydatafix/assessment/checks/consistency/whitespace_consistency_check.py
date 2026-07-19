import pandas as pd

from eazydatafix.models.validation_result import ValidationResult


class WhitespaceConsistencyCheck:
    """
    Detects leading/trailing whitespaces in text columns.
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

            whitespace_count = 0

            for value in df[column].dropna():

                value = str(value)

                if value != value.strip():
                    whitespace_count += 1

            if whitespace_count == 0:

                results.append(
                    ValidationResult(
                        rule="Whitespace Consistency",
                        column=column,
                        passed=True,
                        message="No leading/trailing whitespaces found.",
                    )
                )

            else:

                results.append(
                    ValidationResult(
                        rule="Whitespace Consistency",
                        column=column,
                        passed=False,
                        message=f"{whitespace_count} value(s) contain leading/trailing whitespaces.",
                    )
                )

        return results
