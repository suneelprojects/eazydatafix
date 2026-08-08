from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CleaningChange:
    """Records the deterministic before-and-after effect of one cleaning stage."""

    step: str
    description: str
    rows_before: int
    rows_after: int
    columns_before: int
    columns_after: int
    missing_values_before: int
    missing_values_after: int
    applied: bool
