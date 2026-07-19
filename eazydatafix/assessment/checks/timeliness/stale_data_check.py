from datetime import datetime

import pandas as pd

from eazydatafix.models.validation_result import ValidationResult


class StaleDataCheck:
    """
    Detects stale data based on configurable age.
    """

    def evaluate(
        self,
        df: pd.DataFrame,
        threshold_days: int = 365,
    ) -> list[ValidationResult]:

        results: list[ValidationResult] = []

        today = pd.Timestamp(datetime.today().date())

        for column in df.columns:

            column_name = column.lower()

            if not (
                "updated" in column_name
                or "modified" in column_name
                or "last_updated" in column_name
                or "lastmodified" in column_name
            ):
                continue

            dates = pd.to_datetime(
                df[column],
                errors="coerce",
            )

            stale_count = int(
                (
                    (today - dates).dt.days > threshold_days
                ).sum()
            )

            if stale_count == 0:

                results.append(
                    ValidationResult(
                        rule="Stale Data",
                        column=column,
                        passed=True,
                        message="No stale records found.",
                    )
                )

            else:

                results.append(
                    ValidationResult(
                        rule="Stale Data",
                        column=column,
                        passed=False,
                        message=f"{stale_count} stale record(s) found.",
                    )
                )

        return results
