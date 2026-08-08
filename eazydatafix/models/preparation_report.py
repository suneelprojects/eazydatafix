from dataclasses import dataclass

import pandas as pd

from eazydatafix.models.prepare_config import PrepareConfig


@dataclass(slots=True)
class PreparationReport:
    """Describes deterministic preparation changes without mutating caller data."""

    dataset: pd.DataFrame
    config: PrepareConfig
    changes: list[str]
    warnings: list[str]
    shape_before: tuple[int, int]
    shape_after: tuple[int, int]
    data_types_before: dict[str, str]
    data_types_after: dict[str, str]
