import re

import pandas as pd

from easydatafix.models.validation_result import ValidationResult


class UrlCheck:
    """
    Validates URL columns.
    """

    URL_PATTERN = re.compile(
        r"^(https?://)?([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}(/.*)?$"
    )

    def evaluate(
        self,
        df: pd.DataFrame,
    ) -> list[ValidationResult]:

        results: list[ValidationResult] = []

        for column in df.columns:

            column_name = column.lower()

            if (
                "url" not in column_name
                and "website" not in column_name
                and "link" not in column_name
            ):
                continue

            invalid = 0

            for value in df[column].dropna():

                value = str(value).strip()

                if not self.URL_PATTERN.match(value):
                    invalid += 1

            if invalid == 0:

                results.append(
                    ValidationResult(
                        rule="URL Format",
                        column=column,
                        passed=True,
                        message="All URLs are valid.",
                    )
                )

            else:

                results.append(
                    ValidationResult(
                        rule="URL Format",
                        column=column,
                        passed=False,
                        message=f"{invalid} invalid URL(s) found.",
                    )
                )

        return results
