from dataclasses import dataclass
from typing import Any

from eazydatafix.models.serialization import to_json_compatible


@dataclass(slots=True)
class GeneratedVisualisation:
    """Represents one successfully generated visualisation artifact."""

    type: str
    target_columns: list[str]
    path: str
    source_step: str


@dataclass(slots=True)
class SkippedVisualisation:
    """Records why a recommended visualisation was not generated."""

    type: str
    target_columns: list[str]
    reason: str
    source_step: str


@dataclass(slots=True)
class AgenticEDAReportResult:
    """Represents deterministic Agentic EDA report export artifacts."""

    output_directory: str
    generated_files: list[str]
    generated_visualisations: list[GeneratedVisualisation]
    skipped_visualisations: list[SkippedVisualisation]
    warnings: list[str]
    deterministic_summary: str
    status: str

    def to_dict(self) -> dict[str, Any]:
        """
        Convert report artifact metadata into JSON-compatible structures.

        Returns:
            A nested dictionary containing only JSON-compatible values.
        """
        return to_json_compatible(self)
