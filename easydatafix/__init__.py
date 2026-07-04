from .assessment.engine import AssessmentEngine
from .assessment.profiler import DatasetProfiler
from .fix.engine import FixEngine
from .models.fix_config import FixConfig
from .report import Report

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


def fix(file_path: str, config: FixConfig | None = None):
    """
    Automatically clean a dataset.
    """
    engine = FixEngine()
    return engine.fix(file_path, config)
