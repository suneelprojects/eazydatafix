from dataclasses import dataclass
from typing import TYPE_CHECKING

from eazydatafix.assessment.checks.completeness import CompletenessResult
from eazydatafix.assessment.checks.uniqueness import UniquenessResult
from eazydatafix.models.dataset_info import DatasetInfo
from eazydatafix.models.quality_dimensions import QualityDimensions
from eazydatafix.models.quality_score import QualityScore
from eazydatafix.models.recommendation import Recommendation
from eazydatafix.models.validation_result import ValidationResult

if TYPE_CHECKING:
    from eazydatafix.console_report import Report


@dataclass(slots=True)
class AssessmentReport:
    """
    Represents the overall assessment of a dataset.
    """

    dataset_info: DatasetInfo

    completeness: CompletenessResult
    uniqueness: UniquenessResult

    quality: QualityScore
    quality_dimensions: QualityDimensions

    recommendations: list[Recommendation]
    validations: list[ValidationResult]

    def summary(self) -> None:
        """
        Display a human-readable assessment summary in the console.

        Returns:
            None.
        """
        from eazydatafix.console_report import Report

        Report(self).summary()

    def to_html(
        self,
        output_file: str = "report.html",
    ) -> None:
        """
        Export the assessment report as HTML.

        Args:
            output_file: Destination path for the HTML report.

        Returns:
            None.
        """
        from eazydatafix.reporting.html_report import HtmlReport

        HtmlReport.export(
            self,
            output_file,
        )

    def to_json(
        self,
        output_file: str = "report.json",
    ) -> None:
        """
        Export the assessment report as JSON.

        Args:
            output_file: Destination path for the JSON report.

        Returns:
            None.
        """
        from eazydatafix.reporting.json_report import JsonReport

        JsonReport.export(
            self,
            output_file,
        )

    def to_markdown(
        self,
        output_file: str = "report.md",
    ) -> None:
        """
        Export the assessment report as Markdown.

        Args:
            output_file: Destination path for the Markdown report.

        Returns:
            None.
        """
        from eazydatafix.reporting.markdown_report import MarkdownReport

        MarkdownReport.export(
            self,
            output_file,
        )

    def to_csv(
        self,
        output_file: str = "report.csv",
    ) -> None:
        """
        Export the assessment report as CSV.

        Args:
            output_file: Destination path for the CSV report.

        Returns:
            None.
        """
        from eazydatafix.reporting.csv_report import CsvReport

        CsvReport.export(
            self,
            output_file,
        )

    def to_excel(
        self,
        output_file: str = "report.xlsx",
    ) -> None:
        """
        Export the assessment report as an Excel workbook.

        Args:
            output_file: Destination path for the Excel report.

        Returns:
            None.
        """
        from eazydatafix.reporting.excel_report import ExcelReport

        ExcelReport.export(
            self,
            output_file,
        )

    def to_pdf(
        self,
        output_file: str = "report.pdf",
    ) -> None:
        """
        Export the assessment report as PDF.

        Args:
            output_file: Destination path for the PDF report.

        Returns:
            None.
        """
        from eazydatafix.reporting.pdf_report import PdfReport

        PdfReport.export(
            self,
            output_file,
        )
