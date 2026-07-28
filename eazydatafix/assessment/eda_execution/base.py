from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import Any

import pandas as pd

from eazydatafix.models.eda_plan import EDAPlanStep
from eazydatafix.models.eda_result import EDAResult


class EDAAnalysisHandler(ABC):
    """
    Defines one deterministic EDA plan-step handler.
    """

    name: str

    @abstractmethod
    def execute(
        self,
        dataframe: pd.DataFrame,
        result: EDAResult,
        step: EDAPlanStep,
    ) -> dict[str, Any]:
        """
        Execute the handler and return a serialisable output dictionary.
        """


def percentage(
    count: int | float,
    total: int | float,
) -> float:
    """
    Calculate a deterministic percentage rounded to two decimal places.
    """
    if not total:
        return 0.0

    return round(float(count) / float(total) * 100.0, 2)


def native_value(value: object) -> Any:
    """
    Convert common pandas and NumPy scalar values to JSON-compatible values.
    """
    if value is None:
        return None

    if isinstance(value, (pd.Timestamp, datetime, date)):
        return value.isoformat()

    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass

    item = getattr(value, "item", None)

    if callable(item):
        return item()

    if isinstance(value, (str, int, float, bool)):
        return value

    return str(value)


def float_or_none(value: object) -> float | None:
    """
    Convert a numeric scalar to float while representing missing values as None.
    """
    if value is None or pd.isna(value):
        return None

    return float(value)
