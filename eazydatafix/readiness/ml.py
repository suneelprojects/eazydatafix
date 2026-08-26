from pathlib import Path

import numpy as np
import pandas as pd

from eazydatafix.core.column_profiler import ColumnProfiler
from eazydatafix.fix.column_normalizer import ColumnNormalizer
from eazydatafix.models.ml_ready_config import MLReadyConfig
from eazydatafix.models.ml_ready_result import (
    MLPreprocessingArtifact,
    MLReadyIssue,
    MLReadyResult,
)
from eazydatafix.readiness.analysis import AnalysisReadyEngine


class MLReadyEngine:
    """Create leakage-safe supervised-learning inputs without training a model."""

    def __init__(self) -> None:
        self._analysis_ready_engine = AnalysisReadyEngine()

    def run(
        self,
        dataset: str | Path | pd.DataFrame,
        *,
        target: str,
        config: MLReadyConfig | None = None,
    ) -> MLReadyResult:
        """Split data, fit preprocessing on training rows, and transform both splits."""
        if not isinstance(target, str) or not target.strip():
            raise ValueError("target must be a non-empty column name.")
        config = config or MLReadyConfig()
        analysis_result = self._analysis_ready_engine.run(
            dataset,
            config.analysis_ready_config,
        )
        candidate = analysis_result.dataset.copy()
        resolved_target = self._resolve_target(target, candidate)

        issues: list[MLReadyIssue] = []
        changes = list(analysis_result.changes)
        missing_target_rows = int(candidate[resolved_target].isna().sum())
        if missing_target_rows:
            candidate = candidate.dropna(subset=[resolved_target]).copy()
            issues.append(
                MLReadyIssue(
                    code="missing_target",
                    column=resolved_target,
                    severity="warning",
                    message=(
                        f"Dropped {missing_target_rows} row(s) with a missing supervised target."
                    ),
                    action="Rows with unknown labels were excluded before splitting.",
                )
            )
            changes.append(
                f"Dropped {missing_target_rows} row(s) with missing target '{resolved_target}'."
            )
        candidate = candidate.reset_index(drop=True)
        if len(candidate) < 2:
            raise ValueError("ML Ready requires at least two rows with a non-missing target.")

        train_indices, test_indices = self._split_indices(len(candidate), config)
        train = candidate.iloc[train_indices].reset_index(drop=True)
        test = candidate.iloc[test_indices].reset_index(drop=True)
        X_train_raw = train.drop(columns=[resolved_target])
        X_test_raw = test.drop(columns=[resolved_target])
        y_train = train[resolved_target].reset_index(drop=True)
        y_test = test[resolved_target].reset_index(drop=True)

        dropped_features, feature_issues = self._diagnose_features(
            X_train_raw,
            y_train,
            resolved_target,
            config,
        )
        issues.extend(feature_issues)
        issues.extend(self._diagnose_target(y_train, resolved_target, config))

        artifact = self._fit_artifact(X_train_raw, dropped_features, config)
        X_train = artifact.transform(X_train_raw)
        X_test = artifact.transform(X_test_raw)
        issues.extend(self._unknown_category_issues(X_test_raw, artifact))

        if X_train.empty:
            raise ValueError("No usable ML features remain after readiness diagnostics.")
        if X_train.isna().any().any() or X_test.isna().any().any():
            issues.append(
                MLReadyIssue(
                    code="unresolved_missing_features",
                    column="*",
                    severity="error",
                    message="Missing values remain after fitted preprocessing.",
                    action="Review imputation configuration and unsupported input values.",
                )
            )

        changes.append(
            f"Split {len(candidate)} row(s) into {len(train)} training and {len(test)} test rows."
        )
        if dropped_features:
            changes.append(
                "Excluded unsafe or unusable features: "
                + ", ".join(f"{column} ({reason})" for column, reason in dropped_features.items())
                + "."
            )
        changes.append("Fitted imputation, encoding, and scaling parameters on training rows only.")
        changes.append(
            f"Produced {len(artifact.feature_names_out)} numeric model-input feature(s)."
        )

        warnings = list(
            dict.fromkeys([*analysis_result.warnings, *(issue.message for issue in issues)])
        )
        readiness_score = self._readiness_score(issues)

        return MLReadyResult(
            target=resolved_target,
            X_train=X_train,
            X_test=X_test,
            y_train=y_train,
            y_test=y_test,
            artifact=artifact,
            config=config,
            analysis_ready_result=analysis_result,
            issues=issues,
            changes=changes,
            warnings=warnings,
            readiness_score=readiness_score,
        )

    @staticmethod
    def _resolve_target(target: str, dataset: pd.DataFrame) -> str:
        """Resolve an exact or normalized target name after Analysis Ready cleaning."""
        if target in dataset.columns:
            return target
        normalized = ColumnNormalizer.normalize_name(target)
        if normalized in dataset.columns:
            return normalized
        raise ValueError(
            f"Target column '{target}' was not found after Analysis Ready normalization."
        )

    @staticmethod
    def _split_indices(size: int, config: MLReadyConfig) -> tuple[np.ndarray, np.ndarray]:
        """Return deterministic train and test row indices."""
        test_rows = min(max(1, int(round(size * config.test_size))), size - 1)
        indices = np.arange(size)
        if config.shuffle:
            indices = np.random.default_rng(config.random_state).permutation(indices)
            test_indices = np.sort(indices[:test_rows])
            train_indices = np.sort(indices[test_rows:])
        else:
            train_indices = indices[:-test_rows]
            test_indices = indices[-test_rows:]
        return train_indices, test_indices

    def _diagnose_features(
        self,
        features: pd.DataFrame,
        target: pd.Series,
        target_name: str,
        config: MLReadyConfig,
    ) -> tuple[dict[str, str], list[MLReadyIssue]]:
        """Detect unsafe or low-value features using training rows only."""
        dropped: dict[str, str] = {}
        issues: list[MLReadyIssue] = []

        for column in features.columns:
            series = features[column]
            semantic_type = ColumnProfiler.detect(column, series)
            reason: str | None = None
            code: str | None = None
            configured_drop = False

            if semantic_type in {"IDENTIFIER", "EMAIL", "PHONE"}:
                reason = "identifier"
                code = "identifier_feature"
                configured_drop = config.drop_identifiers
            elif series.nunique(dropna=True) <= 1:
                reason = "constant"
                code = "constant_feature"
                configured_drop = config.drop_constant_features
            elif self._is_leakage_feature(column, series, target, target_name, config):
                reason = "potential target leakage"
                code = "leakage_risk"
                configured_drop = config.drop_leakage_features
            elif pd.api.types.is_datetime64_any_dtype(series):
                reason = "unsupported datetime feature"
                code = "unsupported_feature"
                configured_drop = True
            elif self._is_high_cardinality(series, config):
                reason = "high cardinality"
                code = "high_cardinality"
                configured_drop = config.drop_high_cardinality
            elif not self._is_supported_feature(series):
                reason = "unsupported feature dtype"
                code = "unsupported_feature"
                configured_drop = True

            if reason is None or code is None:
                continue
            if configured_drop:
                dropped[column] = reason
            issues.append(
                MLReadyIssue(
                    code=code,
                    column=column,
                    severity=(
                        "error" if code == "leakage_risk" and not configured_drop else "warning"
                    ),
                    message=f"Feature '{column}' was identified as {reason}.",
                    action=(
                        "Excluded before fitting preprocessing."
                        if configured_drop
                        else "Retained by configuration; review before model training."
                    ),
                )
            )

        return dropped, issues

    @staticmethod
    def _is_high_cardinality(series: pd.Series, config: MLReadyConfig) -> bool:
        """Return whether a categorical feature exceeds configured cardinality limits."""
        if pd.api.types.is_numeric_dtype(series) or pd.api.types.is_bool_dtype(series):
            return False
        unique = int(series.nunique(dropna=True))
        ratio = unique / max(int(series.notna().sum()), 1)
        return unique > config.max_categories or ratio >= config.high_cardinality_threshold

    @staticmethod
    def _is_leakage_feature(
        column: str,
        series: pd.Series,
        target: pd.Series,
        target_name: str,
        config: MLReadyConfig,
    ) -> bool:
        """Detect direct copies, target-derived names, and near-perfect correlation."""
        column_name = ColumnNormalizer.normalize_name(column)
        target_derived_name = bool(
            column_name.startswith(f"{target_name}_")
            or column_name.endswith(f"_{target_name}")
            or f"_{target_name}_" in column_name
            or column_name in {"label", "outcome", "target"}
        )
        if target_derived_name:
            return True

        comparable_feature = series.astype("string").fillna("<missing>")
        comparable_target = target.astype("string").fillna("<missing>")
        if comparable_feature.equals(comparable_target):
            return True

        if pd.api.types.is_numeric_dtype(series) and pd.api.types.is_numeric_dtype(target):
            paired = pd.concat(
                [
                    pd.to_numeric(series, errors="coerce"),
                    pd.to_numeric(target, errors="coerce"),
                ],
                axis=1,
            ).dropna()
            if (
                len(paired) >= 3
                and paired.iloc[:, 0].nunique() > 1
                and paired.iloc[:, 1].nunique() > 1
            ):
                correlation = paired.iloc[:, 0].corr(paired.iloc[:, 1])
                return bool(
                    pd.notna(correlation)
                    and abs(float(correlation)) >= config.leakage_correlation_threshold
                )
        return False

    @staticmethod
    def _is_supported_feature(series: pd.Series) -> bool:
        """Return whether the core artifact can transform this pandas dtype."""
        return bool(
            pd.api.types.is_numeric_dtype(series)
            or pd.api.types.is_bool_dtype(series)
            or pd.api.types.is_object_dtype(series)
            or pd.api.types.is_string_dtype(series)
            or isinstance(series.dtype, pd.CategoricalDtype)
        )

    def _fit_artifact(
        self,
        features: pd.DataFrame,
        dropped_features: dict[str, str],
        config: MLReadyConfig,
    ) -> MLPreprocessingArtifact:
        """Fit imputation, encoding, and scaling using training features only."""
        numeric_features: list[str] = []
        categorical_features: list[str] = []
        numeric_fill_values: dict[str, float] = {}
        categorical_fill_values: dict[str, str] = {}
        categories: dict[str, tuple[str, ...]] = {}
        encoded_feature_names: dict[str, tuple[str, ...]] = {}
        scale_parameters: dict[str, dict[str, float]] = {}
        output_features: list[str] = []

        for column in features.columns:
            if column in dropped_features:
                continue
            series = features[column]
            if pd.api.types.is_numeric_dtype(series) or pd.api.types.is_bool_dtype(series):
                numeric_features.append(column)
                numeric = pd.to_numeric(series, errors="coerce").astype("float64")
                fill_value = self._numeric_fill_value(numeric, config.numeric_imputation)
                numeric_fill_values[column] = fill_value
                fitted = numeric.fillna(fill_value)
                scale_parameters[column] = self._scale_parameters(fitted, config.scaling)
                output_features.append(column)
                continue

            categorical_features.append(column)
            values = series.astype("string")
            fill_value = self._categorical_fill_value(values, config)
            categorical_fill_values[column] = fill_value
            fitted = values.fillna(fill_value)
            learned_categories = tuple(sorted(str(value) for value in fitted.unique()))
            categories[column] = learned_categories
            if config.categorical_encoding == "ordinal":
                encoded_feature_names[column] = (column,)
                output_features.append(column)
            else:
                names = tuple(
                    MLPreprocessingArtifact.encoded_name(column, category, index)
                    for index, category in enumerate(learned_categories)
                )
                encoded_feature_names[column] = names
                output_features.extend(names)

        return MLPreprocessingArtifact(
            input_features=tuple(str(column) for column in features.columns),
            numeric_features=tuple(numeric_features),
            categorical_features=tuple(categorical_features),
            dropped_features=dropped_features,
            numeric_fill_values=numeric_fill_values,
            categorical_fill_values=categorical_fill_values,
            categories=categories,
            encoded_feature_names=encoded_feature_names,
            scale_parameters=scale_parameters,
            categorical_encoding=config.categorical_encoding,
            scaling=config.scaling,
            feature_names_out=tuple(output_features),
        )

    @staticmethod
    def _numeric_fill_value(series: pd.Series, strategy: str) -> float:
        """Return one training-fitted numeric imputation value."""
        if strategy == "zero" or series.dropna().empty:
            return 0.0
        if strategy == "mean":
            return float(series.mean())
        return float(series.median())

    @staticmethod
    def _categorical_fill_value(series: pd.Series, config: MLReadyConfig) -> str:
        """Return one training-fitted categorical imputation value."""
        if config.categorical_imputation == "constant":
            return config.categorical_fill_value
        mode = series.dropna().mode()
        return str(mode.iloc[0]) if not mode.empty else config.categorical_fill_value

    @staticmethod
    def _scale_parameters(series: pd.Series, scaling: str) -> dict[str, float]:
        """Return training-fitted numeric scaling parameters."""
        if scaling == "standard":
            scale = float(series.std(ddof=0))
            return {"mean": float(series.mean()), "scale": scale if scale else 1.0}
        if scaling == "minmax":
            minimum = float(series.min())
            value_range = float(series.max() - minimum)
            return {"minimum": minimum, "range": value_range if value_range else 1.0}
        return {}

    @staticmethod
    def _unknown_category_issues(
        test_features: pd.DataFrame,
        artifact: MLPreprocessingArtifact,
    ) -> list[MLReadyIssue]:
        """Report test categories that were not observed during training."""
        issues: list[MLReadyIssue] = []
        for column in artifact.categorical_features:
            values = (
                test_features[column]
                .astype("string")
                .fillna(artifact.categorical_fill_values[column])
            )
            unknown = int((~values.isin(artifact.categories[column])).sum())
            if unknown:
                issues.append(
                    MLReadyIssue(
                        code="unknown_category",
                        column=column,
                        severity="warning",
                        message=(
                            f"Test feature '{column}' contains {unknown} unseen category value(s)."
                        ),
                        action=(
                            "Encoded as all-zero one-hot values or -1 ordinal values without "
                            "refitting."
                        ),
                    )
                )
        return issues

    @staticmethod
    def _diagnose_target(
        target: pd.Series,
        target_name: str,
        config: MLReadyConfig,
    ) -> list[MLReadyIssue]:
        """Detect single-class and materially imbalanced classification targets."""
        counts = target.value_counts(dropna=True)
        if len(counts) <= 1:
            return [
                MLReadyIssue(
                    code="single_class_target",
                    column=target_name,
                    severity="error",
                    message=f"Target '{target_name}' has fewer than two training classes.",
                    action="Provide training rows containing at least two target classes.",
                )
            ]

        classification_like = bool(
            pd.api.types.is_bool_dtype(target)
            or isinstance(target.dtype, pd.CategoricalDtype)
            or pd.api.types.is_object_dtype(target)
            or pd.api.types.is_string_dtype(target)
            or (len(counts) <= 20 and len(counts) / max(len(target), 1) <= 0.20)
        )
        if not classification_like:
            return []
        ratio = float(counts.min() / counts.max())
        if ratio >= config.class_imbalance_threshold:
            return []
        return [
            MLReadyIssue(
                code="class_imbalance",
                column=target_name,
                severity="warning",
                message=(
                    f"Target '{target_name}' has a minority-to-majority ratio of {ratio:.1%}."
                ),
                action="Use appropriate resampling or class weighting during model training.",
            )
        ]

    @staticmethod
    def _readiness_score(issues: list[MLReadyIssue]) -> float:
        """Calculate a transparent readiness score from unresolved diagnostic severity."""
        warnings = sum(1 for issue in issues if issue.severity == "warning")
        errors = sum(1 for issue in issues if issue.severity == "error")
        return round(max(0.0, 100.0 - min(warnings * 3.0, 30.0) - errors * 25.0), 2)
