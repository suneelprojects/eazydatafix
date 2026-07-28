import math
from dataclasses import dataclass, fields, is_dataclass
from datetime import date, datetime
from enum import Enum
from typing import Any

from eazydatafix.models.eda_plan import EDAPlan
from eazydatafix.models.eda_result import EDAResult


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
        return _json_compatible(self)


def _json_compatible(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _json_compatible(getattr(value, field.name)) for field in fields(value)}

    if isinstance(value, dict):
        return {str(key): _json_compatible(item) for key, item in value.items()}

    if isinstance(value, (list, tuple)):
        return [_json_compatible(item) for item in value]

    if isinstance(value, Enum):
        return _json_compatible(value.value)

    if isinstance(value, (datetime, date)):
        return value.isoformat()

    if isinstance(value, float) and not math.isfinite(value):
        return None

    item = getattr(value, "item", None)

    if callable(item):
        return _json_compatible(item())

    if value is None or isinstance(value, (str, int, float, bool)):
        return value

    return str(value)
