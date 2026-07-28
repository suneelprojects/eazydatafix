from eazydatafix.models.eda_plan import EDAPlan, EDAPlanStep
from eazydatafix.models.eda_result import EDAResult

_MIN_DISTRIBUTION_ROWS = 2
_MIN_SKEWNESS_ROWS = 3
_MIN_ROBUST_ANALYSIS_ROWS = 5
_HIGH_MISSING_RATIO = 0.10
_HIGH_DUPLICATE_RATIO = 0.05
_HIGH_CLASS_DOMINANCE = 0.80
_MAX_CLASS_VALUES = 20
_TARGET_NAME_TOKENS = {
    "churn",
    "class",
    "default",
    "label",
    "outcome",
    "response",
    "status",
    "target",
}


class EDAPlanner:
    """
    Builds deterministic follow-up analysis plans from EDA results.
    """

    def plan(
        self,
        result: EDAResult,
    ) -> EDAPlan:
        """
        Build a structured analysis plan from an existing EDA result.

        Args:
            result: The deterministic EDA result to plan from.

        Returns:
            An EDAPlan containing selected and skipped analysis decisions.

        Raises:
            TypeError: If result is not an EDAResult.
        """
        if not isinstance(result, EDAResult):
            raise TypeError(
                "plan_eda() expected an EDAResult. " "Generate one first with eazydatafix.eda(...)."
            )

        decisions = [
            self._missing_value_analysis(result),
            self._duplicate_review(result),
            self._identifier_exclusion(result),
            self._numeric_distribution_analysis(result),
            self._outlier_analysis(result),
            self._skewness_analysis(result),
            self._categorical_distribution_analysis(result),
            self._boolean_distribution_analysis(result),
            self._class_imbalance_analysis(result),
            self._correlation_review(result),
            self._datetime_trend_analysis(result),
        ]
        selected_steps = [step for selected, step in decisions if selected]
        skipped_steps = [step for selected, step in decisions if not selected]
        warnings = self._warnings(result)

        return EDAPlan(
            selected_steps=selected_steps,
            skipped_steps=skipped_steps,
            warnings=warnings,
            deterministic_summary=self._summary(
                result,
                selected_steps,
                skipped_steps,
            ),
        )

    @staticmethod
    def _missing_value_analysis(
        result: EDAResult,
    ) -> tuple[bool, EDAPlanStep]:
        columns = [
            column for column in result.column_names if result.missing_values.get(column, 0) > 0
        ]
        total_missing = sum(result.missing_values.values())

        if not total_missing:
            return EDAPlanner._skip(
                name="missing_value_analysis",
                reason="No missing values were detected.",
            )

        total_cells = max(result.shape[0] * result.shape[1], 1)
        missing_ratio = total_missing / total_cells

        return EDAPlanner._select(
            name="missing_value_analysis",
            reason=(
                f"{total_missing} missing value(s) were detected across "
                f"{len(columns)} column(s)."
            ),
            priority="high" if missing_ratio >= _HIGH_MISSING_RATIO else "medium",
            required_columns=columns,
        )

    @staticmethod
    def _duplicate_review(
        result: EDAResult,
    ) -> tuple[bool, EDAPlanStep]:
        if not result.duplicate_rows:
            return EDAPlanner._skip(
                name="duplicate_review",
                reason="No duplicate rows were detected.",
            )

        duplicate_ratio = result.duplicate_rows / max(result.shape[0], 1)

        return EDAPlanner._select(
            name="duplicate_review",
            reason=f"{result.duplicate_rows} duplicate row(s) require review.",
            priority="high" if duplicate_ratio >= _HIGH_DUPLICATE_RATIO else "medium",
            required_columns=result.column_names,
        )

    @staticmethod
    def _identifier_exclusion(
        result: EDAResult,
    ) -> tuple[bool, EDAPlanStep]:
        if not result.identifier_columns:
            return EDAPlanner._skip(
                name="identifier_exclusion",
                reason="No identifier columns were detected.",
            )

        return EDAPlanner._select(
            name="identifier_exclusion",
            reason=(
                f"{len(result.identifier_columns)} identifier column(s) must be "
                "excluded from feature-oriented analyses."
            ),
            priority="high",
            required_columns=result.identifier_columns,
        )

    @staticmethod
    def _numeric_distribution_analysis(
        result: EDAResult,
    ) -> tuple[bool, EDAPlanStep]:
        if not result.numeric_columns:
            return EDAPlanner._skip(
                name="numeric_distribution_analysis",
                reason="No numeric measures were detected.",
            )

        if result.shape[0] < _MIN_DISTRIBUTION_ROWS:
            return EDAPlanner._skip(
                name="numeric_distribution_analysis",
                reason="Numeric distribution analysis requires at least 2 rows.",
                required_columns=result.numeric_columns,
            )

        return EDAPlanner._select(
            name="numeric_distribution_analysis",
            reason=(
                f"{len(result.numeric_columns)} numeric measure(s) are available "
                "for distribution analysis."
            ),
            priority="medium",
            required_columns=result.numeric_columns,
        )

    @staticmethod
    def _outlier_analysis(
        result: EDAResult,
    ) -> tuple[bool, EDAPlanStep]:
        dependencies = ["numeric_distribution_analysis"]

        if not result.numeric_columns:
            return EDAPlanner._skip(
                name="outlier_analysis",
                reason="Outlier analysis requires numeric measures.",
                dependencies=dependencies,
            )

        if result.shape[0] < _MIN_ROBUST_ANALYSIS_ROWS:
            return EDAPlanner._skip(
                name="outlier_analysis",
                reason="Outlier analysis requires at least 5 rows for a useful result.",
                required_columns=result.numeric_columns,
                dependencies=dependencies,
            )

        return EDAPlanner._select(
            name="outlier_analysis",
            reason=(
                f"{len(result.numeric_columns)} numeric measure(s) have enough "
                "rows for deterministic outlier analysis."
            ),
            priority="medium",
            required_columns=result.numeric_columns,
            dependencies=dependencies,
        )

    @staticmethod
    def _skewness_analysis(
        result: EDAResult,
    ) -> tuple[bool, EDAPlanStep]:
        dependencies = ["numeric_distribution_analysis"]

        if not result.numeric_columns:
            return EDAPlanner._skip(
                name="skewness_analysis",
                reason="Skewness analysis requires numeric measures.",
                dependencies=dependencies,
            )

        if result.shape[0] < _MIN_SKEWNESS_ROWS:
            return EDAPlanner._skip(
                name="skewness_analysis",
                reason="Skewness analysis requires at least 3 rows.",
                required_columns=result.numeric_columns,
                dependencies=dependencies,
            )

        return EDAPlanner._select(
            name="skewness_analysis",
            reason=(
                f"{len(result.numeric_columns)} numeric measure(s) are available "
                "for skewness analysis."
            ),
            priority="low",
            required_columns=result.numeric_columns,
            dependencies=dependencies,
        )

    @staticmethod
    def _categorical_distribution_analysis(
        result: EDAResult,
    ) -> tuple[bool, EDAPlanStep]:
        if not result.categorical_columns:
            return EDAPlanner._skip(
                name="categorical_distribution_analysis",
                reason="No categorical columns were detected.",
            )

        if not result.shape[0]:
            return EDAPlanner._skip(
                name="categorical_distribution_analysis",
                reason="Categorical distribution analysis requires at least 1 row.",
                required_columns=result.categorical_columns,
            )

        return EDAPlanner._select(
            name="categorical_distribution_analysis",
            reason=(
                f"{len(result.categorical_columns)} categorical column(s) are "
                "available for distribution analysis."
            ),
            priority="medium",
            required_columns=result.categorical_columns,
        )

    @staticmethod
    def _boolean_distribution_analysis(
        result: EDAResult,
    ) -> tuple[bool, EDAPlanStep]:
        if not result.boolean_columns:
            return EDAPlanner._skip(
                name="boolean_distribution_analysis",
                reason="No boolean columns were detected.",
            )

        if not result.shape[0]:
            return EDAPlanner._skip(
                name="boolean_distribution_analysis",
                reason="Boolean distribution analysis requires at least 1 row.",
                required_columns=result.boolean_columns,
            )

        return EDAPlanner._select(
            name="boolean_distribution_analysis",
            reason=(
                f"{len(result.boolean_columns)} boolean column(s) are available "
                "for distribution analysis."
            ),
            priority="medium",
            required_columns=result.boolean_columns,
        )

    @staticmethod
    def _class_imbalance_analysis(
        result: EDAResult,
    ) -> tuple[bool, EDAPlanStep]:
        candidates = EDAPlanner._class_imbalance_candidates(result)
        dependencies = EDAPlanner._class_imbalance_dependencies(result, candidates)

        if not candidates:
            return EDAPlanner._skip(
                name="class_imbalance_analysis",
                reason="No suitable categorical, boolean, or target-like columns were detected.",
                dependencies=dependencies,
            )

        if result.shape[0] < _MIN_ROBUST_ANALYSIS_ROWS:
            return EDAPlanner._skip(
                name="class_imbalance_analysis",
                reason="Class imbalance analysis requires at least 5 rows.",
                required_columns=candidates,
                dependencies=dependencies,
            )

        dominant_columns = EDAPlanner._dominant_class_columns(result, candidates)
        reason = (
            "Potential class dominance was already observed in: "
            + ", ".join(dominant_columns)
            + "."
            if dominant_columns
            else (
                f"{len(candidates)} low-cardinality or target-like column(s) are "
                "suitable for class imbalance analysis."
            )
        )

        return EDAPlanner._select(
            name="class_imbalance_analysis",
            reason=reason,
            priority="high" if dominant_columns else "medium",
            required_columns=candidates,
            dependencies=dependencies,
        )

    @staticmethod
    def _correlation_review(
        result: EDAResult,
    ) -> tuple[bool, EDAPlanStep]:
        dependencies = ["numeric_distribution_analysis"]

        if len(result.numeric_columns) < 2:
            return EDAPlanner._skip(
                name="correlation_review",
                reason="Correlation review requires at least 2 numeric measures.",
                required_columns=result.numeric_columns,
                dependencies=dependencies,
            )

        if result.shape[0] < _MIN_DISTRIBUTION_ROWS:
            return EDAPlanner._skip(
                name="correlation_review",
                reason="Correlation review requires at least 2 rows.",
                required_columns=result.numeric_columns,
                dependencies=dependencies,
            )

        return EDAPlanner._select(
            name="correlation_review",
            reason=(
                f"{len(result.numeric_columns)} numeric measures are available "
                "for pairwise correlation review."
            ),
            priority="medium",
            required_columns=result.numeric_columns,
            dependencies=dependencies,
        )

    @staticmethod
    def _datetime_trend_analysis(
        result: EDAResult,
    ) -> tuple[bool, EDAPlanStep]:
        if not result.datetime_columns:
            return EDAPlanner._skip(
                name="datetime_trend_analysis",
                reason="No datetime columns were detected.",
            )

        if result.shape[0] < _MIN_DISTRIBUTION_ROWS:
            return EDAPlanner._skip(
                name="datetime_trend_analysis",
                reason="Datetime trend analysis requires at least 2 rows.",
                required_columns=result.datetime_columns,
            )

        return EDAPlanner._select(
            name="datetime_trend_analysis",
            reason=(
                f"{len(result.datetime_columns)} datetime column(s) are available "
                "for trend analysis."
            ),
            priority="medium",
            required_columns=result.datetime_columns,
        )

    @staticmethod
    def _class_imbalance_candidates(
        result: EDAResult,
    ) -> list[str]:
        candidates: list[str] = []

        for column in result.categorical_columns:
            unique_count = result.unique_value_counts.get(column, 0)
            summary = result.categorical_summaries.get(column, {})
            observed_count = int(summary.get("count", 0))
            is_target_like = EDAPlanner._is_target_like(column)
            is_low_cardinality = (
                observed_count >= _MIN_ROBUST_ANALYSIS_ROWS
                and 2 <= unique_count <= min(_MAX_CLASS_VALUES, max(observed_count // 2, 2))
            )

            if is_target_like or is_low_cardinality:
                candidates.append(column)

        for column in result.boolean_columns:
            if result.unique_value_counts.get(column, 0) >= 2:
                candidates.append(column)

        for column in result.numeric_columns:
            unique_count = result.unique_value_counts.get(column, 0)

            if EDAPlanner._is_target_like(column) and 2 <= unique_count <= _MAX_CLASS_VALUES:
                candidates.append(column)

        return candidates

    @staticmethod
    def _class_imbalance_dependencies(
        result: EDAResult,
        candidates: list[str],
    ) -> list[str]:
        dependencies: list[str] = []

        if any(column in result.categorical_columns for column in candidates):
            dependencies.append("categorical_distribution_analysis")

        if any(column in result.boolean_columns for column in candidates):
            dependencies.append("boolean_distribution_analysis")

        if any(column in result.numeric_columns for column in candidates):
            dependencies.append("numeric_distribution_analysis")

        return dependencies

    @staticmethod
    def _dominant_class_columns(
        result: EDAResult,
        candidates: list[str],
    ) -> list[str]:
        dominant_columns: list[str] = []

        for column in candidates:
            summary = result.categorical_summaries.get(column)

            if not summary:
                continue

            observed_count = int(summary.get("count", 0))
            most_frequent_count = int(summary.get("most_frequent_count", 0))

            if observed_count and most_frequent_count / observed_count >= _HIGH_CLASS_DOMINANCE:
                dominant_columns.append(column)

        return dominant_columns

    @staticmethod
    def _is_target_like(
        column: str,
    ) -> bool:
        normalized_name = "_".join(
            part
            for part in "".join(
                character.lower() if character.isalnum() else "_" for character in column
            ).split("_")
            if part
        )
        tokens = set(normalized_name.split("_"))

        return bool(tokens & _TARGET_NAME_TOKENS)

    @staticmethod
    def _warnings(
        result: EDAResult,
    ) -> list[str]:
        warnings: list[str] = []
        row_count, column_count = result.shape

        if row_count == 0:
            warnings.append("Dataset is empty; all data-dependent analyses were skipped.")
        elif row_count < _MIN_ROBUST_ANALYSIS_ROWS:
            warnings.append(
                f"Dataset has only {row_count} row(s); robust statistical "
                "conclusions may be unreliable."
            )

        if result.column_names and len(result.identifier_columns) == column_count:
            warnings.append(
                "Dataset contains only identifier columns; no feature-oriented "
                "analysis is available."
            )

        constant_columns = [
            column
            for column in result.column_names
            if (
                column not in result.identifier_columns
                and result.unique_value_counts.get(column, 0) <= 1
            )
        ]

        if constant_columns:
            warnings.append(
                "Constant or empty columns may limit analysis: " + ", ".join(constant_columns) + "."
            )

        return warnings

    @staticmethod
    def _summary(
        result: EDAResult,
        selected_steps: list[EDAPlanStep],
        skipped_steps: list[EDAPlanStep],
    ) -> str:
        selected_names = ", ".join(step.name for step in selected_steps)
        selection_detail = (
            f" Selected steps: {selected_names}."
            if selected_names
            else " No analysis steps were selected."
        )

        return (
            f"Selected {len(selected_steps)} of "
            f"{len(selected_steps) + len(skipped_steps)} deterministic analysis "
            f"steps for a dataset with {result.shape[0]} row(s) and "
            f"{result.shape[1]} column(s); skipped {len(skipped_steps)}." + selection_detail
        )

    @staticmethod
    def _select(
        name: str,
        reason: str,
        priority: str,
        required_columns: list[str],
        dependencies: list[str] | None = None,
    ) -> tuple[bool, EDAPlanStep]:
        return (
            True,
            EDAPlanStep(
                name=name,
                reason=reason,
                priority=priority,
                required_columns=list(required_columns),
                dependencies=list(dependencies or []),
            ),
        )

    @staticmethod
    def _skip(
        name: str,
        reason: str,
        required_columns: list[str] | None = None,
        dependencies: list[str] | None = None,
    ) -> tuple[bool, EDAPlanStep]:
        return (
            False,
            EDAPlanStep(
                name=name,
                reason=reason,
                priority="not_applicable",
                required_columns=list(required_columns or []),
                dependencies=list(dependencies or []),
            ),
        )
