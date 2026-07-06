import re

import pandas as pd

from easydatafix.models.validation_result import ValidationResult


class CreditCardCheck:
    """
    Validates credit card numbers using the Luhn algorithm.
    """

    def evaluate(
        self,
        df: pd.DataFrame,
    ) -> list[ValidationResult]:

        results: list[ValidationResult] = []

        for column in df.columns:

            column_name = column.lower()

            if (
                "card" not in column_name
                and "credit" not in column_name
            ):
                continue

            invalid = 0

            for value in df[column].dropna():

                number = re.sub(
                    r"\D",
                    "",
                    str(value),
                )

                if (
                    len(number) < 13
                    or len(number) > 19
                    or not self._luhn(number)
                ):
                    invalid += 1

            if invalid == 0:

                results.append(
                    ValidationResult(
                        rule="Credit Card",
                        column=column,
                        passed=True,
                        message="All credit card numbers are valid.",
                    )
                )

            else:

                results.append(
                    ValidationResult(
                        rule="Credit Card",
                        column=column,
                        passed=False,
                        message=f"{invalid} invalid credit card number(s) found.",
                    )
                )

        return results

    @staticmethod
    def _luhn(number: str) -> bool:

        total = 0

        reverse_digits = number[::-1]

        for index, digit in enumerate(reverse_digits):

            value = int(digit)

            if index % 2 == 1:

                value *= 2

                if value > 9:
                    value -= 9

            total += value

        return total % 10 == 0
