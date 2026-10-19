"""Explicit conversions used by recipe pipelines, without heuristic inference."""

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

import numpy as np
import pandas as pd

from eazydatafix.pipeline.recipe import ColumnRule


@dataclass(slots=True)
class ConversionResult:
    """Return a typed candidate and the rows that cannot satisfy a declared type."""

    values: pd.Series
    invalid: pd.Series
    reason: str


class ExplicitConverter:
    """Apply literal mappings and declared types without discarding invalid values."""

    @classmethod
    def convert(cls, source: pd.Series, rule: ColumnRule) -> ConversionResult:
        """Build a candidate; the pipeline applies the declared error policy."""
        values = source.copy()
        if rule.missing_markers:
            marker_mask = (
                values.astype("string")
                .str.casefold()
                .isin([x.casefold() for x in rule.missing_markers])
            )
            values = values.astype("object").mask(marker_mask, pd.NA)
        if rule.category_mapping:
            values = values.astype("string").replace(rule.category_mapping)
        if rule.fill_value is not None:
            values = values.astype("object").fillna(rule.fill_value)
        invalid = pd.Series(False, index=source.index)
        if rule.dtype is None:
            return ConversionResult(values, invalid, "")
        if rule.dtype in {"string", "category"}:
            converted = values.astype("string")
            if rule.dtype == "category":
                converted = converted.astype("category")
        elif rule.dtype == "datetime":
            if pd.api.types.is_datetime64_any_dtype(values):
                converted = values.copy()
            else:
                converted = pd.to_datetime(values, format=rule.date_format, errors="coerce")
        elif rule.dtype == "boolean":
            mapping = {
                "true": True,
                "false": False,
                "yes": True,
                "no": False,
                "y": True,
                "n": False,
                "1": True,
                "0": False,
            }
            converted = values.astype("string").str.strip().str.casefold().map(mapping)
            # Actual numeric booleans are accepted without treating '1.0' text as a token.
            if pd.api.types.is_numeric_dtype(values) and not pd.api.types.is_bool_dtype(values):
                converted = values.map({1: True, 0: False})
            converted = converted.astype("boolean")
        else:
            converted = cls._numeric(values, rule)
        invalid = values.notna() & converted.isna()
        return ConversionResult(
            converted,
            invalid,
            f"Value does not satisfy the declared {rule.dtype} rule.",
        )

    @staticmethod
    def _numeric(values: pd.Series, rule: ColumnRule) -> pd.Series:
        if pd.api.types.is_numeric_dtype(values) and not pd.api.types.is_bool_dtype(values):
            normalized = values.astype("string")
            already_numeric = True
        else:
            normalized = values.astype("string").str.strip()
            already_numeric = False
            # Currency symbols are removed only at the boundaries, not from arbitrary text.
            for symbol in rule.currency_symbols:
                normalized = (
                    normalized.str.removeprefix(symbol).str.removesuffix(symbol).str.strip()
                )
            if rule.thousands_separator:
                normalized = normalized.str.replace(rule.thousands_separator, "", regex=False)
            if rule.decimal_separator != ".":
                normalized = normalized.str.replace(rule.decimal_separator, ".", regex=False)
        percent_mask = normalized.str.endswith("%", na=False) if rule.percentage else None
        if rule.percentage:
            normalized = normalized.str.removesuffix("%").str.strip()
        if rule.dtype == "integer":
            # Decimal avoids float rounding of integer identifiers and Int64 overflow.
            parsed: list[int | None] = []
            for token in normalized:
                try:
                    number = Decimal(token) if pd.notna(token) else None
                    valid = (
                        number is not None
                        and number.is_finite()
                        and number == number.to_integral_value()
                        and -(2**63) <= number <= 2**63 - 1
                    )
                    parsed.append(int(number) if valid else None)
                except (InvalidOperation, ValueError, TypeError):
                    parsed.append(None)
            return pd.Series(parsed, index=values.index, dtype="Int64")
        converted = pd.to_numeric(normalized, errors="coerce").astype("Float64")
        converted = converted.mask(~np.isfinite(converted.fillna(0)))
        if rule.percentage and not already_numeric:
            converted = converted.where(~percent_mask, converted / 100)
        return converted
