import json
from dataclasses import asdict
from pathlib import Path

from eazydatafix.models.assessment_report import AssessmentReport


class JsonReport:
    """
    Exports an AssessmentReport to JSON.
    """

    @staticmethod
    def export(
        report: AssessmentReport,
        output_file: str,
    ) -> None:

        data = {
            "dataset": asdict(report.dataset_info),

            "quality": {
                "score": report.quality.score,
                "grade": report.quality.grade,
            },

            "dimensions": {
                "completeness": report.quality_dimensions.completeness,
                "uniqueness": report.quality_dimensions.uniqueness,
                "validity": report.quality_dimensions.validity,
                "consistency": report.quality_dimensions.consistency,
                "accuracy": report.quality_dimensions.accuracy,
                "timeliness": report.quality_dimensions.timeliness,
                "overall": report.quality_dimensions.overall,
            },

            "recommendations": [
                {
                    "title": recommendation.title,
                    "description": recommendation.description,
                    "priority": recommendation.priority,
                    "category": recommendation.category,
                    "auto_fix_available": recommendation.auto_fix_available,
                }
                for recommendation in report.recommendations
            ],

            "validations": [
                {
                    "rule": validation.rule,
                    "column": validation.column,
                    "passed": validation.passed,
                    "message": validation.message,
                }
                for validation in report.validations
            ],
        }

        Path(output_file).write_text(
            json.dumps(
                data,
                indent=4,
            ),
            encoding="utf-8",
        )
