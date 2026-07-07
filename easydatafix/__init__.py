from .assessment.engine import AssessmentEngine
from .assessment.profiler import DatasetProfiler
from .console_report import Report
from .fix.engine import FixEngine
from .models.fix_config import FixConfig

__version__ = "0.1.2"


def profile(dataset):
    """
    Generate a structural profile for a dataset.
    """
    profiler = DatasetProfiler()
    return profiler.profile(dataset)


def assess(dataset):
    """
    Assess the quality of a dataset.
    """
    engine = AssessmentEngine()
    return engine.assess(dataset)


def fix(dataset, config: FixConfig | None = None):
    """
    Automatically clean a dataset.
    """
    engine = FixEngine()
    return engine.fix(dataset, config)
