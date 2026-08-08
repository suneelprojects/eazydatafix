from collections.abc import Sequence
from pathlib import Path

import pandas as pd

from ._version import __version__
from .agentic_eda import AgenticEDAApprovalEngine, AgenticEDAOrchestrator
from .assessment.ai_readiness import AIReadinessEngine
from .assessment.eda import EDAEngine
from .assessment.eda_execution import EDAExecutor
from .assessment.eda_planner import EDAPlanner
from .assessment.engine import AssessmentEngine
from .assessment.profiler import DatasetProfiler
from .console_report import Report
from .fix.engine import FixEngine
from .models.agentic_eda_approval_checkpoint import (
    AgenticEDAApprovalCheckpoint,
)
from .models.agentic_eda_config import AgenticEDAConfig
from .models.agentic_eda_narrative import (
    AgenticEDANarrative,
    NarrativeClaim,
    NarrativeEvidence,
)
from .models.agentic_eda_narrative_config import AgenticEDANarrativeConfig
from .models.agentic_eda_notebook_result import AgenticEDANotebookResult
from .models.agentic_eda_report_result import (
    AgenticEDAReportResult,
    GeneratedVisualisation,
    SkippedVisualisation,
)
from .models.agentic_eda_result import (
    AgenticEDAResult,
    FollowUpAction,
    PriorityFinding,
    UnresolvedQuestion,
    VisualisationRecommendation,
)
from .models.ai_readiness_report import AIReadinessReport
from .models.assessment_report import AssessmentReport
from .models.cleaning_change import CleaningChange
from .models.column_cleaning_rule import ColumnCleaningRule
from .models.dataset_profile import DatasetProfile
from .models.eda_execution_result import (
    EDAExecutionResult,
    EDAExecutionStepResult,
)
from .models.eda_plan import EDAPlan, EDAPlanStep
from .models.eda_result import EDAResult
from .models.fix_config import FixConfig
from .models.fix_result import FixResult
from .models.preparation_report import PreparationReport
from .models.prepare_config import PrepareConfig
from .models.ready_result import ReadyResult
from .models.run_result import RunResult
from .narratives import GroundedNarrativeEngine
from .narratives.provider import NarrativeProvider
from .prepare.engine import PrepareEngine
from .reporting.agentic_eda import (
    AgenticEDANotebookExporter,
    AgenticEDAReportExporter,
)

__all__ = [
    "__version__",
    "AgenticEDAApprovalCheckpoint",
    "AgenticEDAApprovalEngine",
    "AgenticEDAConfig",
    "AgenticEDANotebookExporter",
    "AgenticEDANotebookResult",
    "AgenticEDANarrative",
    "AgenticEDANarrativeConfig",
    "AgenticEDAOrchestrator",
    "AgenticEDAReportExporter",
    "AgenticEDAReportResult",
    "AgenticEDAResult",
    "AIReadinessEngine",
    "AIReadinessReport",
    "AssessmentEngine",
    "AssessmentReport",
    "CleaningChange",
    "ColumnCleaningRule",
    "DatasetProfiler",
    "DatasetProfile",
    "EDAEngine",
    "EDAExecutionResult",
    "EDAExecutionStepResult",
    "EDAExecutor",
    "EDAPlan",
    "EDAPlanner",
    "EDAPlanStep",
    "EDAResult",
    "FixConfig",
    "FixEngine",
    "FixResult",
    "FollowUpAction",
    "GroundedNarrativeEngine",
    "GeneratedVisualisation",
    "PrepareEngine",
    "PrepareConfig",
    "PreparationReport",
    "PriorityFinding",
    "NarrativeClaim",
    "NarrativeEvidence",
    "NarrativeProvider",
    "ReadyResult",
    "Report",
    "RunResult",
    "SkippedVisualisation",
    "UnresolvedQuestion",
    "VisualisationRecommendation",
    "analysis_ready",
    "approve_agentic_eda_plan",
    "assess_ai_readiness",
    "assess",
    "eda",
    "execute_eda",
    "export_agentic_eda_notebook",
    "export_agentic_eda_report",
    "fix",
    "generate_agentic_eda_narrative",
    "plan_eda",
    "prepare",
    "prepare_with_report",
    "prepare_agentic_eda_approval",
    "profile",
    "run_agentic_eda",
    "run",
    "reject_agentic_eda_plan",
    "resume_agentic_eda",
]


def profile(
    dataset: str | Path | pd.DataFrame,
) -> DatasetProfile:
    """
    Generate a structural profile for a dataset.

    Args:
        dataset: A pandas DataFrame or path to a supported dataset file.

    Returns:
        A DatasetProfile containing structural dataset information.
    """
    profiler = DatasetProfiler()
    return profiler.profile(dataset)


def assess(
    dataset: str | Path | pd.DataFrame,
) -> AssessmentReport:
    """
    Assess the quality of a dataset.

    Args:
        dataset: A pandas DataFrame or path to a supported dataset file.

    Returns:
        An AssessmentReport containing quality scores, validations, and
        recommendations.
    """
    engine = AssessmentEngine()
    return engine.assess(dataset)


def assess_ai_readiness(
    dataset: str | Path | pd.DataFrame,
) -> AIReadinessReport:
    """
    Assess whether a dataset is ready for AI-powered applications.

    Args:
        dataset: A pandas DataFrame or path to a supported dataset file.

    Returns:
        An AIReadinessReport with AI suitability metrics and recommendations.
    """
    engine = AIReadinessEngine()
    return engine.assess(dataset)


def eda(
    dataset: str | Path | pd.DataFrame,
) -> EDAResult:
    """
    Generate a deterministic exploratory data analysis result.

    Args:
        dataset: A pandas DataFrame or path to a supported dataset file.

    Returns:
        An EDAResult containing descriptive analysis and recommendations.
    """
    engine = EDAEngine()
    return engine.analyze(dataset)


def plan_eda(
    result: EDAResult,
) -> EDAPlan:
    """
    Build a deterministic follow-up analysis plan for an EDA result.

    Args:
        result: An EDAResult generated by :func:`eda`.

    Returns:
        An EDAPlan explaining every selected and skipped analysis step.
    """
    planner = EDAPlanner()
    return planner.plan(result)


def execute_eda(
    dataset: str | Path | pd.DataFrame,
    result: EDAResult | None = None,
    plan: EDAPlan | None = None,
) -> EDAExecutionResult:
    """
    Execute a deterministic EDA plan against a supported dataset.

    Missing EDA results and plans are generated automatically.

    Args:
        dataset: A pandas DataFrame or path to a supported dataset file.
        result: Optional EDA result corresponding to the dataset.
        plan: Optional EDA plan corresponding to the result.

    Returns:
        An EDAExecutionResult containing step outputs and execution status.
    """
    executor = EDAExecutor()
    return executor.execute(
        dataset=dataset,
        result=result,
        plan=plan,
    )


def run_agentic_eda(
    dataset: str | Path | pd.DataFrame,
    config: AgenticEDAConfig | None = None,
) -> AgenticEDAResult:
    """
    Run the complete deterministic Agentic EDA workflow.

    The workflow understands the dataset, plans and executes applicable
    analyses, and generates traceable follow-up decisions without using an LLM.

    Args:
        dataset: A pandas DataFrame or path to a supported dataset file.
        config: Optional deterministic thresholds and feature toggles.

    Returns:
        An AgenticEDAResult containing all workflow stages and recommendations.
    """
    orchestrator = AgenticEDAOrchestrator()
    return orchestrator.run(dataset=dataset, config=config)


def prepare_agentic_eda_approval(
    dataset: str | Path | pd.DataFrame,
    config: AgenticEDAConfig | None = None,
) -> AgenticEDAApprovalCheckpoint:
    """
    Prepare dataset understanding and an EDA plan for human approval.

    No selected analysis step is executed while preparing the checkpoint.

    Args:
        dataset: A DataFrame or path supported by EazyDataFix data sources.
        config: Optional deterministic thresholds and feature toggles.

    Returns:
        A pending AgenticEDAApprovalCheckpoint.

    Raises:
        TypeError: If config is not an AgenticEDAConfig or None.
    """
    engine = AgenticEDAApprovalEngine()
    return engine.prepare(dataset=dataset, config=config)


def approve_agentic_eda_plan(
    checkpoint: AgenticEDAApprovalCheckpoint,
    approved_step_ids: Sequence[str] | None = None,
    *,
    reviewer: str,
    notes: str | None = None,
) -> AgenticEDAApprovalCheckpoint:
    """
    Approve all or selected deterministic EDA plan steps.

    Args:
        checkpoint: A pending approval checkpoint.
        approved_step_ids: Selected step IDs to approve, or None for all.
        reviewer: Non-empty reviewer name or identifier.
        notes: Optional approval notes.

    Returns:
        A new approved AgenticEDAApprovalCheckpoint.

    Raises:
        TypeError: If an argument has an invalid type.
        ValueError: If the checkpoint or requested step IDs are invalid.
    """
    engine = AgenticEDAApprovalEngine()
    return engine.approve(
        checkpoint=checkpoint,
        approved_step_ids=approved_step_ids,
        reviewer=reviewer,
        notes=notes,
    )


def reject_agentic_eda_plan(
    checkpoint: AgenticEDAApprovalCheckpoint,
    *,
    reviewer: str,
    notes: str | None = None,
) -> AgenticEDAApprovalCheckpoint:
    """
    Reject every selected step in a pending Agentic EDA checkpoint.

    Args:
        checkpoint: A pending approval checkpoint.
        reviewer: Non-empty reviewer name or identifier.
        notes: Optional rejection notes.

    Returns:
        A new rejected AgenticEDAApprovalCheckpoint.

    Raises:
        TypeError: If an argument has an invalid type.
        ValueError: If the checkpoint was already reviewed.
    """
    engine = AgenticEDAApprovalEngine()
    return engine.reject(
        checkpoint=checkpoint,
        reviewer=reviewer,
        notes=notes,
    )


def resume_agentic_eda(
    dataset: str | Path | pd.DataFrame,
    checkpoint: AgenticEDAApprovalCheckpoint,
) -> AgenticEDAResult:
    """
    Resume execution from an approved Agentic EDA checkpoint.

    Args:
        dataset: Dataset that must match the checkpoint fingerprint.
        checkpoint: An approved checkpoint created for the dataset.

    Returns:
        The existing complete AgenticEDAResult workflow type.

    Raises:
        TypeError: If checkpoint has an invalid type.
        ValueError: If approval is absent or the dataset has changed.
    """
    engine = AgenticEDAApprovalEngine()
    return engine.resume(dataset=dataset, checkpoint=checkpoint)


def export_agentic_eda_notebook(
    workflow: AgenticEDAResult,
    dataset: str | Path | pd.DataFrame,
    output_path: str | Path = "agentic-eda.ipynb",
    config: AgenticEDAConfig | None = None,
) -> AgenticEDANotebookResult:
    """
    Export a deterministic, ready-to-run Agentic EDA Jupyter notebook.

    Args:
        workflow: Existing result returned by :func:`run_agentic_eda`.
        dataset: Matching DataFrame or supported dataset file path.
        output_path: Destination ``.ipynb`` file.
        config: Configuration used to reproduce the complete workflow.

    Returns:
        An AgenticEDANotebookResult describing generated artifacts.
    """
    exporter = AgenticEDANotebookExporter()
    return exporter.export(
        workflow=workflow,
        dataset=dataset,
        output_path=output_path,
        config=config,
    )


def export_agentic_eda_report(
    workflow: AgenticEDAResult,
    dataset: str | Path | pd.DataFrame | None = None,
    output_dir: str | Path = "eazydatafix-report",
    formats: Sequence[str] | None = None,
    narrative: AgenticEDANarrative | None = None,
) -> AgenticEDAReportResult:
    """
    Export deterministic Agentic EDA report and visualisation artifacts.

    Args:
        workflow: Existing result returned by :func:`run_agentic_eda`.
        dataset: Optional matching dataset used for raw-data chart types.
        output_dir: Dedicated directory for all generated report artifacts.
        formats: Optional subset of ``html``, ``json``, and ``markdown``.
        narrative: Optional cited narrative generated by
            :func:`generate_agentic_eda_narrative`.

    Returns:
        An AgenticEDAReportResult describing generated and skipped artifacts.
    """
    exporter = AgenticEDAReportExporter()
    return exporter.export(
        workflow=workflow,
        dataset=dataset,
        output_dir=output_dir,
        formats=formats,
        narrative=narrative,
    )


def generate_agentic_eda_narrative(
    workflow: AgenticEDAResult,
    provider: NarrativeProvider,
    config: AgenticEDANarrativeConfig | None = None,
) -> AgenticEDANarrative:
    """Generate an optional cited narrative from deterministic EDA evidence.

    The provider receives only a compact evidence brief built from the completed
    workflow. Every generated claim must cite supplied evidence; invalid or
    uncited provider responses are rejected. This function does not rerun or
    modify the deterministic workflow.

    Args:
        workflow: A completed deterministic Agentic EDA workflow.
        provider: A narrative adapter, such as an OpenAI provider.
        config: Optional limits for evidence supplied to the provider.

    Returns:
        An ``AgenticEDANarrative`` with generated claims and cited evidence.
    """
    engine = GroundedNarrativeEngine()
    return engine.generate(workflow=workflow, provider=provider, config=config)


def fix(
    dataset: str | Path | pd.DataFrame,
    config: FixConfig | None = None,
) -> FixResult:
    """
    Automatically clean a dataset.

    Args:
        dataset: A pandas DataFrame or path to a supported dataset file.
        config: Optional configuration for the cleaning operation.

    Returns:
        A FixResult containing the cleaned DataFrame, before and after
        assessment reports, and applied fixes.
    """
    engine = FixEngine()
    return engine.fix(dataset, config)


def run(
    dataset: str | Path | pd.DataFrame,
    config: FixConfig | None = None,
) -> RunResult:
    """Run profile, assessment, controlled cleaning, and deterministic EDA.

    A dry-run ``FixConfig`` returns the unmodified source dataset in
    ``fix_result.dataset`` and keeps the proposed cleaned dataset separately
    in ``fix_result.proposed_dataset``. EDA therefore remains aligned with the
    dataset returned by the workflow.

    Args:
        dataset: A pandas DataFrame or path to a supported dataset file.
        config: Optional configuration for the cleaning stage.

    Returns:
        A RunResult containing profile, assessment, fix, and EDA results.
    """
    profiler = DatasetProfiler()
    assessment_engine = AssessmentEngine()
    fix_engine = FixEngine()
    eda_engine = EDAEngine()

    dataset_profile = profiler.profile(dataset)
    assessment = assessment_engine.assess(dataset)
    fix_result = fix_engine.fix(dataset, config)
    eda_result = eda_engine.analyze(fix_result.dataset)

    return RunResult(
        profile=dataset_profile,
        assessment=assessment,
        fix_result=fix_result,
        eda_result=eda_result,
    )


def prepare(
    dataset: str | Path | pd.DataFrame,
    config: PrepareConfig | None = None,
) -> pd.DataFrame:
    """
    Prepare a dataset for downstream analytics or machine learning.

    Args:
        dataset: A pandas DataFrame or path to a supported dataset file.

    Returns:
        A prepared pandas DataFrame.
    """
    engine = PrepareEngine()
    return engine.prepare(dataset, config)


def prepare_with_report(
    dataset: str | Path | pd.DataFrame,
    config: PrepareConfig | None = None,
) -> PreparationReport:
    """Prepare a dataset and return its deterministic preparation report."""
    engine = PrepareEngine()
    return engine.prepare_with_report(dataset, config)


def analysis_ready(
    dataset: str | Path | pd.DataFrame,
    config: FixConfig | None = None,
) -> pd.DataFrame:
    """
    Clean and prepare a dataset for exploratory data analysis (EDA).

    Args:
        dataset: A pandas DataFrame or path to a supported dataset file.
        config: Optional configuration for the cleaning operation.

    Returns:
        A cleaned and prepared pandas DataFrame.
    """

    cleaned = fix(
        dataset,
        config=config,
    )

    engine = PrepareEngine()

    return engine.prepare(
        cleaned.dataset,
    )
