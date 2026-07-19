import csv
from pathlib import Path

from eazydatafix.models.assessment_report import AssessmentReport


class CsvReport:
    """
    Exports an AssessmentReport as a CSV report.
    """

    @staticmethod
    def export(
        report: AssessmentReport,
        output_file: str,
    ) -> None:

        with Path(output_file).open(
            "w",
            newline="",
            encoding="utf-8",
        ) as csv_file:

            writer = csv.writer(csv_file)

            writer.writerow(
                [
                    "Section",
                    "Property",
                    "Value",
                ]
            )

            # Dataset Information

            writer.writerow(
                [
                    "Dataset",
                    "File Name",
                    report.dataset_info.file_name,
                ]
            )

            writer.writerow(
                [
                    "Dataset",
                    "Rows",
                    report.dataset_info.rows,
                ]
            )

            writer.writerow(
                [
                    "Dataset",
                    "Columns",
                    report.dataset_info.columns,
                ]
            )

            writer.writerow(
                [
                    "Dataset",
                    "Memory Usage",
                    f"{report.dataset_info.memory_usage_bytes:,} Bytes",
                ]
            )

            # Overall Quality

            writer.writerow(
                [
                    "Quality",
                    "Score",
                    report.quality.score,
                ]
            )

            writer.writerow(
                [
                    "Quality",
                    "Grade",
                    report.quality.grade,
                ]
            )

            # Quality Dimensions

            writer.writerow(
                [
                    "Dimension",
                    "Completeness",
                    report.quality_dimensions.completeness,
                ]
            )

            writer.writerow(
                [
                    "Dimension",
                    "Uniqueness",
                    report.quality_dimensions.uniqueness,
                ]
            )

            writer.writerow(
                [
                    "Dimension",
                    "Validity",
                    report.quality_dimensions.validity,
                ]
            )

            writer.writerow(
                [
                    "Dimension",
                    "Consistency",
                    report.quality_dimensions.consistency,
                ]
            )

            writer.writerow(
                [
                    "Dimension",
                    "Accuracy",
                    report.quality_dimensions.accuracy,
                ]
            )

            writer.writerow(
                [
                    "Dimension",
                    "Timeliness",
                    report.quality_dimensions.timeliness,
                ]
            )

            # Recommendations

            for recommendation in report.recommendations:

                writer.writerow(
                    [
                        "Recommendation",
                        recommendation.priority,
                        recommendation.title,
                    ]
                )

            # Validations

            for validation in report.validations:

                writer.writerow(
                    [
                        "Validation",
                        validation.rule,
                        validation.column,
                        "PASS" if validation.passed else "FAIL",
                    ]
                )
