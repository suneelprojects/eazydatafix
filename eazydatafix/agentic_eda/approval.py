import hashlib
import json
from collections.abc import Sequence
from copy import deepcopy
from pathlib import Path

import pandas as pd

from eazydatafix.agentic_eda.engine import (
    AgenticEDAOrchestrator,
    _validate_agentic_eda_config,
)
from eazydatafix.assessment.eda import EDAEngine
from eazydatafix.assessment.eda_planner import EDAPlanner
from eazydatafix.assessment.eda_validation import load_eda_frame
from eazydatafix.models.agentic_eda_approval_checkpoint import (
    AgenticEDAApprovalCheckpoint,
)
from eazydatafix.models.agentic_eda_config import AgenticEDAConfig
from eazydatafix.models.agentic_eda_result import AgenticEDAResult
from eazydatafix.models.eda_plan import EDAPlan, EDAPlanStep
from eazydatafix.models.eda_result import EDAResult
from eazydatafix.models.serialization import to_json_compatible


class AgenticEDAApprovalEngine:
    """Coordinates deterministic Agentic EDA approval checkpoints."""

    def __init__(
        self,
        eda_engine: EDAEngine | None = None,
        planner: EDAPlanner | None = None,
        orchestrator: AgenticEDAOrchestrator | None = None,
    ) -> None:
        """
        Initialise approval handling with optional compatible components.

        Args:
            eda_engine: Optional dataset-understanding engine.
            planner: Optional deterministic analysis planner.
            orchestrator: Optional orchestrator used only after approval.
        """
        self._eda_engine = eda_engine or EDAEngine()
        self._planner = planner or EDAPlanner()
        self._orchestrator = orchestrator or AgenticEDAOrchestrator()

    def prepare(
        self,
        dataset: str | Path | pd.DataFrame,
        config: AgenticEDAConfig | None = None,
    ) -> AgenticEDAApprovalCheckpoint:
        """
        Understand a dataset and prepare its deterministic plan for review.

        No selected analysis plan step is executed by this method.

        Args:
            dataset: A DataFrame or path supported by EazyDataFix data sources.
            config: Optional deterministic orchestration configuration.

        Returns:
            A pending approval checkpoint with understanding and plan snapshots.
        """
        selected_config = _validate_agentic_eda_config(
            config,
            function_name="prepare_agentic_eda_approval",
        )
        dataframe = load_eda_frame(dataset)
        eda_result = self._eda_engine.analyze(dataframe)
        eda_plan = self._planner.plan(eda_result)
        dataset_fingerprint = _dataset_fingerprint(dataframe)

        return AgenticEDAApprovalCheckpoint(
            eda_result=eda_result,
            eda_plan=eda_plan,
            approval_status="pending",
            approved_step_ids=(),
            rejected_step_ids=(),
            reviewer=None,
            notes=None,
            config=selected_config,
            dataset_fingerprint=dataset_fingerprint,
            snapshot_fingerprint=_snapshot_fingerprint(
                eda_result=eda_result,
                eda_plan=eda_plan,
                config=selected_config,
                dataset_fingerprint=dataset_fingerprint,
            ),
            deterministic_summary=(
                "Prepared a pending Agentic EDA approval checkpoint with "
                f"{len(eda_plan.selected_steps)} selected step(s) and "
                f"{len(eda_plan.skipped_steps)} skipped step(s); no analysis "
                "steps were executed."
            ),
        )

    def approve(
        self,
        checkpoint: AgenticEDAApprovalCheckpoint,
        approved_step_ids: Sequence[str] | None = None,
        *,
        reviewer: str,
        notes: str | None = None,
    ) -> AgenticEDAApprovalCheckpoint:
        """
        Approve all or a subset of the originally selected plan steps.

        Args:
            checkpoint: A pending approval checkpoint.
            approved_step_ids: Selected step IDs to approve, or None for all.
            reviewer: Non-empty reviewer name or identifier.
            notes: Optional review notes.

        Returns:
            A new approved checkpoint preserving original planner order.

        Raises:
            TypeError: If an argument has an invalid type.
            ValueError: If the checkpoint or requested step IDs are invalid.
        """
        selected_checkpoint = self._pending_checkpoint(checkpoint, action="approved")
        selected_reviewer = self._reviewer(reviewer)
        selected_notes = self._notes(notes)
        selected_names = [step.name for step in selected_checkpoint.eda_plan.selected_steps]
        approved_names = self._approved_step_ids(
            checkpoint=selected_checkpoint,
            approved_step_ids=approved_step_ids,
        )
        approved_name_set = set(approved_names)
        rejected_names = [name for name in selected_names if name not in approved_name_set]

        return AgenticEDAApprovalCheckpoint(
            eda_result=selected_checkpoint.eda_result,
            eda_plan=selected_checkpoint.eda_plan,
            approval_status="approved",
            approved_step_ids=tuple(approved_names),
            rejected_step_ids=tuple(rejected_names),
            reviewer=selected_reviewer,
            notes=selected_notes,
            config=selected_checkpoint.config,
            dataset_fingerprint=selected_checkpoint.dataset_fingerprint,
            snapshot_fingerprint=selected_checkpoint.snapshot_fingerprint,
            deterministic_summary=(
                f"Reviewer {selected_reviewer} approved {len(approved_names)} of "
                f"{len(selected_names)} originally selected Agentic EDA step(s) "
                "for execution."
            ),
        )

    def reject(
        self,
        checkpoint: AgenticEDAApprovalCheckpoint,
        *,
        reviewer: str,
        notes: str | None = None,
    ) -> AgenticEDAApprovalCheckpoint:
        """
        Reject every originally selected plan step.

        Args:
            checkpoint: A pending approval checkpoint.
            reviewer: Non-empty reviewer name or identifier.
            notes: Optional review notes.

        Returns:
            A new rejected checkpoint that cannot be resumed.
        """
        selected_checkpoint = self._pending_checkpoint(checkpoint, action="rejected")
        selected_reviewer = self._reviewer(reviewer)
        selected_notes = self._notes(notes)
        rejected_names = tuple(step.name for step in selected_checkpoint.eda_plan.selected_steps)

        return AgenticEDAApprovalCheckpoint(
            eda_result=selected_checkpoint.eda_result,
            eda_plan=selected_checkpoint.eda_plan,
            approval_status="rejected",
            approved_step_ids=(),
            rejected_step_ids=rejected_names,
            reviewer=selected_reviewer,
            notes=selected_notes,
            config=selected_checkpoint.config,
            dataset_fingerprint=selected_checkpoint.dataset_fingerprint,
            snapshot_fingerprint=selected_checkpoint.snapshot_fingerprint,
            deterministic_summary=(
                f"Reviewer {selected_reviewer} rejected all "
                f"{len(rejected_names)} originally selected Agentic EDA step(s)."
            ),
        )

    def resume(
        self,
        dataset: str | Path | pd.DataFrame,
        checkpoint: AgenticEDAApprovalCheckpoint,
    ) -> AgenticEDAResult:
        """
        Resume deterministic execution from an approved checkpoint.

        Args:
            dataset: Dataset that must match the checkpoint fingerprint.
            checkpoint: An approved Agentic EDA checkpoint.

        Returns:
            The existing complete AgenticEDAResult workflow type.

        Raises:
            TypeError: If checkpoint has an invalid type.
            ValueError: If approval is absent or the dataset has changed.
        """
        selected_checkpoint = self._checkpoint(checkpoint)

        if selected_checkpoint.approval_status == "pending":
            raise ValueError("Cannot resume Agentic EDA from a pending approval checkpoint.")

        if selected_checkpoint.approval_status == "rejected":
            raise ValueError("Cannot resume Agentic EDA from a rejected approval checkpoint.")

        if selected_checkpoint.approval_status != "approved":
            raise ValueError(
                "Agentic EDA approval checkpoint status must be pending, approved, " "or rejected."
            )

        dataframe = load_eda_frame(dataset)
        supplied_fingerprint = _dataset_fingerprint(dataframe)

        if supplied_fingerprint != selected_checkpoint.dataset_fingerprint:
            raise ValueError(
                "The supplied dataset does not match the approval checkpoint "
                "fingerprint; prepare a new checkpoint for the changed dataset."
            )

        eda_result = deepcopy(selected_checkpoint.eda_result)
        approved_plan = self._approved_plan(selected_checkpoint)

        return self._orchestrator._complete_planned_workflow(
            dataset=dataframe,
            eda_result=eda_result,
            eda_plan=approved_plan,
            config=selected_checkpoint.config,
        )

    @staticmethod
    def _checkpoint(
        checkpoint: AgenticEDAApprovalCheckpoint,
    ) -> AgenticEDAApprovalCheckpoint:
        if not isinstance(checkpoint, AgenticEDAApprovalCheckpoint):
            raise TypeError("checkpoint must be an AgenticEDAApprovalCheckpoint.")

        expected_fingerprint = _snapshot_fingerprint(
            eda_result=checkpoint.eda_result,
            eda_plan=checkpoint.eda_plan,
            config=checkpoint.config,
            dataset_fingerprint=checkpoint.dataset_fingerprint,
        )

        if checkpoint.snapshot_fingerprint != expected_fingerprint:
            raise ValueError(
                "The Agentic EDA approval checkpoint snapshots were modified; "
                "prepare a new checkpoint before approval or execution."
            )

        return checkpoint

    @classmethod
    def _pending_checkpoint(
        cls,
        checkpoint: AgenticEDAApprovalCheckpoint,
        *,
        action: str,
    ) -> AgenticEDAApprovalCheckpoint:
        selected_checkpoint = cls._checkpoint(checkpoint)

        if selected_checkpoint.approval_status != "pending":
            raise ValueError("Only pending Agentic EDA approval checkpoints can be " f"{action}.")

        return selected_checkpoint

    @staticmethod
    def _reviewer(reviewer: str) -> str:
        if not isinstance(reviewer, str):
            raise TypeError("reviewer must be a string.")

        selected_reviewer = reviewer.strip()

        if not selected_reviewer:
            raise ValueError("reviewer must not be empty.")

        return selected_reviewer

    @staticmethod
    def _notes(notes: str | None) -> str | None:
        if notes is not None and not isinstance(notes, str):
            raise TypeError("notes must be a string or None.")

        return notes

    @staticmethod
    def _approved_step_ids(
        checkpoint: AgenticEDAApprovalCheckpoint,
        approved_step_ids: Sequence[str] | None,
    ) -> list[str]:
        selected_names = [step.name for step in checkpoint.eda_plan.selected_steps]

        if approved_step_ids is None:
            return selected_names

        if isinstance(approved_step_ids, (str, bytes)) or not isinstance(
            approved_step_ids, Sequence
        ):
            raise TypeError("approved_step_ids must be a sequence of strings or None.")

        requested_names = list(approved_step_ids)

        if any(not isinstance(name, str) for name in requested_names):
            raise TypeError("approved_step_ids must contain only strings.")

        duplicate_names = _ordered_duplicates(requested_names)

        if duplicate_names:
            raise ValueError(
                "approved_step_ids must not contain duplicate step IDs: "
                + ", ".join(duplicate_names)
                + "."
            )

        selected_name_set = set(selected_names)
        skipped_name_set = {step.name for step in checkpoint.eda_plan.skipped_steps}

        for name in requested_names:
            if name in skipped_name_set:
                raise ValueError(
                    f"EDA plan step '{name}' was skipped by the deterministic "
                    "planner and cannot be approved."
                )

            if name not in selected_name_set:
                raise ValueError(f"Unknown or unplanned EDA step ID: '{name}'.")

        requested_name_set = set(requested_names)
        return [name for name in selected_names if name in requested_name_set]

    @staticmethod
    def _approved_plan(
        checkpoint: AgenticEDAApprovalCheckpoint,
    ) -> EDAPlan:
        approved_name_set = set(checkpoint.approved_step_ids)
        selected_steps = [
            deepcopy(step)
            for step in checkpoint.eda_plan.selected_steps
            if step.name in approved_name_set
        ]
        approval_skips = [
            EDAPlanStep(
                name=step.name,
                reason=(
                    "The step was not approved for execution. Original planner "
                    f"reason: {step.reason}"
                ),
                priority="not_applicable",
                required_columns=list(step.required_columns),
                dependencies=list(step.dependencies),
            )
            for step in checkpoint.eda_plan.selected_steps
            if step.name not in approved_name_set
        ]
        skipped_steps = [
            *approval_skips,
            *(deepcopy(step) for step in checkpoint.eda_plan.skipped_steps),
        ]
        warnings = list(checkpoint.eda_plan.warnings)

        if checkpoint.rejected_step_ids:
            warnings.append(
                "Human approval excluded originally selected step(s): "
                + ", ".join(checkpoint.rejected_step_ids)
                + "."
            )

        return EDAPlan(
            selected_steps=selected_steps,
            skipped_steps=skipped_steps,
            warnings=warnings,
            deterministic_summary=(
                f"Human approval selected {len(selected_steps)} of "
                f"{len(checkpoint.eda_plan.selected_steps)} originally selected "
                "deterministic analysis step(s) for execution."
            ),
        )


def _ordered_duplicates(values: list[str]) -> list[str]:
    seen: set[str] = set()
    duplicates: list[str] = []

    for value in values:
        if value in seen and value not in duplicates:
            duplicates.append(value)
        seen.add(value)

    return duplicates


def _dataset_fingerprint(dataframe: pd.DataFrame) -> str:
    metadata = {
        "columns": list(dataframe.columns),
        "dtypes": [str(dtype) for dtype in dataframe.dtypes],
        "shape": list(dataframe.shape),
    }
    digest = hashlib.sha256(
        json.dumps(
            metadata,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    )
    row_hashes = pd.util.hash_pandas_object(
        dataframe,
        index=False,
        categorize=True,
    )

    for row_hash in row_hashes.astype("uint64").tolist():
        digest.update(int(row_hash).to_bytes(8, byteorder="big", signed=False))

    return f"sha256:{digest.hexdigest()}"


def _snapshot_fingerprint(
    *,
    eda_result: EDAResult,
    eda_plan: EDAPlan,
    config: AgenticEDAConfig,
    dataset_fingerprint: str,
) -> str:
    payload = {
        "config": to_json_compatible(config),
        "dataset_fingerprint": dataset_fingerprint,
        "eda_plan": to_json_compatible(eda_plan),
        "eda_result": to_json_compatible(eda_result),
    }
    content = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return f"sha256:{hashlib.sha256(content.encode('utf-8')).hexdigest()}"
