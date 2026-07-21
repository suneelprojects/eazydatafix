from pathlib import Path

import pandas as pd

from eazydatafix.core.column_profiler import ColumnProfiler
from eazydatafix.core.dataset_loader import DatasetLoader


class PrepareEngine:
    """
    Prepares a dataset for analysis.

    This engine performs safe transformations without
    changing the meaning of the data.
    """

    def prepare(
        self,
        dataset: str | Path | pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Prepare a supported dataset for downstream analysis.

        Args:
            dataset: A pandas DataFrame or path to a supported dataset file.

        Returns:
            A prepared pandas DataFrame.
        """

        df = DatasetLoader.load(dataset).copy()

        boolean_map = {
            "yes": True,
            "no": False,
            "y": True,
            "n": False,
            "true": True,
            "false": False,
            "1": True,
            "0": False,
        }

        for column in df.columns:

            series = df[column]

            semantic_type = ColumnProfiler.detect(
                column,
                series,
            )

            # -------------------------------------
            # Identifier
            # -------------------------------------

            if semantic_type == "IDENTIFIER":

                df[column] = series.astype("string")
                continue

            # -------------------------------------
            # Email
            # -------------------------------------

            if semantic_type == "EMAIL":

                df[column] = series.astype("string")
                continue

            # -------------------------------------
            # Phone
            # -------------------------------------

            if semantic_type == "PHONE":

                df[column] = series.astype("string")
                continue

            # -------------------------------------
            # Date
            # -------------------------------------

            if semantic_type == "DATE":

                df[column] = pd.to_datetime(
                    series,
                    errors="coerce",
                )

                continue

            # -------------------------------------
            # Currency
            # -------------------------------------

            if semantic_type == "CURRENCY":

                df[column] = (
                    pd.to_numeric(
                        series,
                        errors="coerce",
                    )
                    .astype("float32")
                )

                continue

            # -------------------------------------
            # Boolean
            # -------------------------------------

            if semantic_type == "BOOLEAN":

                df[column] = (
                    series.astype(str)
                    .str.strip()
                    .str.lower()
                    .map(boolean_map)
                    .astype(bool)
                )

                continue

            # -------------------------------------
            # Category
            # -------------------------------------

            if semantic_type == "CATEGORY":

                df[column] = series.astype("category")
                continue

            # -------------------------------------
            # Numeric Optimization
            # -------------------------------------

            if pd.api.types.is_integer_dtype(series):

                df[column] = pd.to_numeric(
                    series,
                    downcast="integer",
                )

                continue

            if pd.api.types.is_float_dtype(series):

                df[column] = pd.to_numeric(
                    series,
                    downcast="float",
                )

                continue

            # -------------------------------------
            # Remaining Text Columns
            # -------------------------------------

            if pd.api.types.is_string_dtype(series):

                df[column] = series.astype("string")

        return df
