import pandas as pd

from eazydatafix.models.validation_result import ValidationResult


class DateCheck:
    """
    Validates date columns.
    """

    def evaluate(
        self,
        df: pd.DataFrame,
    ) -> list[ValidationResult]:

        results: list[ValidationResult] = []

        for column in df.columns:

            column_name = column.lower()

            if (
                "date" not in column_name
                and "dob" not in column_name
                and "birth" not in column_name
                and "joining" not in column_name
            ):
                continue

            invalid = 0

            for value in df[column].dropna():

                try:
                    pd.to_datetime(
                        value,
                        errors="raise",
                    )

                except Exception:
                    invalid += 1

            if invalid == 0:

                results.append(
                    ValidationResult(
                        rule="Date Format",
                        column=column,
                        passed=True,
                        message="All dates are valid.",
                    )
                )

            else:

                results.append(
                    ValidationResult(
                        rule="Date Format",
                        column=column,
                        passed=False,
                        message=f"{invalid} invalid date(s) found.",
                    )
                )

        return results
