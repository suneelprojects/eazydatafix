from pathlib import Path

import pandas as pd

from eazydatafix.core.column_profiler import ColumnProfiler
from eazydatafix.core.dataset_loader import DatasetLoader
from eazydatafix.models.preparation_report import PreparationReport
from eazydatafix.models.prepare_config import PrepareConfig


class PrepareEngine:
    """
    Prepares a dataset for analysis.

    This engine performs safe transformations without
    changing the meaning of the data.
    """

    def prepare(
        self,
        dataset: str | Path | pd.DataFrame,
        config: PrepareConfig | None = None,
    ) -> pd.DataFrame:
        """
        Prepare a supported dataset for downstream analysis.

        Args:
            dataset: A pandas DataFrame or path to a supported dataset file.

        Returns:
            A prepared pandas DataFrame.
        """

        return self.prepare_with_report(dataset, config).dataset

    def prepare_with_report(
        self,
        dataset: str | Path | pd.DataFrame,
        config: PrepareConfig | None = None,
    ) -> PreparationReport:
        """Prepare a dataset and return deterministic transformation details."""
        config = config or PrepareConfig()
        df = DatasetLoader.load(dataset).copy()
        before_shape = df.shape
        before_types = {column: str(dtype) for column, dtype in df.dtypes.items()}
        changes: list[str] = []
        warnings: list[str] = []

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

            if semantic_type == "DATE" and self._parse_date_column(
                df, column, config, changes, warnings
            ):
                continue

            # -------------------------------------
            # Currency
            # -------------------------------------

            if semantic_type == "CURRENCY":

                converted = pd.to_numeric(series, errors="coerce")
                if self._conversion_ratio(series, converted) >= config.numeric_conversion_threshold:
                    df[column] = converted.astype("float32")
                    changes.append(f"Converted currency-like column '{column}' to numeric.")

                continue

            # -------------------------------------
            # Boolean
            # -------------------------------------

            if semantic_type == "BOOLEAN":

                mapped = series.astype("string").str.strip().str.lower().map(boolean_map)
                if mapped.notna().sum() == series.notna().sum():
                    df[column] = mapped.astype("boolean")
                    changes.append(f"Converted boolean column '{column}'.")

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
                converted = pd.to_numeric(series, errors="coerce")
                if self._conversion_ratio(series, converted) >= config.numeric_conversion_threshold:
                    df[column] = converted
                    changes.append(f"Converted text column '{column}' to numeric.")
                else:
                    df[column] = series.astype("string")

        if config.normalize_text:
            self._normalize_text(df, changes)
        if config.remove_duplicates:
            self._remove_duplicates(df, changes)
        self._handle_outliers(df, config, changes, warnings)
        self._derive_date_parts(df, config, changes, warnings)

        return PreparationReport(
            dataset=df,
            config=config,
            changes=changes,
            warnings=warnings,
            shape_before=before_shape,
            shape_after=df.shape,
            data_types_before=before_types,
            data_types_after={column: str(dtype) for column, dtype in df.dtypes.items()},
        )

    @staticmethod
    def _conversion_ratio(source: pd.Series, converted: pd.Series) -> float:
        """Return the fraction of non-missing values converted successfully."""
        available = int(source.notna().sum())
        return 1.0 if available == 0 else float(converted.notna().sum() / available)

    def _parse_date_column(
        self,
        df: pd.DataFrame,
        column: str,
        config: PrepareConfig,
        changes: list[str],
        warnings: list[str],
    ) -> bool:
        """Parse date-like columns only when their conversion is sufficiently reliable."""
        series = df[column]
        if pd.api.types.is_datetime64_any_dtype(series):
            return True
        parsed = pd.to_datetime(series, errors="coerce", format="mixed")
        ratio = self._conversion_ratio(series, parsed)
        if ratio >= config.date_parsing_threshold:
            df[column] = parsed
            changes.append(f"Parsed date-like column '{column}' ({ratio:.0%} valid).")
            return True
        warnings.append(f"Kept '{column}' unchanged because only {ratio:.0%} parsed as dates.")
        return False

    @staticmethod
    def _normalize_text(df: pd.DataFrame, changes: list[str]) -> None:
        """Normalize surrounding and repeated whitespace in text columns."""
        normalized: list[str] = []
        for column in df.select_dtypes(include=["object", "string"]):
            before = df[column].copy()
            df[column] = (
                df[column].astype("string").str.strip().str.replace(r"\s+", " ", regex=True)
            )
            if not before.equals(df[column]):
                normalized.append(column)
        if normalized:
            changes.append("Normalized text whitespace: " + ", ".join(normalized))

    @staticmethod
    def _remove_duplicates(df: pd.DataFrame, changes: list[str]) -> None:
        """Remove exact duplicate rows only when explicitly configured."""
        count = int(df.duplicated().sum())
        if count:
            df.drop_duplicates(inplace=True)
            changes.append(f"Removed {count} duplicate row(s).")

    @staticmethod
    def _handle_outliers(
        df: pd.DataFrame,
        config: PrepareConfig,
        changes: list[str],
        warnings: list[str],
    ) -> None:
        """Apply deterministic IQR outlier controls without touching identifiers."""
        if config.outlier_action == "none":
            return
        for column in df.select_dtypes(include="number"):
            if ColumnProfiler.detect(column, df[column]) == "IDENTIFIER":
                continue
            series = df[column].dropna()
            if len(series) < 4:
                continue
            lower = series.quantile(0.25) - 1.5 * (series.quantile(0.75) - series.quantile(0.25))
            upper = series.quantile(0.75) + 1.5 * (series.quantile(0.75) - series.quantile(0.25))
            mask = (df[column] < lower) | (df[column] > upper)
            count = int(mask.sum())
            if not count:
                continue
            if config.outlier_action == "flag":
                flag_column = f"{column}_is_outlier"
                if flag_column in df.columns:
                    warnings.append(
                        f"Skipped outlier flag for '{column}' because "
                        f"'{flag_column}' already exists."
                    )
                    continue
                df[flag_column] = mask.astype("boolean")
                changes.append(f"Flagged {count} IQR outlier(s) in '{column}'.")
            elif config.outlier_action == "cap":
                df[column] = df[column].clip(lower=lower, upper=upper)
                changes.append(f"Capped {count} IQR outlier(s) in '{column}'.")
            else:
                df.drop(index=df.index[mask], inplace=True)
                changes.append(f"Dropped {count} row(s) with IQR outliers in '{column}'.")

    @staticmethod
    def _derive_date_parts(
        df: pd.DataFrame,
        config: PrepareConfig,
        changes: list[str],
        warnings: list[str],
    ) -> None:
        """Derive configured analytical fields from parsed datetime columns."""
        if not config.derive_date_parts:
            return

        extractors = {
            "year": lambda series: series.dt.year.astype("Int16"),
            "quarter": lambda series: series.dt.quarter.astype("Int8"),
            "month": lambda series: series.dt.month.astype("Int8"),
            "month_name": lambda series: series.dt.month_name().astype("string"),
            "week": lambda series: series.dt.isocalendar().week.astype("Int16"),
            "day": lambda series: series.dt.day.astype("Int8"),
            "day_of_week": lambda series: series.dt.day_name().astype("string"),
            "is_weekend": lambda series: series.dt.dayofweek.ge(5).astype("boolean"),
        }

        date_columns = list(df.select_dtypes(include=["datetime", "datetimetz"]).columns)
        for column in date_columns:
            created: list[str] = []
            for part in config.derive_date_parts:
                derived_column = f"{column}_{part}"
                if derived_column in df.columns:
                    warnings.append(
                        f"Skipped date part '{part}' for '{column}' because "
                        f"'{derived_column}' already exists."
                    )
                    continue
                df[derived_column] = extractors[part](df[column])
                created.append(derived_column)
            if created:
                changes.append(f"Derived date parts from '{column}': " + ", ".join(created) + ".")
