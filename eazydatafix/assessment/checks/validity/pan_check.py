import re

import pandas as pd

from eazydatafix.models.validation_result import ValidationResult


class PanCheck:
    """
    Validates Indian PAN numbers.
    """

    PAN_PATTERN = re.compile(
        r"^[A-Z]{5}[0-9]{4}[A-Z]$"
    )

    def evaluate(
        self,
        df: pd.DataFrame,
    ) -> list[ValidationResult]:

        results: list[ValidationResult] = []

        for column in df.columns:

            column_name = column.lower()

            if "pan" not in column_name:
                continue

            invalid = 0

            for value in df[column].dropna():

                value = str(value).strip().upper()

                if not self.PAN_PATTERN.match(value):
                    invalid += 1

            if invalid == 0:

                results.append(
                    ValidationResult(
                        rule="PAN Number",
                        column=column,
                        passed=True,
                        message="All PAN numbers are valid.",
                    )
                )

            else:

                results.append(
                    ValidationResult(
                        rule="PAN Number",
                        column=column,
                        passed=False,
                        message=f"{invalid} invalid PAN number(s) found.",
                    )
                )

        return results
