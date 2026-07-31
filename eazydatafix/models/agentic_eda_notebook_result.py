from dataclasses import dataclass
from typing import Any

from eazydatafix.models.serialization import to_json_compatible


@dataclass(slots=True)
class AgenticEDANotebookResult:
    """Represents deterministic Agentic EDA notebook export artifacts."""

    notebook_path: str
    generated_files: list[str]
    companion_files: list[str]
    cell_count: int
    notebook_format_version: int
    deterministic_summary: str
    status: str

    def to_dict(self) -> dict[str, Any]:
        """
        Convert notebook artifact metadata into JSON-compatible structures.

        Returns:
            A nested dictionary containing only JSON-compatible values.
        """
        return to_json_compatible(self)
