from pathlib import Path

import pandas as pd

from eazydatafix.assessment.engine import AssessmentEngine
from eazydatafix.core.column_profiler import ColumnProfiler
from eazydatafix.core.dataset_loader import DatasetLoader
from eazydatafix.fix.engine import FixEngine
from eazydatafix.models.analysis_ready_config import AnalysisReadyConfig
from eazydatafix.models.analysis_ready_result import (
    AnalysisReadyIssue,
    AnalysisReadyResult,
)
from eazydatafix.models.validation_result import ValidationResult
from eazydatafix.prepare.engine import PrepareEngine
from eazydatafix.validation.engine import ValidationEngine


class AnalysisReadyEngine:
    """Compose assessment, cleaning, preparation, and final validation."""

    def __init__(self) -> None:
        self._fix_engine = FixEngine()
        self._prepare_engine = PrepareEngine()
        self._assessment_engine = AssessmentEngine()
        self._validation_engine = ValidationEngine()

    def run(
        self,
        dataset: str | Path | pd.DataFrame,
        config: AnalysisReadyConfig | None = None,
    ) -> AnalysisReadyResult:
        """Build an Analysis Ready candidate with auditable workflow evidence."""
        config = config or AnalysisReadyConfig()
        source = DatasetLoader.load(dataset).copy()

        fix_result = self._fix_engine.fix(source, config.fix_config)
        fixed_candidate = (
            fix_result.proposed_dataset
            if fix_result.dry_run and fix_result.proposed_dataset is not None
            else fix_result.dataset
        )
        preparation_report = self._prepare_engine.prepare_with_report(
            fixed_candidate,
            config.prepare_config,
        )
        candidate = preparation_report.dataset

        file_name = Path(dataset).name if isinstance(dataset, (str, Path)) else "DataFrame"
        after_report = self._assessment_engine.assess_dataframe(candidate, file_name=file_name)
        validations = self._validation_engine.validate(candidate)
        issues = self._diagnose(candidate, validations, config.nearly_empty_threshold)

        changes = [*fix_result.applied_fixes, *preparation_report.changes]
        warnings = self._unique(
            [*preparation_report.warnings, *(issue.message for issue in issues)]
        )
        dry_run = fix_result.dry_run

        return AnalysisReadyResult(
            dataset=source.copy() if dry_run else candidate,
            config=config,
            before_report=fix_result.before_report,
            after_report=after_report,
            fix_result=fix_result,
            preparation_report=preparation_report,
            validations=validations,
            issues=issues,
            changes=changes,
            warnings=warnings,
            dry_run=dry_run,
            proposed_dataset=candidate if dry_run else None,
        )

    @classmethod
    def _diagnose(
        cls,
        df: pd.DataFrame,
        validations: list[ValidationResult],
        nearly_empty_threshold: float,
    ) -> list[AnalysisReadyIssue]:
        """Detect structural and semantic blockers for reliable analysis."""
        issues: list[AnalysisReadyIssue] = []

        for column in df.columns:
            series = df[column]
            missing_ratio = float(series.isna().mean()) if len(series) else 0.0
            if missing_ratio >= nearly_empty_threshold:
                issues.append(
                    AnalysisReadyIssue(
                        code="nearly_empty",
                        column=column,
                        severity="warning",
                        message=(
                            f"Column '{column}' is nearly empty "
                            f"({missing_ratio:.0%} missing values)."
                        ),
                    )
                )

            available = series.dropna()
            if not available.empty and available.nunique(dropna=True) == 1:
                issues.append(
                    AnalysisReadyIssue(
                        code="constant",
                        column=column,
                        severity="warning",
                        message=f"Column '{column}' is constant and adds no analytical variance.",
                    )
                )

            if cls._has_inconsistent_categories(column, series):
                issues.append(
                    AnalysisReadyIssue(
                        code="inconsistent_category",
                        column=column,
                        severity="warning",
                        message=f"Column '{column}' contains inconsistent category labels.",
                    )
                )

        for validation in validations:
            if validation.passed or validation.rule == "Missing Values":
                continue
            issues.append(
                AnalysisReadyIssue(
                    code="invalid_values",
                    column=validation.column,
                    severity="error",
                    message=(
                        f"Column '{validation.column}' failed {validation.rule}: "
                        f"{validation.message}"
                    ),
                )
            )

        return issues

    @staticmethod
    def _has_inconsistent_categories(column: str, series: pd.Series) -> bool:
        """Return whether category labels differ only by case or whitespace."""
        if not (
            isinstance(series.dtype, pd.CategoricalDtype)
            or ColumnProfiler.detect(column, series) == "CATEGORY"
        ):
            return False
        values = series.dropna().astype("string")
        if values.empty:
            return False
        original_count = values.nunique(dropna=True)
        normalized_count = values.str.strip().str.casefold().nunique(dropna=True)
        return normalized_count < original_count

    @staticmethod
    def _unique(items: list[str]) -> list[str]:
        """Deduplicate messages while preserving deterministic order."""
        return list(dict.fromkeys(items))
