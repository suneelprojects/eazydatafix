import pandas as pd

from eazydatafix.contracts.fix_step import FixStep
from eazydatafix.core.column_profiler import ColumnProfiler
from eazydatafix.models.fix_config import FixConfig


class DataTypeConverter(FixStep):
    """Safely converts text columns to deterministic pandas data types."""

    _BOOLEAN_MAP = {
        "yes": True,
        "no": False,
        "y": True,
        "n": False,
        "true": True,
        "false": False,
    }
    _CURRENCY_SYMBOLS = r"[$£€₹]"

    def run(
        self,
        df: pd.DataFrame,
        config: FixConfig,
        applied_fixes: list[str],
    ) -> pd.DataFrame:
        """Convert only columns that meet the configured confidence threshold."""
        if not config.convert_data_types:
            return df

        converted: list[str] = []
        for column in df.select_dtypes(include=["object", "string", "category"]):
            series = df[column]
            semantic_type = ColumnProfiler.detect(column, series)

            # Identifiers and contact fields can contain only digits while still
            # being labels. Converting them would destroy leading zeroes.
            if semantic_type in {"IDENTIFIER", "EMAIL", "PHONE"}:
                continue

            boolean = self._boolean_candidate(series)
            if boolean is not None:
                df[column] = boolean
                converted.append(f"{column} -> boolean")
                continue

            if semantic_type == "DATE":
                parsed = pd.to_datetime(series, errors="coerce", format="mixed")
                ratio = self._conversion_ratio(series, parsed)
                if ratio >= config.date_parsing_threshold:
                    df[column] = parsed
                    converted.append(f"{column} -> datetime ({ratio:.0%} valid)")
                continue

            numeric, kind = self._numeric_candidate(series, semantic_type)
            ratio = self._conversion_ratio(series, numeric)
            if ratio >= config.numeric_conversion_threshold:
                df[column] = numeric
                converted.append(f"{column} -> {kind} ({ratio:.0%} valid)")

        if converted:
            applied_fixes.append("Converted data types: " + "; ".join(converted))

        return df

    @classmethod
    def _boolean_candidate(cls, series: pd.Series) -> pd.Series | None:
        """Return a nullable boolean series only for an unambiguous token set."""
        values = series.astype("string").str.strip().str.casefold()
        available = values.dropna()
        if available.empty or not available.isin(cls._BOOLEAN_MAP).all():
            return None
        return values.map(cls._BOOLEAN_MAP).astype("boolean")

    @classmethod
    def _numeric_candidate(
        cls,
        series: pd.Series,
        semantic_type: str,
    ) -> tuple[pd.Series, str]:
        """Build a numeric candidate while preserving explicit unit semantics."""
        values = series.astype("string").str.strip()
        available = values.dropna()
        all_percent = not available.empty and available.str.endswith("%").all()
        has_currency = semantic_type == "CURRENCY" or (
            not available.empty and available.str.contains(cls._CURRENCY_SYMBOLS, regex=True).all()
        )

        normalized = values.str.replace(",", "", regex=False)
        if has_currency:
            normalized = normalized.str.replace(cls._CURRENCY_SYMBOLS, "", regex=True).str.strip()
        if all_percent:
            normalized = normalized.str.removesuffix("%").str.strip()

        converted = pd.to_numeric(normalized, errors="coerce")
        if all_percent:
            converted = converted / 100
            kind = "percentage"
        elif has_currency:
            kind = "currency numeric"
        else:
            kind = "numeric"
        return converted, kind

    @staticmethod
    def _conversion_ratio(source: pd.Series, converted: pd.Series) -> float:
        """Return the share of non-missing source values converted successfully."""
        available = int(source.notna().sum())
        return 1.0 if available == 0 else float(converted.notna().sum() / available)
