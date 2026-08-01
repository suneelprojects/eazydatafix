import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

import eazydatafix as edf
from eazydatafix.agentic_eda import AgenticEDAApprovalEngine
from eazydatafix.assessment.eda import EDAEngine
from eazydatafix.assessment.eda_execution import EDAExecutor
from eazydatafix.assessment.eda_planner import EDAPlanner
from eazydatafix.models.agentic_eda_approval_checkpoint import (
    AgenticEDAApprovalCheckpoint,
)
from eazydatafix.models.agentic_eda_result import AgenticEDAResult
from eazydatafix.models.eda_plan import EDAPlanStep


def _approval_dataset() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "employee_id": list(range(1, 11)),
            "amount": [1, 2, 3, 4, 5, 6, 7, 8, 9, 100],
            "score": [2, 4, 6, 8, 10, 12, 14, 16, 18, 20],
            "department": ["Sales"] * 6 + ["Engineering"] * 4,
            "is_active": [True] * 8 + [False] * 2,
            "event_date": pd.date_range("2025-01-01", periods=10, freq="D"),
        }
    )


def _approved_checkpoint(
    dataset: pd.DataFrame | Path,
    approved_step_ids: list[str] | None = None,
    config: edf.AgenticEDAConfig | None = None,
) -> AgenticEDAApprovalCheckpoint:
    checkpoint = edf.prepare_agentic_eda_approval(dataset, config=config)
    return edf.approve_agentic_eda_plan(
        checkpoint,
        approved_step_ids=approved_step_ids,
        reviewer="Suneel Kumar Kola",
        notes="Approved for execution",
    )


def test_approval_apis_and_model_are_public() -> None:
    public_functions = [
        "prepare_agentic_eda_approval",
        "approve_agentic_eda_plan",
        "reject_agentic_eda_plan",
        "resume_agentic_eda",
    ]

    for name in public_functions:
        assert name in edf.__all__
        assert callable(getattr(edf, name))

    assert "AgenticEDAApprovalCheckpoint" in edf.__all__
    assert "AgenticEDAApprovalEngine" in edf.__all__
    assert edf.AgenticEDAApprovalCheckpoint is AgenticEDAApprovalCheckpoint
    assert edf.AgenticEDAApprovalEngine is AgenticEDAApprovalEngine


def test_prepare_creates_pending_checkpoint_without_executing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def unexpected_execute(*args: Any, **kwargs: Any) -> None:
        pytest.fail("EDAExecutor.execute() must not run while preparing approval.")

    monkeypatch.setattr(EDAExecutor, "execute", unexpected_execute)

    checkpoint = edf.prepare_agentic_eda_approval(_approval_dataset())

    assert checkpoint.approval_status == "pending"
    assert checkpoint.approved_step_ids == ()
    assert checkpoint.rejected_step_ids == ()
    assert checkpoint.reviewer is None
    assert checkpoint.notes is None
    assert checkpoint.dataset_fingerprint.startswith("sha256:")
    assert len(checkpoint.dataset_fingerprint) == 71
    assert checkpoint.snapshot_fingerprint.startswith("sha256:")
    assert len(checkpoint.snapshot_fingerprint) == 71
    assert checkpoint.eda_plan.selected_steps
    assert "no analysis steps were executed" in checkpoint.deterministic_summary


def test_approve_none_approves_all_selected_steps() -> None:
    checkpoint = edf.prepare_agentic_eda_approval(_approval_dataset())

    approved = edf.approve_agentic_eda_plan(
        checkpoint,
        approved_step_ids=None,
        reviewer="Suneel Kumar Kola",
        notes="Approved for execution",
    )

    selected_names = tuple(step.name for step in checkpoint.eda_plan.selected_steps)
    assert approved.approval_status == "approved"
    assert approved.approved_step_ids == selected_names
    assert approved.rejected_step_ids == ()
    assert approved.reviewer == "Suneel Kumar Kola"
    assert approved.notes == "Approved for execution"
    assert checkpoint.approval_status == "pending"
    assert approved.eda_plan is not checkpoint.eda_plan


def test_subset_approval_preserves_original_plan_order() -> None:
    checkpoint = edf.prepare_agentic_eda_approval(_approval_dataset())
    selected_names = [step.name for step in checkpoint.eda_plan.selected_steps]
    requested_names = [selected_names[-1], selected_names[1], selected_names[0]]

    approved = edf.approve_agentic_eda_plan(
        checkpoint,
        approved_step_ids=requested_names,
        reviewer="Reviewer",
    )

    expected_approved = tuple(name for name in selected_names if name in requested_names)
    expected_rejected = tuple(name for name in selected_names if name not in requested_names)
    assert approved.approved_step_ids == expected_approved
    assert approved.rejected_step_ids == expected_rejected


def test_subset_approval_rejects_missing_required_dependencies() -> None:
    checkpoint = edf.prepare_agentic_eda_approval(_approval_dataset())

    with pytest.raises(
        ValueError,
        match="omit required dependencies.*never automatically approved",
    ):
        edf.approve_agentic_eda_plan(
            checkpoint,
            approved_step_ids=["outlier_analysis"],
            reviewer="Reviewer",
        )


def test_subset_approval_accepts_explicit_dependencies_in_planner_order() -> None:
    dataset = _approval_dataset()
    checkpoint = edf.prepare_agentic_eda_approval(dataset)

    approved = edf.approve_agentic_eda_plan(
        checkpoint,
        approved_step_ids=[
            "outlier_analysis",
            "numeric_distribution_analysis",
        ],
        reviewer="Reviewer",
    )
    workflow = edf.resume_agentic_eda(dataset, approved)

    assert approved.approved_step_ids == (
        "numeric_distribution_analysis",
        "outlier_analysis",
    )
    assert workflow.execution_result.execution_order == list(approved.approved_step_ids)
    assert workflow.overall_status == "success"


def test_approval_rejects_duplicate_step_ids() -> None:
    checkpoint = edf.prepare_agentic_eda_approval(_approval_dataset())
    step_id = checkpoint.eda_plan.selected_steps[0].name

    with pytest.raises(ValueError, match="duplicate step IDs"):
        edf.approve_agentic_eda_plan(
            checkpoint,
            approved_step_ids=[step_id, step_id],
            reviewer="Reviewer",
        )


def test_approval_rejects_unknown_or_unplanned_step_ids() -> None:
    checkpoint = edf.prepare_agentic_eda_approval(_approval_dataset())

    with pytest.raises(ValueError, match="Unknown or unplanned"):
        edf.approve_agentic_eda_plan(
            checkpoint,
            approved_step_ids=["invented_analysis"],
            reviewer="Reviewer",
        )


def test_approval_rejects_planner_skipped_step_ids() -> None:
    checkpoint = edf.prepare_agentic_eda_approval(_approval_dataset())
    skipped_step_id = checkpoint.eda_plan.skipped_steps[0].name

    with pytest.raises(ValueError, match="skipped by the deterministic planner"):
        edf.approve_agentic_eda_plan(
            checkpoint,
            approved_step_ids=[skipped_step_id],
            reviewer="Reviewer",
        )


def test_explicit_rejection_records_all_selected_steps() -> None:
    checkpoint = edf.prepare_agentic_eda_approval(_approval_dataset())

    rejected = edf.reject_agentic_eda_plan(
        checkpoint,
        reviewer="Risk reviewer",
        notes="Dataset requires domain review.",
    )

    assert rejected.approval_status == "rejected"
    assert rejected.approved_step_ids == ()
    assert rejected.rejected_step_ids == tuple(
        step.name for step in checkpoint.eda_plan.selected_steps
    )
    assert rejected.reviewer == "Risk reviewer"
    assert checkpoint.approval_status == "pending"


def test_resume_rejects_pending_checkpoint() -> None:
    dataset = _approval_dataset()
    checkpoint = edf.prepare_agentic_eda_approval(dataset)

    with pytest.raises(ValueError, match="pending approval checkpoint"):
        edf.resume_agentic_eda(dataset, checkpoint)


def test_resume_rejects_rejected_checkpoint() -> None:
    dataset = _approval_dataset()
    checkpoint = edf.prepare_agentic_eda_approval(dataset)
    rejected = edf.reject_agentic_eda_plan(
        checkpoint,
        reviewer="Reviewer",
    )

    with pytest.raises(ValueError, match="rejected approval checkpoint"):
        edf.resume_agentic_eda(dataset, rejected)


def test_resume_executes_approved_plan_and_returns_existing_result_type() -> None:
    dataset = _approval_dataset()
    approved = _approved_checkpoint(dataset)
    approved_snapshot = approved.to_dict()

    workflow = edf.resume_agentic_eda(dataset, approved)

    assert isinstance(workflow, AgenticEDAResult)
    assert workflow.eda_plan is workflow.execution_result.eda_plan
    assert workflow.eda_result is workflow.execution_result.eda_result
    assert workflow.execution_result.execution_order == list(approved.approved_step_ids)
    assert workflow.overall_status == "success"
    assert approved.to_dict() == approved_snapshot


def test_resume_does_not_repeat_understanding_or_planning(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dataset = _approval_dataset()
    approved = _approved_checkpoint(dataset)

    def unexpected_call(*args: Any, **kwargs: Any) -> None:
        pytest.fail("Understanding and planning must not rerun during resume.")

    monkeypatch.setattr(EDAEngine, "analyze", unexpected_call)
    monkeypatch.setattr(EDAPlanner, "plan", unexpected_call)

    workflow = edf.resume_agentic_eda(dataset, approved)

    assert workflow.overall_status == "success"


def test_resume_detects_dataset_value_changes_with_stable_shape() -> None:
    dataset = _approval_dataset()
    approved = _approved_checkpoint(dataset)
    changed = dataset.copy(deep=True)
    changed.loc[0, "amount"] = 999

    with pytest.raises(ValueError, match="does not match.*fingerprint"):
        edf.resume_agentic_eda(changed, approved)


def test_dataframe_is_not_mutated_by_prepare_approve_or_resume() -> None:
    dataset = _approval_dataset()
    original = dataset.copy(deep=True)

    checkpoint = edf.prepare_agentic_eda_approval(dataset)
    approved = edf.approve_agentic_eda_plan(
        checkpoint,
        reviewer="Reviewer",
    )
    edf.resume_agentic_eda(dataset, approved)

    pd.testing.assert_frame_equal(dataset, original)


@pytest.mark.parametrize("suffix", [".csv", ".xlsx", ".json", ".parquet"])
def test_file_path_datasets_can_prepare_approve_and_resume(
    tmp_path: Path,
    suffix: str,
) -> None:
    dataset = _approval_dataset()
    dataset_path = tmp_path / f"approval{suffix}"

    if suffix == ".csv":
        dataset.to_csv(dataset_path, index=False)
    elif suffix == ".xlsx":
        dataset.to_excel(dataset_path, index=False)
    elif suffix == ".json":
        dataset.to_json(dataset_path, orient="records", date_format="iso")
    else:
        pytest.importorskip("pyarrow")
        dataset.to_parquet(dataset_path, index=False)

    approved = _approved_checkpoint(dataset_path)
    workflow = edf.resume_agentic_eda(dataset_path, approved)

    assert workflow.overall_status == "success"
    assert workflow.eda_result.shape == dataset.shape


def test_custom_config_is_preserved_and_used_during_resume() -> None:
    dataset = _approval_dataset()
    config = edf.AgenticEDAConfig(
        correlation_threshold=1.0,
        outlier_iqr_multiplier=3.0,
        class_imbalance_threshold=0.90,
        enable_visualisation_recommendations=False,
        enable_unresolved_questions=False,
        max_recommendations_per_category=2,
    )
    checkpoint = edf.prepare_agentic_eda_approval(dataset, config=config)
    approved = edf.approve_agentic_eda_plan(
        checkpoint,
        reviewer="Reviewer",
    )

    workflow = edf.resume_agentic_eda(dataset, approved)
    outputs = {
        step.name: step.output
        for step in workflow.execution_result.executed_steps
        if step.status == "success"
    }

    assert checkpoint.config == config
    assert approved.config == config
    assert outputs["correlation_review"]["threshold"] == 1.0
    assert outputs["outlier_analysis"]["iqr_multiplier"] == 3.0
    assert outputs["class_imbalance_analysis"]["threshold_percentage"] == 90.0
    assert workflow.recommended_visualisations == []
    assert workflow.unresolved_questions == []


def test_repeated_checkpoint_creation_is_deterministic_and_json_ready() -> None:
    dataset = _approval_dataset()

    first = edf.prepare_agentic_eda_approval(dataset)
    second = edf.prepare_agentic_eda_approval(dataset)
    first_approved = edf.approve_agentic_eda_plan(
        first,
        reviewer="Reviewer",
        notes="Approved deterministically.",
    )
    second_approved = edf.approve_agentic_eda_plan(
        second,
        reviewer="Reviewer",
        notes="Approved deterministically.",
    )

    assert first == second
    assert first.dataset_fingerprint == second.dataset_fingerprint
    assert json.loads(json.dumps(first.to_dict())) == first.to_dict()
    assert first.to_dict()["approved_step_ids"] == []
    assert first_approved == second_approved
    assert json.loads(json.dumps(first_approved.to_dict())) == first_approved.to_dict()


def test_empty_subset_approval_executes_no_steps() -> None:
    dataset = _approval_dataset()
    approved = _approved_checkpoint(dataset, approved_step_ids=[])

    workflow = edf.resume_agentic_eda(dataset, approved)

    assert approved.approved_step_ids == ()
    assert workflow.execution_result.executed_steps == []
    assert workflow.execution_result.execution_order == []
    assert workflow.overall_status == "success"
    assert any("Human approval excluded" in warning for warning in workflow.workflow_warnings)


def test_existing_run_agentic_eda_behavior_and_return_type_remain_unchanged() -> None:
    dataset = _approval_dataset()

    workflow = edf.run_agentic_eda(dataset)

    assert isinstance(workflow, AgenticEDAResult)
    assert workflow.execution_result.executed_steps
    assert workflow.eda_plan is workflow.execution_result.eda_plan


def test_resumed_workflow_is_compatible_with_notebook_and_report_exporters(
    tmp_path: Path,
) -> None:
    dataset = _approval_dataset()
    approved = _approved_checkpoint(dataset)
    workflow = edf.resume_agentic_eda(dataset, approved)

    notebook = edf.export_agentic_eda_notebook(
        workflow,
        dataset=dataset,
        output_path=tmp_path / "approval-workflow.ipynb",
        config=approved.config,
    )
    report = edf.export_agentic_eda_report(
        workflow,
        output_dir=tmp_path / "report",
        formats=["json"],
    )

    assert Path(notebook.notebook_path).is_file()
    assert notebook.status == "success"
    assert report.status == "success"
    assert "agentic-eda-report.json" in report.generated_files


@pytest.mark.parametrize(
    ("reviewer", "error"),
    [
        ("", ValueError),
        ("   ", ValueError),
        (None, TypeError),
    ],
)
def test_approval_validates_reviewer(
    reviewer: str,
    error: type[Exception],
) -> None:
    checkpoint = edf.prepare_agentic_eda_approval(_approval_dataset())

    with pytest.raises(error):
        edf.approve_agentic_eda_plan(
            checkpoint,
            reviewer=reviewer,
        )


def test_decided_checkpoint_cannot_be_reviewed_again() -> None:
    approved = _approved_checkpoint(_approval_dataset())

    with pytest.raises(ValueError, match="Only pending"):
        edf.reject_agentic_eda_plan(
            approved,
            reviewer="Another reviewer",
        )


def test_nested_checkpoint_plan_mutation_is_rejected() -> None:
    checkpoint = edf.prepare_agentic_eda_approval(_approval_dataset())
    checkpoint.eda_plan.selected_steps.append(
        EDAPlanStep(
            name="invented_analysis",
            reason="Not part of the original deterministic plan.",
            priority="high",
            required_columns=[],
            dependencies=[],
        )
    )

    with pytest.raises(ValueError, match="snapshots were modified"):
        edf.approve_agentic_eda_plan(
            checkpoint,
            reviewer="Reviewer",
        )


def test_checkpoint_decision_field_tampering_is_rejected() -> None:
    dataset = _approval_dataset()
    checkpoint = edf.prepare_agentic_eda_approval(dataset)
    selected_names = tuple(step.name for step in checkpoint.eda_plan.selected_steps)
    forged = replace(
        checkpoint,
        approval_status="approved",
        approved_step_ids=selected_names,
        reviewer="Forged reviewer",
        deterministic_summary="Forged approval decision.",
    )

    with pytest.raises(ValueError, match="snapshots were modified"):
        edf.resume_agentic_eda(dataset, forged)
