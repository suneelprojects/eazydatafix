import logging
from collections.abc import Iterable
from pathlib import Path

import pandas as pd

from eazydatafix.assessment.eda import EDAEngine
from eazydatafix.assessment.eda_execution.base import EDAAnalysisHandler
from eazydatafix.assessment.eda_execution.registry import default_handlers
from eazydatafix.assessment.eda_planner import EDAPlanner
from eazydatafix.assessment.eda_validation import (
    load_eda_frame,
    validate_eda_result,
)
from eazydatafix.models.eda_execution_result import (
    EDAExecutionResult,
    EDAExecutionStepResult,
)
from eazydatafix.models.eda_plan import EDAPlan, EDAPlanStep
from eazydatafix.models.eda_result import EDAResult

logger = logging.getLogger(__name__)


class EDAExecutor:
    """
    Executes selected deterministic EDA plan steps through registered handlers.
    """

    def __init__(
        self,
        handlers: Iterable[EDAAnalysisHandler] | None = None,
    ) -> None:
        """
        Initialise the executor with built-in or custom deterministic handlers.

        Args:
            handlers: Optional iterable replacing the built-in handler set.

        Raises:
            ValueError: If multiple handlers use the same step name.
        """
        selected_handlers = list(handlers) if handlers is not None else default_handlers()
        self._handlers: dict[str, EDAAnalysisHandler] = {}

        for handler in selected_handlers:
            if handler.name in self._handlers:
                raise ValueError(
                    f"Duplicate EDA execution handler registered for '{handler.name}'."
                )

            self._handlers[handler.name] = handler

    def execute(
        self,
        dataset: str | Path | pd.DataFrame,
        result: EDAResult | None = None,
        plan: EDAPlan | None = None,
    ) -> EDAExecutionResult:
        """
        Execute a deterministic EDA plan against a supported dataset.

        Args:
            dataset: A pandas DataFrame or path to a supported dataset file.
            result: Optional EDA result corresponding to the supplied dataset.
            plan: Optional EDA plan corresponding to the result.

        Returns:
            An EDAExecutionResult with reproducible step-level outputs.

        Raises:
            TypeError: If result or plan has an invalid type.
            ValueError: If the EDA result does not correspond to the dataset.
        """
        dataframe = load_eda_frame(dataset)

        if result is None:
            result = EDAEngine().analyze(dataset)
        elif not isinstance(result, EDAResult):
            raise TypeError("execute_eda() result must be an EDAResult or None.")

        validate_eda_result(dataframe, result)

        if plan is None:
            plan = EDAPlanner().plan(result)
        elif not isinstance(plan, EDAPlan):
            raise TypeError("execute_eda() plan must be an EDAPlan or None.")

        self._validate_plan(plan)

        executed_steps: list[EDAExecutionStepResult] = []
        execution_order: list[str] = []
        warnings = list(plan.warnings)
        statuses: dict[str, str] = {}

        for step in plan.selected_steps:
            execution_order.append(step.name)
            step_result = self._execute_step(
                dataframe=dataframe,
                result=result,
                step=step,
                statuses=statuses,
            )
            executed_steps.append(step_result)
            statuses[step.name] = step_result.status

            if step_result.status == "failure":
                warning = f"Step '{step.name}' failed: {step_result.error}"

                if warning not in warnings:
                    warnings.append(warning)

        skipped_steps = [self._skipped_step_record(step) for step in plan.skipped_steps]
        status = self._execution_status(executed_steps)

        return EDAExecutionResult(
            eda_result=result,
            eda_plan=plan,
            executed_steps=executed_steps,
            skipped_steps=skipped_steps,
            execution_order=execution_order,
            warnings=warnings,
            deterministic_summary=self._summary(
                executed_steps,
                skipped_steps,
                status,
            ),
            status=status,
        )

    @staticmethod
    def _validate_plan(
        plan: EDAPlan,
    ) -> None:
        step_names = [step.name for step in plan.selected_steps + plan.skipped_steps]

        if len(set(step_names)) != len(step_names):
            raise ValueError("EDAPlan step names must be unique.")

    def _execute_step(
        self,
        dataframe: pd.DataFrame,
        result: EDAResult,
        step: EDAPlanStep,
        statuses: dict[str, str],
    ) -> EDAExecutionStepResult:
        missing_columns = [
            column for column in step.required_columns if column not in dataframe.columns
        ]

        if missing_columns:
            return self._failure_record(
                step,
                "Required columns are missing from the dataset: "
                + ", ".join(missing_columns)
                + ".",
            )

        unavailable_dependencies = [
            dependency for dependency in step.dependencies if statuses.get(dependency) != "success"
        ]

        if unavailable_dependencies:
            return self._failure_record(
                step,
                "Required dependencies did not complete successfully: "
                + ", ".join(unavailable_dependencies)
                + ".",
            )

        handler = self._handlers.get(step.name)

        if handler is None:
            return self._failure_record(
                step,
                f"No deterministic handler is registered for '{step.name}'.",
            )

        try:
            output = handler.execute(
                dataframe=dataframe,
                result=result,
                step=step,
            )
        except Exception as exc:
            logger.exception("EDA execution step '%s' failed.", step.name)
            return self._failure_record(
                step,
                f"{type(exc).__name__}: {exc}",
            )

        return EDAExecutionStepResult(
            name=step.name,
            status="success",
            reason=step.reason,
            priority=step.priority,
            required_columns=list(step.required_columns),
            dependencies=list(step.dependencies),
            output=output,
            error=None,
        )

    @staticmethod
    def _failure_record(
        step: EDAPlanStep,
        error: str,
    ) -> EDAExecutionStepResult:
        return EDAExecutionStepResult(
            name=step.name,
            status="failure",
            reason=step.reason,
            priority=step.priority,
            required_columns=list(step.required_columns),
            dependencies=list(step.dependencies),
            output=None,
            error=error,
        )

    @staticmethod
    def _skipped_step_record(
        step: EDAPlanStep,
    ) -> EDAExecutionStepResult:
        return EDAExecutionStepResult(
            name=step.name,
            status="skipped",
            reason=step.reason,
            priority=step.priority,
            required_columns=list(step.required_columns),
            dependencies=list(step.dependencies),
            output=None,
            error=None,
        )

    @staticmethod
    def _execution_status(
        executed_steps: list[EDAExecutionStepResult],
    ) -> str:
        failure_count = sum(step.status == "failure" for step in executed_steps)
        success_count = sum(step.status == "success" for step in executed_steps)

        if not failure_count:
            return "success"

        return "partial_failure" if success_count else "failure"

    @staticmethod
    def _summary(
        executed_steps: list[EDAExecutionStepResult],
        skipped_steps: list[EDAExecutionStepResult],
        status: str,
    ) -> str:
        success_count = sum(step.status == "success" for step in executed_steps)
        failure_count = sum(step.status == "failure" for step in executed_steps)

        return (
            f"Executed {success_count} of {len(executed_steps)} selected step(s) "
            f"successfully; {failure_count} failed and {len(skipped_steps)} "
            f"planned step(s) remained skipped. Overall status: {status}."
        )
