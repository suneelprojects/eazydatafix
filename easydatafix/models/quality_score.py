from dataclasses import dataclass


@dataclass(slots=True)
class QualityScore:
    """
    Represents the overall quality score of a dataset.
    """

    score: float
    grade: str
