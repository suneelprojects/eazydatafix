from pathlib import Path

import pandas as pd

from eazydatafix.agentic_eda.decisions import FollowUpDecisionEngine
from eazydatafix.assessment.eda import EDAEngine
from eazydatafix.assessment.eda_execution import EDAExecutor
from eazydatafix.assessment.eda_execution.registry import default_handlers
from eazydatafix.assessment.eda_planner import EDAPlanner
from eazydatafix.models.agentic_eda_config import AgenticEDAConfig
from eazydatafix.models.agentic_eda_result import AgenticEDAResult
from eazydatafix.models.eda_plan import EDAPlan
from eazydatafix.models.eda_result import EDAResult


class AgenticEDAOrchestrator:
    """
    Coordinates the deterministic Agentic EDA workflow.

    The orchestrator composes the existing understanding, planning, and
    execution engines, then derives traceable follow-up decisions without
    rerunning or duplicating their analysis logic.
    """

    def __init__(
        self,
        eda_engine: EDAEngine | None = None,
        planner: EDAPlanner | None = None,
        executor: EDAExecutor | None = None,
        decision_engine: FollowUpDecisionEngine | None = None,
    ) -> None:
        """
        Initialise the orchestrator with optional compatible components.

        Args:
            eda_engine: Optional dataset-understanding engine.
            planner: Optional deterministic analysis planner.
            executor: Optional executor, primarily for controlled extensions.
            decision_engine: Optional deterministic follow-up decision engine.
        """
        self._eda_engine = eda_engine or EDAEngine()
        self._planner = planner or EDAPlanner()
        self._executor = executor
        self._decision_engine = decision_engine or FollowUpDecisionEngine()

    def run(
        self,
        dataset: str | Path | pd.DataFrame,
        config: AgenticEDAConfig | None = None,
    ) -> AgenticEDAResult:
        """
        Run the complete deterministic Agentic EDA workflow.

        Args:
            dataset: A DataFrame or path supported by EazyDataFix data sources.
            config: Optional validated thresholds and feature toggles.

        Returns:
            A structured, JSON-ready AgenticEDAResult.

        Raises:
            TypeError: If config is not an AgenticEDAConfig or None.
        """
        selected_config = self._validate_config(config)
        eda_result = self._eda_engine.analyze(dataset)
        eda_plan = self._planner.plan(eda_result)

        return self._complete_planned_workflow(
            dataset=dataset,
            eda_result=eda_result,
            eda_plan=eda_plan,
            config=selected_config,
        )

    def _complete_planned_workflow(
        self,
        dataset: str | Path | pd.DataFrame,
        eda_result: EDAResult,
        eda_plan: EDAPlan,
        config: AgenticEDAConfig,
    ) -> AgenticEDAResult:
        """Execute and finalise an already understood and planned workflow."""
        executor = self._executor or EDAExecutor(
            handlers=default_handlers(
                correlation_threshold=config.correlation_threshold,
                outlier_iqr_multiplier=config.outlier_iqr_multiplier,
                class_imbalance_threshold=config.class_imbalance_threshold,
            )
        )
        execution_result = executor.execute(
            dataset=dataset,
            result=eda_result,
            plan=eda_plan,
        )
        decisions = self._decision_engine.generate(
            execution=execution_result,
            config=config,
        )
        warnings = list(execution_result.warnings)

        if not decisions.actions:
            warnings.append("No deterministic follow-up actions were generated.")

        status = execution_result.status

        return AgenticEDAResult(
            eda_result=eda_result,
            eda_plan=eda_plan,
            execution_result=execution_result,
            follow_up_actions=decisions.actions,
            unresolved_questions=decisions.questions,
            recommended_visualisations=decisions.visualisations,
            priority_findings=decisions.findings,
            workflow_warnings=warnings,
            deterministic_final_summary=self._summary(
                status=status,
                action_count=len(decisions.actions),
                question_count=len(decisions.questions),
                visualisation_count=len(decisions.visualisations),
                finding_count=len(decisions.findings),
            ),
            overall_status=status,
        )

    @staticmethod
    def _validate_config(
        config: AgenticEDAConfig | None,
    ) -> AgenticEDAConfig:
        return _validate_agentic_eda_config(
            config,
            function_name="run_agentic_eda",
        )

    @staticmethod
    def _summary(
        *,
        status: str,
        action_count: int,
        question_count: int,
        visualisation_count: int,
        finding_count: int,
    ) -> str:
        return (
            f"Deterministic Agentic EDA completed with status {status}: "
            f"{finding_count} priority finding(s), {action_count} follow-up action(s), "
            f"{visualisation_count} visualisation recommendation(s), and "
            f"{question_count} unresolved question(s)."
        )


def _validate_agentic_eda_config(
    config: AgenticEDAConfig | None,
    *,
    function_name: str,
) -> AgenticEDAConfig:
    if config is None:
        return AgenticEDAConfig()

    if not isinstance(config, AgenticEDAConfig):
        raise TypeError(f"{function_name}() config must be an AgenticEDAConfig or None.")

    return config
