import re

import pandas as pd

from eazydatafix.models.validation_result import ValidationResult


class AadhaarCheck:
    """
    Validates Aadhaar numbers.
    """

    AADHAAR_PATTERN = re.compile(r"^[2-9][0-9]{11}$")

    def evaluate(
        self,
        df: pd.DataFrame,
    ) -> list[ValidationResult]:

        results: list[ValidationResult] = []

        for column in df.columns:

            column_name = column.lower()

            if (
                "aadhaar" not in column_name
                and "aadhar" not in column_name
            ):
                continue

            invalid = 0

            for value in df[column].dropna():

                value = str(value).replace(" ", "").strip()

                if not self.AADHAAR_PATTERN.match(value):
                    invalid += 1

            if invalid == 0:

                results.append(
                    ValidationResult(
                        rule="Aadhaar Number",
                        column=column,
                        passed=True,
                        message="All Aadhaar numbers are valid.",
                    )
                )

            else:

                results.append(
                    ValidationResult(
                        rule="Aadhaar Number",
                        column=column,
                        passed=False,
                        message=f"{invalid} invalid Aadhaar number(s) found.",
                    )
                )

        return results
