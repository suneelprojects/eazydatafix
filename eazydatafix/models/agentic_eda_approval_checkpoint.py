from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from eazydatafix.models.agentic_eda_config import AgenticEDAConfig
from eazydatafix.models.eda_plan import EDAPlan
from eazydatafix.models.eda_result import EDAResult
from eazydatafix.models.serialization import to_json_compatible


@dataclass(frozen=True, slots=True)
class AgenticEDAApprovalCheckpoint:
    """
    Snapshots a deterministic Agentic EDA plan for explicit human review.

    The checkpoint is created before analysis execution. Its EDA result,
    original plan, configuration, and ordered approval decisions are copied so
    later workflow stages cannot mutate caller-owned checkpoint state.
    """

    eda_result: EDAResult
    eda_plan: EDAPlan
    approval_status: str
    approved_step_ids: tuple[str, ...]
    rejected_step_ids: tuple[str, ...]
    reviewer: str | None
    notes: str | None
    config: AgenticEDAConfig
    dataset_fingerprint: str
    snapshot_fingerprint: str
    deterministic_summary: str

    def __post_init__(self) -> None:
        """Copy nested workflow snapshots and normalise ordered step IDs."""
        object.__setattr__(self, "eda_result", deepcopy(self.eda_result))
        object.__setattr__(self, "eda_plan", deepcopy(self.eda_plan))
        object.__setattr__(self, "config", deepcopy(self.config))
        object.__setattr__(self, "approved_step_ids", tuple(self.approved_step_ids))
        object.__setattr__(self, "rejected_step_ids", tuple(self.rejected_step_ids))

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the checkpoint to deterministic JSON-compatible structures.

        Returns:
            A nested dictionary containing only JSON-compatible values.
        """
        return to_json_compatible(self)
