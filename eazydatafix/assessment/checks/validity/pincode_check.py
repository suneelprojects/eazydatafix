import re

import pandas as pd

from eazydatafix.models.validation_result import ValidationResult


class PincodeCheck:
    """
    Validates Indian PIN codes.
    """

    PIN_PATTERN = re.compile(r"^[1-9][0-9]{5}$")

    def evaluate(
        self,
        df: pd.DataFrame,
    ) -> list[ValidationResult]:

        results = []

        for column in df.columns:

            column_name = column.lower()

            if (
                "pincode" not in column_name
                and "pin" not in column_name
                and "zipcode" not in column_name
                and "postal" not in column_name
            ):
                continue

            invalid = 0

            for value in df[column].dropna():

                value = str(value).strip()

                if not self.PIN_PATTERN.match(value):
                    invalid += 1

            if invalid == 0:

                results.append(
                    ValidationResult(
                        rule="PIN Code",
                        column=column,
                        passed=True,
                        message="All PIN codes are valid.",
                    )
                )

            else:

                results.append(
                    ValidationResult(
                        rule="PIN Code",
                        column=column,
                        passed=False,
                        message=f"{invalid} invalid PIN code(s) found.",
                    )
                )

        return results
