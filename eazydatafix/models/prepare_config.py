from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PrepareConfig:
    """Controls deterministic preparation and feature-readiness transformations."""

    numeric_conversion_threshold: float = 0.95
    date_parsing_threshold: float = 0.80
    remove_duplicates: bool = False
    outlier_action: str = "none"
    normalize_text: bool = False
    categorize_low_cardinality: bool = True
    derive_date_parts: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Validate deterministic thresholds and supported actions."""
        for name, value in (
            ("numeric_conversion_threshold", self.numeric_conversion_threshold),
            ("date_parsing_threshold", self.date_parsing_threshold),
        ):
            if not isinstance(value, float) or not 0.0 < value <= 1.0:
                raise ValueError(f"{name} must be a float between 0 and 1.")
        if self.outlier_action not in {"none", "flag", "cap", "drop"}:
            raise ValueError("outlier_action must be one of: none, flag, cap, drop.")
        supported_date_parts = {
            "year",
            "quarter",
            "month",
            "month_name",
            "week",
            "day",
            "day_of_week",
            "is_weekend",
        }
        if not isinstance(self.derive_date_parts, tuple) or any(
            part not in supported_date_parts for part in self.derive_date_parts
        ):
            raise ValueError(
                "derive_date_parts must be a tuple containing only: "
                + ", ".join(sorted(supported_date_parts))
                + "."
            )
