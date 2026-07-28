import math
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AgenticEDAConfig:
    """
    Configures stable deterministic thresholds and orchestration features.

    Thresholds use ratios from zero to one, except ``outlier_iqr_multiplier``,
    which is the positive multiplier applied to the interquartile range.
    """

    correlation_threshold: float = 0.80
    outlier_iqr_multiplier: float = 1.50
    class_imbalance_threshold: float = 0.80
    enable_visualisation_recommendations: bool = True
    enable_unresolved_questions: bool = True
    max_recommendations_per_category: int = 10

    def __post_init__(self) -> None:
        """
        Validate deterministic orchestration settings.

        Raises:
            TypeError: If a setting has an invalid type.
            ValueError: If a threshold or limit falls outside its supported range.
        """
        self._validate_ratio("correlation_threshold", self.correlation_threshold)
        self._validate_ratio("class_imbalance_threshold", self.class_imbalance_threshold)

        if isinstance(self.outlier_iqr_multiplier, bool) or not isinstance(
            self.outlier_iqr_multiplier, (int, float)
        ):
            raise TypeError("outlier_iqr_multiplier must be a number.")

        if (
            not math.isfinite(float(self.outlier_iqr_multiplier))
            or self.outlier_iqr_multiplier <= 0
        ):
            raise ValueError("outlier_iqr_multiplier must be finite and greater than zero.")

        for name, value in (
            (
                "enable_visualisation_recommendations",
                self.enable_visualisation_recommendations,
            ),
            ("enable_unresolved_questions", self.enable_unresolved_questions),
        ):
            if not isinstance(value, bool):
                raise TypeError(f"{name} must be a bool.")

        if isinstance(self.max_recommendations_per_category, bool) or not isinstance(
            self.max_recommendations_per_category, int
        ):
            raise TypeError("max_recommendations_per_category must be an int.")

        if self.max_recommendations_per_category < 1:
            raise ValueError("max_recommendations_per_category must be at least 1.")

    @staticmethod
    def _validate_ratio(
        name: str,
        value: float,
    ) -> None:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError(f"{name} must be a number.")

        if not math.isfinite(float(value)) or not 0 < value <= 1:
            raise ValueError(f"{name} must be finite, greater than 0, and at most 1.")
