from eazydatafix.assessment.engine import AssessmentEngine
from eazydatafix.core.dataset_loader import DatasetLoader
from eazydatafix.fix.column_normalizer import ColumnNormalizer
from eazydatafix.fix.datatype_converter import DataTypeConverter
from eazydatafix.fix.duplicate_remover import DuplicateRemover
from eazydatafix.fix.empty_column_remover import EmptyColumnRemover
from eazydatafix.fix.empty_row_remover import EmptyRowRemover
from eazydatafix.fix.strategies.factory import StrategyFactory
from eazydatafix.fix.whitespace_trimmer import WhitespaceTrimmer
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
            DuplicateRemover(),
            EmptyRowRemover(),
            EmptyColumnRemover(),
        ]

    def fix(
        self,
        file_path: str,
        config: FixConfig | None = None,
    ) -> FixResult:

        config = config or FixConfig()

        df = DatasetLoader.load(file_path)

        assessment_engine = AssessmentEngine()

        before_report = assessment_engine.assess_dataframe(
            df=df,
            file_name=file_path,
        )

        cleaned_df = df.copy()

        applied_fixes: list[str] = []

        # -----------------------------
        # Cleaning Pipeline
        # -----------------------------
        for step in self.steps:

            cleaned_df = step.run(
                cleaned_df,
                config,
                applied_fixes,
            )

        # -----------------------------
        # Missing Value Strategy
        # -----------------------------
        strategy = StrategyFactory.create(
            config.missing_value_strategy
        )

        cleaned_df = strategy.apply(
            cleaned_df,
            applied_fixes,
        )

        # -----------------------------
        # Final Assessment
        # -----------------------------
        after_report = assessment_engine.assess_dataframe(
            df=cleaned_df,
            file_name=file_path,
        )

        return FixResult(
            dataframe=cleaned_df,
            before_report=before_report,
            after_report=after_report,
            applied_fixes=applied_fixes,
        )
