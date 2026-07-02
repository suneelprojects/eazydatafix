from .assessment.engine import AssessmentEngine
from .assessment.profiler import DatasetProfiler

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
