from dataclasses import dataclass, field

from eazydatafix.models.analysis_ready_config import AnalysisReadyConfig
from eazydatafix.models.fix_config import FixConfig


def _default_analysis_ready_config() -> AnalysisReadyConfig:
    """Keep missing values available for training-only imputation."""
    return AnalysisReadyConfig(
        fix_config=FixConfig(missing_value_strategy="keep"),
    )


@dataclass(slots=True)
class MLReadyConfig:
    """Configure leakage-safe preparation for supervised machine learning."""

    analysis_ready_config: AnalysisReadyConfig = field(
        default_factory=_default_analysis_ready_config
    )
    test_size: float = 0.20
    random_state: int = 42
    shuffle: bool = True
    numeric_imputation: str = "median"
    categorical_imputation: str = "most_frequent"
    categorical_fill_value: str = "__missing__"
    categorical_encoding: str = "one_hot"
    scaling: str = "none"
    high_cardinality_threshold: float = 0.50
    max_categories: int = 50
    leakage_correlation_threshold: float = 0.995
    class_imbalance_threshold: float = 0.20
    drop_identifiers: bool = True
    drop_constant_features: bool = True
    drop_high_cardinality: bool = True
    drop_leakage_features: bool = True
    minimum_readiness_score: float = 80.0

    def __post_init__(self) -> None:
        """Validate split, transformation, and diagnostic controls."""
        if not isinstance(self.analysis_ready_config, AnalysisReadyConfig):
            raise TypeError("analysis_ready_config must be an AnalysisReadyConfig instance.")
        if not isinstance(self.test_size, float) or not 0.0 < self.test_size < 1.0:
            raise ValueError("test_size must be a float between 0 and 1.")
        if not isinstance(self.random_state, int) or isinstance(self.random_state, bool):
            raise TypeError("random_state must be an integer.")
        if not isinstance(self.shuffle, bool):
            raise TypeError("shuffle must be a boolean.")
        if self.numeric_imputation not in {"median", "mean", "zero"}:
            raise ValueError("numeric_imputation must be one of: median, mean, zero.")
        if self.categorical_imputation not in {"most_frequent", "constant"}:
            raise ValueError("categorical_imputation must be one of: most_frequent, constant.")
        if not isinstance(self.categorical_fill_value, str):
            raise TypeError("categorical_fill_value must be a string.")
        if self.categorical_encoding not in {"one_hot", "ordinal"}:
            raise ValueError("categorical_encoding must be one of: one_hot, ordinal.")
        if self.scaling not in {"none", "standard", "minmax"}:
            raise ValueError("scaling must be one of: none, standard, minmax.")
        for name, value in (
            ("high_cardinality_threshold", self.high_cardinality_threshold),
            ("leakage_correlation_threshold", self.leakage_correlation_threshold),
            ("class_imbalance_threshold", self.class_imbalance_threshold),
        ):
            if not isinstance(value, float) or not 0.0 < value <= 1.0:
                raise ValueError(f"{name} must be a float between 0 and 1.")
        if not isinstance(self.max_categories, int) or isinstance(self.max_categories, bool):
            raise TypeError("max_categories must be an integer.")
        if self.max_categories < 2:
            raise ValueError("max_categories must be at least 2.")
        for name in (
            "drop_identifiers",
            "drop_constant_features",
            "drop_high_cardinality",
            "drop_leakage_features",
        ):
            if not isinstance(getattr(self, name), bool):
                raise TypeError(f"{name} must be a boolean.")
        if not isinstance(self.minimum_readiness_score, float) or not (
            0.0 <= self.minimum_readiness_score <= 100.0
        ):
            raise ValueError("minimum_readiness_score must be a float between 0 and 100.")

        fix_config = self.analysis_ready_config.fix_config
        if fix_config.dry_run:
            raise ValueError("ML Ready does not accept a dry-run FixConfig.")
        if fix_config.missing_value_strategy != "keep" or any(
            rule.missing_value_strategy not in {None, "keep"}
            for rule in fix_config.column_rules.values()
        ):
            raise ValueError(
                "ML Ready requires missing_value_strategy='keep' so imputation is fitted "
                "only on training data."
            )
        if self.analysis_ready_config.prepare_config.outlier_action != "none":
            raise ValueError(
                "ML Ready requires PrepareConfig.outlier_action='none'; fit outlier "
                "handling after the train/test split."
            )
