from pathlib import Path

import eazydatafix as edf
from eazydatafix._version import __version__ as package_version


def test_release_version_has_one_public_value() -> None:
    assert package_version == "0.5.0"
    assert edf.__version__ == package_version


def test_release_documentation_matches_package_version() -> None:
    project_root = Path(__file__).resolve().parents[1]
    changelog = (project_root / "CHANGELOG.md").read_text(encoding="utf-8")
    readme = (project_root / "README.md").read_text(encoding="utf-8")
    release_notes = (project_root / "RELEASE_NOTES.md").read_text(encoding="utf-8")

    assert "## [0.5.0] - 2026-08-04" in changelog
    assert "### Planned version: 0.5.0" not in changelog
    assert "- Current stable version: v0.5.0" in readme
    assert release_notes.startswith("# EazyDataFix 0.5.0 Release Notes")


def test_required_public_functions_are_exported() -> None:
    public_functions = [
        "eda",
        "plan_eda",
        "execute_eda",
        "run_agentic_eda",
        "prepare_agentic_eda_approval",
        "approve_agentic_eda_plan",
        "reject_agentic_eda_plan",
        "resume_agentic_eda",
        "export_agentic_eda_notebook",
        "export_agentic_eda_report",
        "generate_agentic_eda_narrative",
        "fix",
        "prepare",
        "profile",
    ]

    for name in public_functions:
        assert name in edf.__all__
        assert callable(getattr(edf, name))


def test_public_result_and_config_classes_are_exported() -> None:
    public_classes = [
        "AgenticEDAConfig",
        "AgenticEDAApprovalCheckpoint",
        "AgenticEDAApprovalEngine",
        "AgenticEDANotebookResult",
        "AgenticEDANarrative",
        "AgenticEDANarrativeConfig",
        "AgenticEDAResult",
        "AgenticEDAReportResult",
        "EDAResult",
        "EDAPlan",
        "EDAPlanStep",
        "EDAExecutionResult",
        "EDAExecutionStepResult",
        "FollowUpAction",
        "PriorityFinding",
        "UnresolvedQuestion",
        "VisualisationRecommendation",
        "GeneratedVisualisation",
        "NarrativeClaim",
        "NarrativeEvidence",
        "NarrativeProvider",
        "SkippedVisualisation",
        "FixConfig",
        "FixResult",
        "AssessmentReport",
        "AIReadinessReport",
        "DatasetProfile",
        "ReadyResult",
    ]

    assert len(edf.__all__) == len(set(edf.__all__))

    for name in public_classes:
        assert name in edf.__all__
        assert isinstance(getattr(edf, name), type)
