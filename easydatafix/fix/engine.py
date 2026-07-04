import pandas as pd

from easydatafix.assessment.engine import AssessmentEngine
from easydatafix.models.fix_result import FixResult


class FixEngine:
    """
    Coordinates automatic dataset cleaning.
    """

    def fix(self, file_path: str, strategy: str = "smart") -> FixResult:
        """
        Automatically clean a dataset.
        """

        # Read dataset
        df = pd.read_csv(file_path)

        # Assess before cleaning
        before_report = AssessmentEngine().assess(file_path)

        # Work on a copy
        cleaned_df = df.copy()

        applied_fixes: list[str] = []

        # ------------------------------------------------------------------
        # Strategy: Remove Duplicate Rows
        # ------------------------------------------------------------------
        duplicate_count = int(cleaned_df.duplicated().sum())

        if duplicate_count > 0:
            cleaned_df = cleaned_df.drop_duplicates()
            applied_fixes.append(
                f"Removed {duplicate_count} duplicate row(s)."
            )

        # ------------------------------------------------------------------
        # Strategy: Fill Missing Values
        # ------------------------------------------------------------------
        for column in cleaned_df.columns:

            if cleaned_df[column].isna().sum() == 0:
                continue

            if pd.api.types.is_numeric_dtype(cleaned_df[column]):
                value = cleaned_df[column].median()
            else:
                mode = cleaned_df[column].mode()
                value = mode.iloc[0] if not mode.empty else ""

            cleaned_df[column] = cleaned_df[column].fillna(value)

            applied_fixes.append(
                f"Filled missing values in '{column}'."
            )

        # Save temporary cleaned file for reassessment
        temp_file = "__easydatafix_temp__.csv"
        cleaned_df.to_csv(temp_file, index=False)

        after_report = AssessmentEngine().assess(temp_file)

        return FixResult(
            dataframe=cleaned_df,
            before_report=before_report,
            after_report=after_report,
            applied_fixes=applied_fixes,
        )
