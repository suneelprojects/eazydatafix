from dataclasses import dataclass


@dataclass(slots=True)
class DatasetInfo:
    """
    Basic information about a dataset.
    """

    file_name: str
    rows: int
    columns: int
    memory_usage_bytes: int
