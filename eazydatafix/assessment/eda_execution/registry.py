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


def default_handlers(
    *,
    correlation_threshold: float = 0.80,
    outlier_iqr_multiplier: float = 1.50,
    class_imbalance_threshold: float = 0.80,
) -> list[EDAAnalysisHandler]:
    """
    Build the deterministic handlers supported by the EDA executor.

    Args:
        correlation_threshold: Absolute correlation threshold from zero to one.
        outlier_iqr_multiplier: Positive multiplier applied to the IQR.
        class_imbalance_threshold: Dominant-class ratio from zero to one.

    Returns:
        Deterministic handlers in canonical execution order.
    """
    return [
        MissingValueAnalysisHandler(),
        DuplicateReviewHandler(),
        IdentifierExclusionHandler(),
        NumericDistributionAnalysisHandler(),
        OutlierAnalysisHandler(iqr_multiplier=outlier_iqr_multiplier),
        SkewnessAnalysisHandler(),
        CategoricalDistributionAnalysisHandler(),
        BooleanDistributionAnalysisHandler(),
        ClassImbalanceAnalysisHandler(
            threshold_percentage=class_imbalance_threshold * 100,
        ),
        CorrelationReviewHandler(threshold=correlation_threshold),
        DatetimeTrendAnalysisHandler(),
    ]
