from dataclasses import dataclass, field

from eazydatafix.models.fix_config import FixConfig
from eazydatafix.models.prepare_config import PrepareConfig


@dataclass(slots=True)
class AnalysisReadyConfig:
    """Configure the deterministic Analysis Ready workflow."""

    fix_config: FixConfig = field(default_factory=FixConfig)
    prepare_config: PrepareConfig = field(default_factory=PrepareConfig)
    nearly_empty_threshold: float = 0.80
    minimum_readiness_score: float = 80.0

    def __post_init__(self) -> None:
        """Validate composed workflow configuration and score thresholds."""
        if not isinstance(self.fix_config, FixConfig):
            raise TypeError("fix_config must be a FixConfig instance.")
        if not isinstance(self.prepare_config, PrepareConfig):
            raise TypeError("prepare_config must be a PrepareConfig instance.")
        if not isinstance(self.nearly_empty_threshold, float) or not (
            0.0 < self.nearly_empty_threshold <= 1.0
        ):
            raise ValueError("nearly_empty_threshold must be a float between 0 and 1.")
        if not isinstance(self.minimum_readiness_score, float) or not (
            0.0 <= self.minimum_readiness_score <= 100.0
        ):
            raise ValueError("minimum_readiness_score must be a float between 0 and 100.")
