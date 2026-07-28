from eazydatafix.assessment.eda_execution.base import EDAAnalysisHandler
from eazydatafix.assessment.eda_execution.categorical import (
    BooleanDistributionAnalysisHandler,
    CategoricalDistributionAnalysisHandler,
    ClassImbalanceAnalysisHandler,
)
from eazydatafix.assessment.eda_execution.datetime import (
    DatetimeTrendAnalysisHandler,
)
from eazydatafix.assessment.eda_execution.numeric import (
    CorrelationReviewHandler,
    NumericDistributionAnalysisHandler,
    OutlierAnalysisHandler,
    SkewnessAnalysisHandler,
)
from eazydatafix.assessment.eda_execution.quality import (
    DuplicateReviewHandler,
    IdentifierExclusionHandler,
    MissingValueAnalysisHandler,
)


def default_handlers() -> list[EDAAnalysisHandler]:
    """
    Build the deterministic handlers supported by the EDA executor.
    """
    return [
        MissingValueAnalysisHandler(),
        DuplicateReviewHandler(),
        IdentifierExclusionHandler(),
        NumericDistributionAnalysisHandler(),
        OutlierAnalysisHandler(),
        SkewnessAnalysisHandler(),
        CategoricalDistributionAnalysisHandler(),
        BooleanDistributionAnalysisHandler(),
        ClassImbalanceAnalysisHandler(),
        CorrelationReviewHandler(),
        DatetimeTrendAnalysisHandler(),
    ]
