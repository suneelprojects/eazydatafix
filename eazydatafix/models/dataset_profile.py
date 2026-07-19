from dataclasses import dataclass
from typing import List


@dataclass(slots=True)
class DatasetProfile:
    """
    Represents the structural profile of a dataset.

    The DatasetProfile contains descriptive information only.
    It does not perform any quality assessment.
    """

    file_name: str
    file_type: str

    rows: int
    columns: int

    column_names: List[str]
    data_types: List[str]

    memory_usage_bytes: int
