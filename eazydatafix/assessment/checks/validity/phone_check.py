import re

import pandas as pd

from eazydatafix.models.validation_result import ValidationResult


class PhoneCheck:
    """
    Validates phone numbers.
    """

    PHONE_PATTERN = re.compile(
        r"^\+?[1-9]\d{9,14}$"
    )

    def evaluate(
        self,
        df: pd.DataFrame,
    ) -> list[ValidationResult]:

        results: list[ValidationResult] = []

        for column in df.columns:

            column_name = column.lower()

            if (
                "phone" not in column_name
                and "mobile" not in column_name
                and "contact" not in column_name
            ):
                continue

            invalid = 0

            for value in df[column].dropna():

                value = str(value).strip()

                if not self.PHONE_PATTERN.match(value):
                    invalid += 1

            if invalid == 0:

                results.append(
                    ValidationResult(
                        rule="Phone Number",
                        column=column,
                        passed=True,
                        message="All phone numbers are valid.",
                    )
                )

            else:

                results.append(
                    ValidationResult(
                        rule="Phone Number",
                        column=column,
                        passed=False,
                        message=f"{invalid} invalid phone number(s) found.",
                    )
                )

        return results
