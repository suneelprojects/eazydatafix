from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from eazydatafix.models.analysis_ready_config import AnalysisReadyConfig
from eazydatafix.models.assessment_report import AssessmentReport
from eazydatafix.models.fix_result import FixResult
from eazydatafix.models.preparation_report import PreparationReport
from eazydatafix.models.validation_result import ValidationResult


@dataclass(frozen=True, slots=True)
class AnalysisReadyIssue:
    """Describe a deterministic issue that can affect analytical usefulness."""

    code: str
    column: str
    severity: str
    message: str


@dataclass(slots=True)
class AnalysisReadyResult:
    """Return the dataset and evidence produced by the Analysis Ready workflow."""

    dataset: pd.DataFrame
    config: AnalysisReadyConfig
    before_report: AssessmentReport
    after_report: AssessmentReport
    fix_result: FixResult
    preparation_report: PreparationReport
    validations: list[ValidationResult]
    issues: list[AnalysisReadyIssue]
    changes: list[str]
    warnings: list[str]
    dry_run: bool = False
    proposed_dataset: pd.DataFrame | None = None

    @property
    def before_score(self) -> float:
        """Return the quality score before readiness transformations."""
        return self.before_report.quality.score

    @property
    def after_score(self) -> float:
        """Return the quality score after readiness transformations."""
        return self.after_report.quality.score

    @property
    def improvement(self) -> float:
        """Return the deterministic score change produced by the workflow."""
        return round(self.after_score - self.before_score, 2)

    @property
    def is_ready(self) -> bool:
        """Return whether the candidate meets the configured readiness gate."""
        has_errors = any(issue.severity == "error" for issue in self.issues)
        return self.after_score >= self.config.minimum_readiness_score and not has_errors

    def save(
        self,
        path: str | Path,
        *,
        index: bool = False,
        **kwargs: object,
    ) -> None:
        """Save the returned Analysis Ready dataset as CSV."""
        self.dataset.to_csv(path, index=index, **kwargs)
