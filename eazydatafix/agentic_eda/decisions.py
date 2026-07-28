from dataclasses import dataclass, field
from typing import Any

from eazydatafix.models.agentic_eda_config import AgenticEDAConfig
from eazydatafix.models.agentic_eda_result import (
    FollowUpAction,
    PriorityFinding,
    UnresolvedQuestion,
    VisualisationRecommendation,
)
from eazydatafix.models.eda_execution_result import (
    EDAExecutionResult,
    EDAExecutionStepResult,
)

_PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


@dataclass(slots=True)
class FollowUpDecisions:
    """Collects the deterministic decisions generated after EDA execution."""

    actions: list[FollowUpAction] = field(default_factory=list)
    questions: list[UnresolvedQuestion] = field(default_factory=list)
    visualisations: list[VisualisationRecommendation] = field(default_factory=list)
    findings: list[PriorityFinding] = field(default_factory=list)


class FollowUpDecisionEngine:
    """Generates traceable follow-up decisions from successful step outputs."""

    def generate(
        self,
        execution: EDAExecutionResult,
        config: AgenticEDAConfig,
    ) -> FollowUpDecisions:
        """
        Generate deterministic actions, questions, visualisations, and findings.

        Args:
            execution: Completed deterministic EDA execution.
            config: Validated orchestration configuration.

        Returns:
            Structured follow-up decisions in deterministic order.
        """
        decisions = FollowUpDecisions()
        handlers = {
            "missing_value_analysis": self._missing_values,
            "duplicate_review": self._duplicates,
            "identifier_exclusion": self._identifiers,
            "outlier_analysis": self._outliers,
            "skewness_analysis": self._skewness,
            "categorical_distribution_analysis": self._categorical,
            "boolean_distribution_analysis": self._boolean,
            "class_imbalance_analysis": self._class_imbalance,
            "correlation_review": self._correlations,
            "datetime_trend_analysis": self._datetime,
        }

        for step in execution.executed_steps:
            if step.status != "success" or step.output is None:
                continue

            handler = handlers.get(step.name)

            if handler is not None:
                handler(step, decisions, config)

        limit = config.max_recommendations_per_category
        decisions.actions = self._sort_by_priority(decisions.actions)[:limit]
        decisions.questions = (
            self._sort_by_priority(decisions.questions)[:limit]
            if config.enable_unresolved_questions
            else []
        )
        decisions.visualisations = (
            self._sort_by_priority(decisions.visualisations)[:limit]
            if config.enable_visualisation_recommendations
            else []
        )
        decisions.findings = self._sort_by_priority(decisions.findings)[:limit]
        return decisions

    def _missing_values(
        self,
        step: EDAExecutionStepResult,
        decisions: FollowUpDecisions,
        config: AgenticEDAConfig,
    ) -> None:
        output = self._output(step)
        affected = output.get("affected_columns", [])

        if not affected:
            return

        columns = [str(item["column"]) for item in affected]
        percentage = float(output.get("percentage", 0.0))
        priority = "high" if percentage >= 10 else "medium"
        reason = (
            f"{output.get('count', 0)} missing value(s) affect "
            f"{len(columns)} column(s); review imputation and row or column removal."
        )
        self._add_action(
            decisions,
            "missing_value_remediation",
            columns,
            reason,
            priority,
            step.name,
            ["Confirm the missingness mechanism.", "Review downstream data requirements."],
        )
        self._add_finding(
            decisions,
            "missing_values",
            columns,
            reason,
            priority,
            step.name,
        )
        self._add_visualisation(
            decisions,
            config,
            "missing_value_chart",
            columns,
            "Compare missing-value counts and percentages across affected columns.",
            priority,
            step.name,
            ["Missing-value analysis completed successfully."],
        )

        for column in columns:
            self._add_question(
                decisions,
                config,
                "missingness_context",
                [column],
                f"Is {column} missing at random, or does its absence carry domain meaning?",
                "The missingness mechanism cannot be established from descriptive statistics.",
                priority,
                step.name,
                ["Consult the data owner or collection specification."],
            )

    def _duplicates(
        self,
        step: EDAExecutionStepResult,
        decisions: FollowUpDecisions,
        config: AgenticEDAConfig,
    ) -> None:
        output = self._output(step)
        count = int(output.get("duplicate_count", 0))

        if not count:
            return

        percentage = float(output.get("duplicate_percentage", 0.0))
        priority = "high" if percentage >= 5 else "medium"
        reason = (
            f"{count} duplicate row(s) were detected ({percentage}%); confirm whether "
            "they are redundant records or valid repeated events."
        )
        self._add_action(
            decisions,
            "duplicate_resolution",
            list(step.required_columns),
            reason,
            priority,
            step.name,
            ["Define the dataset's business key.", "Confirm valid repeat-event semantics."],
        )
        self._add_finding(
            decisions,
            "duplicate_rows",
            list(step.required_columns),
            reason,
            priority,
            step.name,
        )
        self._add_question(
            decisions,
            config,
            "duplicate_semantics",
            list(step.required_columns),
            "Do duplicate rows represent data-entry duplication or valid repeated events?",
            "Only domain knowledge can determine whether equal rows are invalid.",
            priority,
            step.name,
            ["Identify record and event grain."],
        )

    def _identifiers(
        self,
        step: EDAExecutionStepResult,
        decisions: FollowUpDecisions,
        config: AgenticEDAConfig,
    ) -> None:
        excluded = self._output(step).get("excluded_columns", [])

        for item in excluded:
            column = str(item["column"])
            reason = (
                f"{column} is classified as an identifier and should remain excluded "
                "from model-feature statistics."
            )
            self._add_action(
                decisions,
                "identifier_feature_exclusion",
                [column],
                reason,
                "high",
                step.name,
                ["Confirm the identifier is not a meaningful ordinal measure."],
            )
            self._add_finding(
                decisions,
                "identifier_detected",
                [column],
                reason,
                "high",
                step.name,
            )
            self._add_question(
                decisions,
                config,
                "identifier_retention",
                [column],
                f"Should {column} remain in the analytical dataset for joins or auditing?",
                "Retention depends on governance, privacy, and traceability needs.",
                "medium",
                step.name,
                ["Review privacy and data-governance requirements."],
            )

    def _outliers(
        self,
        step: EDAExecutionStepResult,
        decisions: FollowUpDecisions,
        config: AgenticEDAConfig,
    ) -> None:
        for column, metrics in self._columns(step).items():
            count = int(metrics.get("outlier_count", 0))

            if not count:
                continue

            percentage = float(metrics.get("outlier_percentage", 0.0))
            priority = "high" if percentage >= 10 else "medium"
            reason = (
                f"{column} has {count} IQR outlier(s) ({percentage}%); inspect, cap, "
                "transform, or validate them against domain rules."
            )
            self._add_action(
                decisions,
                "outlier_review",
                [column],
                reason,
                priority,
                step.name,
                [
                    f"Use the configured IQR multiplier of {config.outlier_iqr_multiplier}.",
                    "Confirm domain-valid ranges.",
                ],
            )
            self._add_finding(
                decisions,
                "outliers_detected",
                [column],
                reason,
                priority,
                step.name,
            )
            self._add_visualisation(
                decisions,
                config,
                "box_plot",
                [column],
                f"Show the distribution and IQR outliers detected in {column}.",
                priority,
                step.name,
                ["Numeric values are available."],
            )
            self._add_question(
                decisions,
                config,
                "outlier_validity",
                [column],
                f"Are detected outliers in {column} valid business cases?",
                "Statistical boundaries cannot determine business validity.",
                priority,
                step.name,
                ["Confirm expected domain ranges and exceptional cases."],
            )

    def _skewness(
        self,
        step: EDAExecutionStepResult,
        decisions: FollowUpDecisions,
        config: AgenticEDAConfig,
    ) -> None:
        for column, metrics in self._columns(step).items():
            interpretation = str(metrics.get("interpretation", ""))

            if not interpretation.startswith("highly_"):
                continue

            skewness = metrics.get("skewness")
            reason = (
                f"{column} is {interpretation.replace('_', ' ')} "
                f"(skewness {skewness}); review log, power, or robust transformations."
            )
            self._add_action(
                decisions,
                "skewness_transformation_review",
                [column],
                reason,
                "medium",
                step.name,
                ["Confirm values and modelling assumptions permit transformation."],
            )
            self._add_finding(
                decisions,
                "high_skewness",
                [column],
                reason,
                "medium",
                step.name,
            )
            self._add_visualisation(
                decisions,
                config,
                "histogram",
                [column],
                f"Inspect the highly skewed distribution of {column}.",
                "medium",
                step.name,
                ["Numeric distribution analysis completed successfully."],
            )

    def _categorical(
        self,
        step: EDAExecutionStepResult,
        decisions: FollowUpDecisions,
        config: AgenticEDAConfig,
    ) -> None:
        for column in self._columns(step):
            self._add_visualisation(
                decisions,
                config,
                "bar_chart",
                [column],
                f"Compare category frequencies for {column}.",
                "medium",
                step.name,
                ["Categorical distribution analysis completed successfully."],
            )

    def _boolean(
        self,
        step: EDAExecutionStepResult,
        decisions: FollowUpDecisions,
        config: AgenticEDAConfig,
    ) -> None:
        for column in self._columns(step):
            self._add_visualisation(
                decisions,
                config,
                "bar_chart",
                [column],
                f"Compare true, false, and missing values for {column}.",
                "low",
                step.name,
                ["Boolean distribution analysis completed successfully."],
            )

    def _class_imbalance(
        self,
        step: EDAExecutionStepResult,
        decisions: FollowUpDecisions,
        config: AgenticEDAConfig,
    ) -> None:
        for column, metrics in self._columns(step).items():
            is_imbalanced = bool(metrics.get("is_imbalanced", False))
            percentage = float(metrics.get("dominant_percentage", 0.0))
            question_priority = "high" if is_imbalanced else "medium"
            self._add_question(
                decisions,
                config,
                "target_confirmation",
                [column],
                f"Is {column} the intended modelling target?",
                "Target intent cannot be inferred conclusively from its values or name.",
                question_priority,
                step.name,
                ["Confirm the modelling objective."],
            )

            if not is_imbalanced:
                continue

            reason = (
                f"{column} is dominated by {metrics.get('dominant_class')} at "
                f"{percentage}%; review resampling, class weights, and evaluation metrics."
            )
            self._add_action(
                decisions,
                "class_imbalance_strategy",
                [column],
                reason,
                "high",
                step.name,
                ["Confirm the modelling target.", "Choose task-appropriate metrics."],
            )
            self._add_finding(
                decisions,
                "class_imbalance",
                [column],
                reason,
                "high",
                step.name,
            )
            self._add_visualisation(
                decisions,
                config,
                "class_distribution_chart",
                [column],
                f"Show class dominance in {column}.",
                "high",
                step.name,
                ["Class-imbalance analysis completed successfully."],
            )

    def _correlations(
        self,
        step: EDAExecutionStepResult,
        decisions: FollowUpDecisions,
        config: AgenticEDAConfig,
    ) -> None:
        pairs = self._output(step).get("pairwise_correlations", [])
        strong_pairs = [
            pair
            for pair in pairs
            if pair.get("correlation") is not None
            and abs(float(pair["correlation"])) >= config.correlation_threshold
        ]

        if not strong_pairs:
            return

        visual_columns: list[str] = []

        for pair in strong_pairs:
            columns = [str(pair["column_a"]), str(pair["column_b"])]

            for column in columns:
                if column not in visual_columns:
                    visual_columns.append(column)

            reason = (
                f"{columns[0]} and {columns[1]} have correlation "
                f"{float(pair['correlation']):.3f}; review multicollinearity."
            )
            self._add_action(
                decisions,
                "multicollinearity_review",
                columns,
                reason,
                "high",
                step.name,
                ["Confirm the relationship is meaningful and not caused by leakage."],
            )
            self._add_finding(
                decisions,
                "strong_correlation",
                columns,
                reason,
                "high",
                step.name,
            )

        self._add_visualisation(
            decisions,
            config,
            "correlation_heatmap",
            visual_columns,
            "Compare strong pairwise relationships between numeric measures.",
            "high",
            step.name,
            ["At least two numeric measures are available."],
        )

    def _datetime(
        self,
        step: EDAExecutionStepResult,
        decisions: FollowUpDecisions,
        config: AgenticEDAConfig,
    ) -> None:
        for column, metrics in self._columns(step).items():
            if int(metrics.get("parsed_valid_count", 0)) == 0:
                continue

            reason = (
                f"{column} spans {metrics.get('earliest')} to {metrics.get('latest')}; "
                "review time-based grouping and trend analysis."
            )
            self._add_action(
                decisions,
                "datetime_trend_review",
                [column],
                reason,
                "medium",
                step.name,
                ["Confirm the date's business meaning and time grain."],
            )
            self._add_finding(
                decisions,
                "datetime_coverage",
                [column],
                reason,
                "medium",
                step.name,
            )
            self._add_visualisation(
                decisions,
                config,
                "time_series_line_chart",
                [column],
                f"Inspect record frequency or a selected measure over {column}.",
                "medium",
                step.name,
                ["Choose an aggregation and, where applicable, a numeric measure."],
            )
            self._add_question(
                decisions,
                config,
                "datetime_semantics",
                [column],
                f"Is {column} intended as an event date or a business lifecycle date?",
                "The column values establish time coverage but not business meaning.",
                "medium",
                step.name,
                ["Confirm date semantics with the data owner."],
            )

    @staticmethod
    def _output(
        step: EDAExecutionStepResult,
    ) -> dict[str, Any]:
        return step.output or {}

    def _columns(
        self,
        step: EDAExecutionStepResult,
    ) -> dict[str, dict[str, Any]]:
        return self._output(step).get("columns", {})

    @staticmethod
    def _add_action(
        decisions: FollowUpDecisions,
        action_type: str,
        columns: list[str],
        reason: str,
        priority: str,
        source_step: str,
        prerequisites: list[str],
    ) -> None:
        decisions.actions.append(
            FollowUpAction(
                type=action_type,
                target_columns=columns,
                reason=reason,
                priority=priority,
                source_step=source_step,
                prerequisites=prerequisites,
            )
        )

    @staticmethod
    def _add_visualisation(
        decisions: FollowUpDecisions,
        config: AgenticEDAConfig,
        visualisation_type: str,
        columns: list[str],
        reason: str,
        priority: str,
        source_step: str,
        prerequisites: list[str],
    ) -> None:
        if not config.enable_visualisation_recommendations:
            return

        decisions.visualisations.append(
            VisualisationRecommendation(
                type=visualisation_type,
                target_columns=columns,
                reason=reason,
                priority=priority,
                source_step=source_step,
                prerequisites=prerequisites,
            )
        )

    @staticmethod
    def _add_question(
        decisions: FollowUpDecisions,
        config: AgenticEDAConfig,
        question_type: str,
        columns: list[str],
        question: str,
        reason: str,
        priority: str,
        source_step: str,
        prerequisites: list[str],
    ) -> None:
        if not config.enable_unresolved_questions:
            return

        decisions.questions.append(
            UnresolvedQuestion(
                type=question_type,
                target_columns=columns,
                question=question,
                reason=reason,
                priority=priority,
                source_step=source_step,
                prerequisites=prerequisites,
            )
        )

    @staticmethod
    def _add_finding(
        decisions: FollowUpDecisions,
        finding_type: str,
        columns: list[str],
        reason: str,
        priority: str,
        source_step: str,
    ) -> None:
        decisions.findings.append(
            PriorityFinding(
                type=finding_type,
                target_columns=columns,
                reason=reason,
                priority=priority,
                source_step=source_step,
                prerequisites=["Source execution step completed successfully."],
            )
        )

    @staticmethod
    def _sort_by_priority(items: list[Any]) -> list[Any]:
        return sorted(
            items,
            key=lambda item: _PRIORITY_ORDER.get(item.priority, 3),
        )
