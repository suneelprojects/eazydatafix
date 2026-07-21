from pathlib import Path

import pandas as pd

from .assessment.engine import AssessmentEngine
from .assessment.ai_readiness import AIReadinessEngine
from .assessment.profiler import DatasetProfiler
from .console_report import Report
from .fix.engine import FixEngine
from .models.assessment_report import AssessmentReport
from .models.ai_readiness_report import AIReadinessReport
from .models.dataset_profile import DatasetProfile
from .models.fix_config import FixConfig
from .models.fix_result import FixResult
from .prepare.engine import PrepareEngine
from .models.ready_result import ReadyResult

__version__ = "0.2.1"

__all__ = [
    "__version__",
    "AIReadinessEngine",
    "AIReadinessReport",
    "AssessmentEngine",
    "AssessmentReport",
    "DatasetProfiler",
    "DatasetProfile",
    "FixConfig",
    "FixEngine",
    "FixResult",
    "PrepareEngine",
    "Report",
    "analysis_ready",
    "assess_ai_readiness",
    "assess",
    "fix",
    "prepare",
    "profile",
]


def profile(
    dataset: str | Path | pd.DataFrame,
) -> DatasetProfile:
    """
    Generate a structural profile for a dataset.

    Args:
        dataset: A pandas DataFrame or path to a supported dataset file.

    Returns:
        A DatasetProfile containing structural dataset information.
    """
    profiler = DatasetProfiler()
    return profiler.profile(dataset)


def assess(
    dataset: str | Path | pd.DataFrame,
) -> AssessmentReport:
    """
    Assess the quality of a dataset.

    Args:
        dataset: A pandas DataFrame or path to a supported dataset file.

    Returns:
        An AssessmentReport containing quality scores, validations, and
        recommendations.
    """
    engine = AssessmentEngine()
    return engine.assess(dataset)


def assess_ai_readiness(
    dataset: str | Path | pd.DataFrame,
) -> AIReadinessReport:
    """
    Assess whether a dataset is ready for AI-powered applications.

    Args:
        dataset: A pandas DataFrame or path to a supported dataset file.

    Returns:
        An AIReadinessReport with AI suitability metrics and recommendations.
    """
    engine = AIReadinessEngine()
    return engine.assess(dataset)


def fix(
    dataset: str | Path | pd.DataFrame,
    config: FixConfig | None = None,
) -> FixResult:
    """
    Automatically clean a dataset.

    Args:
        dataset: A pandas DataFrame or path to a supported dataset file.
        config: Optional configuration for the cleaning operation.

    Returns:
        A FixResult containing the cleaned DataFrame, before and after
        assessment reports, and applied fixes.
    """
    engine = FixEngine()
    return engine.fix(dataset, config)


def prepare(
    dataset: str | Path | pd.DataFrame,
) -> pd.DataFrame:
    """
    Prepare a dataset for downstream analytics or machine learning.

    Args:
        dataset: A pandas DataFrame or path to a supported dataset file.

    Returns:
        A prepared pandas DataFrame.
    """
    engine = PrepareEngine()
    return engine.prepare(dataset)


def analysis_ready(
    dataset: str | Path | pd.DataFrame,
    config: FixConfig | None = None,
) -> pd.DataFrame:
    """
    Clean and prepare a dataset for exploratory data analysis (EDA).

    Args:
        dataset: A pandas DataFrame or path to a supported dataset file.
        config: Optional configuration for the cleaning operation.

    Returns:
        A cleaned and prepared pandas DataFrame.
    """

    cleaned = fix(
        dataset,
        config=config,
    )

    engine = PrepareEngine()

    return engine.prepare(
        cleaned.dataset,
    )
