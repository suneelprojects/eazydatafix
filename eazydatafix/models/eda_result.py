from dataclasses import dataclass
from typing import Any

from eazydatafix.models.dataset_profile import DatasetProfile


@dataclass(slots=True)
class EDAResult:
    """
    Represents a deterministic exploratory data analysis result.
    """

    dataset_profile: DatasetProfile
    shape: tuple[int, int]
    column_names: list[str]
    data_types: dict[str, str]
    missing_values: dict[str, int]
    duplicate_rows: int
    numeric_statistics: dict[str, dict[str, float | None]]
    categorical_summaries: dict[str, dict[str, Any]]
    unique_value_counts: dict[str, int]
    correlation_matrix: dict[str, dict[str, float | None]]
    numeric_columns: list[str]
    categorical_columns: list[str]
    observations: list[str]
    recommendations: list[str]
