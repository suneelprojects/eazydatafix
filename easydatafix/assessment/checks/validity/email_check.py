import re

import pandas as pd

from easydatafix.models.validation_result import ValidationResult


class EmailCheck:
    """
    Validates email addresses.
    """

    EMAIL_PATTERN = re.compile(
        r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
    )

    def evaluate(
        self,
        df: pd.DataFrame,
    ) -> list[ValidationResult]:

        results: list[ValidationResult] = []

        for column in df.columns:

            if "email" not in column.lower():
                continue

            invalid = 0

            for value in df[column].dropna():

                value = str(value).strip()

                if not self.EMAIL_PATTERN.match(value):
                    invalid += 1

            if invalid == 0:

                results.append(
                    ValidationResult(
                        rule="Email Format",
                        column=column,
                        passed=True,
                        message="All email addresses are valid.",
                    )
                )

            else:

                results.append(
                    ValidationResult(
                        rule="Email Format",
                        column=column,
                        passed=False,
                        message=f"{invalid} invalid email address(es) found.",
                    )
                )

        return results
