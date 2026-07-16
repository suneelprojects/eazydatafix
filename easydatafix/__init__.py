from .assessment.engine import AssessmentEngine
from .assessment.profiler import DatasetProfiler
from .console_report import Report
from .fix.engine import FixEngine
from .models.fix_config import FixConfig
from .prepare.engine import PrepareEngine

__version__ = "0.1.3"


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


def analysis_ready(
    dataset,
    config: FixConfig | None = None,
):
    """
    Clean and prepare a dataset for exploratory
    data analysis (EDA).
    """

    cleaned = fix(
        dataset,
        config=config,
    )

    engine = PrepareEngine()

    return engine.prepare(
        cleaned.dataframe,
    )
