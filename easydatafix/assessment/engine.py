from pathlib import Path

import pandas as pd

from easydatafix.assessment.checks.accuracy.engine import AccuracyEngine
from easydatafix.assessment.checks.completeness import CompletenessCheck
from easydatafix.assessment.checks.consistency.engine import ConsistencyEngine
from easydatafix.assessment.checks.timeliness.engine import TimelinessEngine
from easydatafix.assessment.checks.uniqueness import UniquenessCheck
from easydatafix.contracts.check import Check
from easydatafix.core.dataset_loader import DatasetLoader
from easydatafix.core.score_calculator import ScoreCalculator
from easydatafix.models.assessment_report import AssessmentReport
from easydatafix.models.dataset_info import DatasetInfo
from easydatafix.models.quality_dimensions import QualityDimensions
from easydatafix.recommendations.engine import RecommendationEngine
from easydatafix.validation.engine import ValidationEngine


class AssessmentEngine:
    """
    Coordinates all assessment checks.
    """

    def __init__(self) -> None:

        self._checks: list[Check] = [
            CompletenessCheck(),
            UniquenessCheck(),
        ]

        self._validation_engine = ValidationEngine()
        self._consistency_engine = ConsistencyEngine()
        self._accuracy_engine = AccuracyEngine()
        self._timeliness_engine = TimelinessEngine()

    def assess(
        self,
        dataset,
    ) -> AssessmentReport:

        df = DatasetLoader.load(dataset)

        file_name = (
            Path(dataset).name
            if isinstance(dataset, (str, Path))
            else "DataFrame"
        )

        return self.assess_dataframe(
            df=df,
            file_name=file_name,
        )

    def assess_dataframe(
        self,
        df: pd.DataFrame,
        file_name: str = "DataFrame",
    ) -> AssessmentReport:

        dataset_info = DatasetInfo(
            file_name=file_name,
            rows=len(df),
            columns=len(df.columns),
            memory_usage_bytes=int(
                df.memory_usage(deep=True).sum()
            ),
        )

        results = {}

        for check in self._checks:
            results[check.name] = check.evaluate(df)

        completeness = results["Completeness"]
        uniqueness = results["Uniqueness"]

        validations = []

        validation_results = self._validation_engine.validate(df)
        consistency_results = self._consistency_engine.evaluate(df)
        accuracy_results = self._accuracy_engine.evaluate(df)
        timeliness_results = self._timeliness_engine.evaluate(df)

        validations.extend(validation_results)
        validations.extend(consistency_results)
        validations.extend(accuracy_results)
        validations.extend(timeliness_results)

        def percentage(items: list) -> float:

            if not items:
                return 100.0

            passed = sum(
                1
                for item in items
                if item.passed
            )

            return round(
                (passed / len(items)) * 100,
                2,
            )

        quality_dimensions = QualityDimensions(
            completeness=completeness.completeness_score,
            uniqueness=uniqueness.uniqueness_score,
            validity=percentage(validation_results),
            consistency=percentage(consistency_results),
            accuracy=percentage(accuracy_results),
            timeliness=percentage(timeliness_results),
        )

        quality = ScoreCalculator().calculate(
            completeness_score=completeness.completeness_score,
            uniqueness_score=uniqueness.uniqueness_score,
            validations=validations,
        )

        report = AssessmentReport(
            dataset_info=dataset_info,
            completeness=completeness,
            uniqueness=uniqueness,
            quality=quality,
            quality_dimensions=quality_dimensions,
            recommendations=[],
            validations=validations,
        )

        report.recommendations = (
            RecommendationEngine().generate(report)
        )

        return report
