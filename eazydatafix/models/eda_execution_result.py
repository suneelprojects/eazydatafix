from dataclasses import dataclass
from typing import Any

from eazydatafix.models.eda_plan import EDAPlan
from eazydatafix.models.eda_result import EDAResult
from eazydatafix.models.serialization import to_json_compatible


@dataclass(slots=True)
class EDAExecutionStepResult:
    """
    Represents the deterministic execution outcome for one analysis step.
    """

    name: str
    status: str
    reason: str
    priority: str
    required_columns: list[str]
    dependencies: list[str]
    output: dict[str, Any] | None
    error: str | None


@dataclass(slots=True)
class EDAExecutionResult:
    """
    Represents a reproducible execution of a deterministic EDA plan.
    """

    eda_result: EDAResult
    eda_plan: EDAPlan
    executed_steps: list[EDAExecutionStepResult]
    skipped_steps: list[EDAExecutionStepResult]
    execution_order: list[str]
    warnings: list[str]
    deterministic_summary: str
    status: str

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the complete execution result into JSON-compatible structures.

        Returns:
            A nested dictionary containing only dataclass and native values.
        """
        return to_json_compatible(self)
