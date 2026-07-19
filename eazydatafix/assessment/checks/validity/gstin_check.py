import re

import pandas as pd

from eazydatafix.models.validation_result import ValidationResult


class GstinCheck:
    """
    Validates Indian GSTIN numbers.
    """

    GSTIN_PATTERN = re.compile(
        r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]$"
    )

    def evaluate(
        self,
        df: pd.DataFrame,
    ) -> list[ValidationResult]:

        results: list[ValidationResult] = []

        for column in df.columns:

            column_name = column.lower()

            if (
                "gst" not in column_name
                and "gstin" not in column_name
            ):
                continue

            invalid = 0

            for value in df[column].dropna():

                value = str(value).strip().upper()

                if not self.GSTIN_PATTERN.match(value):
                    invalid += 1

            if invalid == 0:

                results.append(
                    ValidationResult(
                        rule="GSTIN",
                        column=column,
                        passed=True,
                        message="All GSTIN numbers are valid.",
                    )
                )

            else:

                results.append(
                    ValidationResult(
                        rule="GSTIN",
                        column=column,
                        passed=False,
                        message=f"{invalid} invalid GSTIN number(s) found.",
                    )
                )

        return results
