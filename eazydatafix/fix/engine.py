from pathlib import Path

import pandas as pd

from eazydatafix.assessment.engine import AssessmentEngine
from eazydatafix.core.dataset_loader import DatasetLoader
from eazydatafix.fix.column_normalizer import ColumnNormalizer
from eazydatafix.fix.duplicate_remover import DuplicateRemover
from eazydatafix.fix.empty_column_remover import EmptyColumnRemover
from eazydatafix.fix.empty_row_remover import EmptyRowRemover
from eazydatafix.fix.missing_marker_detector import MissingMarkerDetector
from eazydatafix.fix.strategies.factory import StrategyFactory
from eazydatafix.fix.whitespace_trimmer import WhitespaceTrimmer
from eazydatafix.models.cleaning_change import CleaningChange
from eazydatafix.models.fix_config import FixConfig
from eazydatafix.models.fix_result import FixResult


class FixEngine:
    """
    Coordinates automatic dataset cleaning.
    """

    def __init__(self) -> None:

        self.steps = [
            ColumnNormalizer(),
            WhitespaceTrimmer(),
            MissingMarkerDetector(),
            DuplicateRemover(),
            EmptyRowRemover(),
            EmptyColumnRemover(),
        ]

    def fix(
        self,
        file_path: str | Path | pd.DataFrame,
        config: FixConfig | None = None,
    ) -> FixResult:
        """
        Clean a supported dataset using the configured cleaning pipeline.

        Args:
            file_path: A pandas DataFrame or path to a supported dataset file.
            config: Optional configuration for the cleaning operation.

        Returns:
            A FixResult containing the cleaned dataset and assessment reports.
        """

        config = config or FixConfig()

        df = DatasetLoader.load(file_path).copy()

        assessment_engine = AssessmentEngine()

        before_report = assessment_engine.assess_dataframe(
            df=df,
            file_name=file_path,
        )

        cleaned_df = df.copy()

        applied_fixes: list[str] = []
        change_log: list[CleaningChange] = []

        # -----------------------------
        # Cleaning Pipeline
        # -----------------------------
        for step in self.steps:
            cleaned_df = self._run_step(
                step=step,
                dataframe=cleaned_df,
                config=config,
                applied_fixes=applied_fixes,
                change_log=change_log,
            )

        # -----------------------------
        # Missing Value Strategy
        # -----------------------------
        cleaned_df = self._apply_missing_value_strategies(
            dataframe=cleaned_df,
            config=config,
            applied_fixes=applied_fixes,
            change_log=change_log,
        )

        # -----------------------------
        # Final Assessment
        # -----------------------------
        after_report = assessment_engine.assess_dataframe(
            df=cleaned_df,
            file_name=file_path,
        )

        result_dataset = df.copy() if config.dry_run else cleaned_df

        return FixResult(
            dataset=result_dataset,
            before_report=before_report,
            after_report=after_report,
            applied_fixes=applied_fixes,
            change_log=change_log,
            dry_run=config.dry_run,
            proposed_dataset=cleaned_df if config.dry_run else None,
        )

    def _apply_missing_value_strategies(
        self,
        dataframe: pd.DataFrame,
        config: FixConfig,
        applied_fixes: list[str],
        change_log: list[CleaningChange],
    ) -> pd.DataFrame:
        """Apply global and explicit per-column missing-value strategies."""
        overrides = {
            column: rule.missing_value_strategy
            for column, rule in config.column_rules.items()
            if rule.missing_value_strategy is not None and column in dataframe.columns
        }
        default_columns = [column for column in dataframe.columns if column not in overrides]

        if default_columns:
            strategy = StrategyFactory.create(config.missing_value_strategy)
            dataframe = self._run_missing_strategy(
                strategy_name=config.missing_value_strategy,
                dataframe=dataframe,
                strategy=strategy,
                columns=default_columns,
                config=config,
                applied_fixes=applied_fixes,
                change_log=change_log,
            )

        for column, strategy_name in overrides.items():
            strategy = StrategyFactory.create(strategy_name)
            dataframe = self._run_missing_strategy(
                strategy_name=strategy_name,
                dataframe=dataframe,
                strategy=strategy,
                columns=[column],
                config=config,
                applied_fixes=applied_fixes,
                change_log=change_log,
            )
        return dataframe

    def _run_missing_strategy(
        self,
        strategy_name: str,
        dataframe: pd.DataFrame,
        strategy: object,
        columns: list[str],
        config: FixConfig,
        applied_fixes: list[str],
        change_log: list[CleaningChange],
    ) -> pd.DataFrame:
        """Record an auditable before-and-after snapshot for a strategy."""
        before = dataframe.copy()
        after = strategy.apply(dataframe, applied_fixes, columns=columns)
        self._record_change(
            step=f"missing_values:{strategy_name}",
            description=(
                f"Applied the {strategy_name} missing-value strategy to: " + ", ".join(columns)
            ),
            before=before,
            after=after,
            dry_run=config.dry_run,
            change_log=change_log,
        )
        return after

    def _run_step(
        self,
        step: object,
        dataframe: pd.DataFrame,
        config: FixConfig,
        applied_fixes: list[str],
        change_log: list[CleaningChange],
    ) -> pd.DataFrame:
        """Execute a FixStep and preserve its deterministic audit snapshot."""
        before = dataframe.copy()
        after = step.run(dataframe, config, applied_fixes)
        self._record_change(
            step=type(step).__name__,
            description=type(step).__doc__ or type(step).__name__,
            before=before,
            after=after,
            dry_run=config.dry_run,
            change_log=change_log,
        )
        return after

    @staticmethod
    def _record_change(
        step: str,
        description: str,
        before: pd.DataFrame,
        after: pd.DataFrame,
        dry_run: bool,
        change_log: list[CleaningChange],
    ) -> None:
        """Append an audit record only when a stage changed the dataset."""
        if before.equals(after) and list(before.columns) == list(after.columns):
            return
        change_log.append(
            CleaningChange(
                step=step,
                description=" ".join(description.split()),
                rows_before=len(before),
                rows_after=len(after),
                columns_before=len(before.columns),
                columns_after=len(after.columns),
                missing_values_before=int(before.isna().sum().sum()),
                missing_values_after=int(after.isna().sum().sum()),
                applied=not dry_run,
            )
        )
