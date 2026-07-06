import ipaddress

import pandas as pd

from easydatafix.models.validation_result import ValidationResult


class IpAddressCheck:
    """
    Validates IPv4 and IPv6 address columns.
    """

    def evaluate(
        self,
        df: pd.DataFrame,
    ) -> list[ValidationResult]:

        results: list[ValidationResult] = []

        for column in df.columns:

            column_name = column.lower()

            if (
                "ip" not in column_name
                and "ip_address" not in column_name
                and "ipaddress" not in column_name
            ):
                continue

            invalid = 0

            for value in df[column].dropna():

                try:
                    ipaddress.ip_address(str(value).strip())

                except ValueError:
                    invalid += 1

            if invalid == 0:

                results.append(
                    ValidationResult(
                        rule="IP Address",
                        column=column,
                        passed=True,
                        message="All IP addresses are valid.",
                    )
                )

            else:

                results.append(
                    ValidationResult(
                        rule="IP Address",
                        column=column,
                        passed=False,
                        message=f"{invalid} invalid IP address(es) found.",
                    )
                )

        return results
