import pandas as pd

from easydatafix.assessment.engine import AssessmentEngine
from easydatafix.core.dataset_loader import DatasetLoader
from easydatafix.fix.strategies.factory import StrategyFactory
from easydatafix.models.fix_config import FixConfig
from easydatafix.models.fix_result import FixResult


class FixEngine:
    """
    Coordinates automatic dataset cleaning.
    """

    def fix(
        self,
        file_path: str,
        config: FixConfig | None = None,
    ) -> FixResult:

        config = config or FixConfig()

        df = DatasetLoader.load(file_path)

        assessment_engine = AssessmentEngine()

        before_report = assessment_engine.assess_dataframe(df)

        cleaned_df = df.copy()

        applied_fixes: list[str] = []

        # ---------------------------------------------
        # Remove duplicate rows
        # ---------------------------------------------
        if config.remove_duplicates:

            duplicate_count = int(cleaned_df.duplicated().sum())

            if duplicate_count > 0:
                cleaned_df = cleaned_df.drop_duplicates()

                applied_fixes.append(
                    f"Removed {duplicate_count} duplicate row(s)."
                )

        # ---------------------------------------------
        # Remove empty rows
        # ---------------------------------------------
        if config.remove_empty_rows:

            before = len(cleaned_df)

            cleaned_df = cleaned_df.dropna(how="all")

            removed = before - len(cleaned_df)

            if removed > 0:
                applied_fixes.append(
                    f"Removed {removed} empty row(s)."
                )

        # ---------------------------------------------
        # Remove empty columns
        # ---------------------------------------------
        if config.remove_empty_columns:

            before = len(cleaned_df.columns)

            cleaned_df = cleaned_df.dropna(axis=1, how="all")

            removed = before - len(cleaned_df.columns)

            if removed > 0:
                applied_fixes.append(
                    f"Removed {removed} empty column(s)."
                )

        # ---------------------------------------------
        # Missing Value Strategy
        # ---------------------------------------------
        strategy = StrategyFactory.create(
            config.missing_value_strategy
        )

        cleaned_df = strategy.apply(
            cleaned_df,
            applied_fixes,
        )

        # ---------------------------------------------
        # Final Assessment
        # ---------------------------------------------
        after_report = assessment_engine.assess_dataframe(cleaned_df)

        return FixResult(
            dataframe=cleaned_df,
            before_report=before_report,
            after_report=after_report,
            applied_fixes=applied_fixes,
        )
