from dataclasses import dataclass

from easydatafix.models.assessment_report import AssessmentReport


@dataclass(slots=True)
class ComparisonReport:
    """
    Represents a comparison between two assessment reports.
    """

    before: AssessmentReport

    after: AssessmentReport

    @property
    def score_difference(self) -> float:
        return round(
            self.after.quality.score -
            self.before.quality.score,
            2,
        )

    @property
    def recommendation_difference(self) -> int:
        return (
            len(self.before.recommendations)
            -
            len(self.after.recommendations)
        )

    def summary(self) -> None:
        """
        Display the comparison summary.

        Implementation will be added in the next step.
        """
        raise NotImplementedError
