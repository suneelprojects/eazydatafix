from dataclasses import dataclass


@dataclass(slots=True)
class QualityDimensions:
    """
    Represents individual data quality dimensions.
    """

    completeness: float
    uniqueness: float
    validity: float
    consistency: float
    accuracy: float
    timeliness: float

    @property
    def overall(self) -> float:
        return round(
            (
                self.completeness
                + self.uniqueness
                + self.validity
                + self.consistency
                + self.accuracy
                + self.timeliness
            )
            / 6,
            2,
        )
