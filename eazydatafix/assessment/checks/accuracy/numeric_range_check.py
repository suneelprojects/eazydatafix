import pandas as pd

from eazydatafix.models.validation_result import ValidationResult


class NumericRangeCheck:
    """
    Detects numeric values outside acceptable ranges.
    """

    DEFAULT_RANGES = {
        "age": (0, 120),
        "salary": (0, 1_000_000_000),
        "marks": (0, 100),
        "percentage": (0, 100),
        "score": (0, 100),
        "rating": (0, 5),
    }

    def evaluate(
        self,
        df: pd.DataFrame,
    ) -> list[ValidationResult]:

        results: list[ValidationResult] = []

        for column in df.columns:

            column_name = column.lower()

            if column_name not in self.DEFAULT_RANGES:
                continue

            minimum, maximum = self.DEFAULT_RANGES[column_name]

            invalid = 0

            numeric_values = pd.to_numeric(
                df[column],
                errors="coerce",
            )

            for value in numeric_values.dropna():

                if value < minimum or value > maximum:
                    invalid += 1

            if invalid == 0:

                results.append(
                    ValidationResult(
                        rule="Numeric Range",
                        column=column,
                        passed=True,
                        message="All values are within the expected range.",
                    )
                )

            else:

                results.append(
                    ValidationResult(
                        rule="Numeric Range",
                        column=column,
                        passed=False,
                        message=f"{invalid} value(s) outside the expected range.",
                    )
                )

        return results
