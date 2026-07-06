from datetime import datetime

import pandas as pd

from easydatafix.models.validation_result import ValidationResult


class FutureDateCheck:
    """
    Detects dates that occur in the future.
    """

    def evaluate(
        self,
        df: pd.DataFrame,
    ) -> list[ValidationResult]:

        results: list[ValidationResult] = []

        today = pd.Timestamp(datetime.today().date())

        for column in df.columns:

            column_name = column.lower()

            if (
                "date" not in column_name
                and "joining" not in column_name
                and "dob" not in column_name
                and "birth" not in column_name
            ):
                continue

            dates = pd.to_datetime(
                df[column],
                errors="coerce",
            )

            future_count = int((dates > today).sum())

            if future_count == 0:

                results.append(
                    ValidationResult(
                        rule="Future Date",
                        column=column,
                        passed=True,
                        message="No future dates found.",
                    )
                )

            else:

                results.append(
                    ValidationResult(
                        rule="Future Date",
                        column=column,
                        passed=False,
                        message=f"{future_count} future date(s) found.",
                    )
                )

        return results
