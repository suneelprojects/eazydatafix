import re

import pandas as pd


class ColumnProfiler:
    """
    Detects the semantic meaning of a column.

    Unlike pandas dtypes, this profiler tries to
    understand what the column actually represents.
    """

    EMAIL_PATTERN = re.compile(
        r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
    )

    IDENTIFIER_COLUMNS = {
        "id",
        "uuid",
        "identifier",
    }

    NAME_COLUMNS = {
        "name",
        "first_name",
        "last_name",
        "fullname",
        "full_name",
    }

    @classmethod
    def detect(
        cls,
        column_name: str,
        series: pd.Series,
    ) -> str:

        name = column_name.lower().strip()

        # ------------------------------------------
        # Identifier
        # ------------------------------------------

        if (
            name in cls.IDENTIFIER_COLUMNS
            or name.endswith("_id")
        ):
            return "IDENTIFIER"

        # ------------------------------------------
        # Person Name
        # ------------------------------------------

        if name in cls.NAME_COLUMNS:
            return "TEXT"

        # ------------------------------------------
        # Email
        # ------------------------------------------

        if "email" in name:
            return "EMAIL"

        # ------------------------------------------
        # Phone
        # ------------------------------------------

        if any(
            keyword in name
            for keyword in (
                "phone",
                "mobile",
                "contact",
            )
        ):
            return "PHONE"

        # ------------------------------------------
        # Date
        # ------------------------------------------

        if any(
            keyword in name
            for keyword in (
                "date",
                "dob",
                "created",
                "updated",
                "joined",
                "join",
            )
        ):
            return "DATE"

        # ------------------------------------------
        # Currency
        # ------------------------------------------

        if any(
            keyword in name
            for keyword in (
                "salary",
                "amount",
                "price",
                "cost",
                "income",
                "fare",
            )
        ):
            return "CURRENCY"

        # ------------------------------------------
        # Boolean
        # ------------------------------------------

        if pd.api.types.is_bool_dtype(series):
            return "BOOLEAN"

        # ------------------------------------------
        # Datetime
        # ------------------------------------------

        if pd.api.types.is_datetime64_any_dtype(series):
            return "DATE"

        # ------------------------------------------
        # Numeric
        # ------------------------------------------

        if pd.api.types.is_numeric_dtype(series):
            return "NUMERIC"

        # ------------------------------------------
        # Category
        # ------------------------------------------

        if pd.api.types.is_string_dtype(series):

            unique = series.nunique(dropna=True)
            ratio = unique / max(len(series), 1)

            if unique <= 100 and ratio <= 0.20:
                return "CATEGORY"

        # ------------------------------------------
        # Default
        # ------------------------------------------

        return "TEXT"
