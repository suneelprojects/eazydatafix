from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ColumnCleaningRule:
    """Optional, deterministic cleaning overrides for one normalized column."""

    missing_value_strategy: str | None = None
    trim_whitespace: bool | None = None
    missing_markers: tuple[str, ...] | None = None

    def __post_init__(self) -> None:
        """Validate rule values without applying a transformation."""
        if self.missing_value_strategy is not None and not isinstance(
            self.missing_value_strategy, str
        ):
            raise TypeError("missing_value_strategy must be a string or None.")
        if self.trim_whitespace is not None and not isinstance(self.trim_whitespace, bool):
            raise TypeError("trim_whitespace must be a boolean or None.")
        if self.missing_markers is not None and any(
            not isinstance(marker, str) for marker in self.missing_markers
        ):
            raise TypeError("missing_markers must contain only strings.")
