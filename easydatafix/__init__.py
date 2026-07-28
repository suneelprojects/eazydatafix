from pathlib import Path

import pandas as pd

from .assessment.eda import EDAEngine
from .assessment.engine import AssessmentEngine
from .assessment.profiler import DatasetProfiler
from .fix.engine import FixEngine
from .models.eda_result import EDAResult

__version__ = "0.1.0"


def profile(file_path: str):
    """
    Generate a structural profile for a dataset.
    """
    profiler = DatasetProfiler()
    return profiler.profile(file_path)


def assess(file_path: str):
    """
    Assess the quality of a dataset.
    """
    engine = AssessmentEngine()
    return engine.assess(file_path)


def fix(file_path: str, strategy: str = "smart"):
    """
    Automatically clean a dataset.
    """
    engine = FixEngine()
    return engine.fix(file_path, strategy)


def eda(
    dataset: str | Path | pd.DataFrame,
) -> EDAResult:
    """
    Generate a deterministic exploratory data analysis result.

    Args:
        dataset: A pandas DataFrame or supported dataset file path.

    Returns:
        An EDAResult containing descriptive analysis and recommendations.
    """
    engine = EDAEngine()
    return engine.analyze(dataset)


__all__ = [
    "profile",
    "assess",
    "fix",
    "eda",
    "EDAEngine",
    "EDAResult",
]
