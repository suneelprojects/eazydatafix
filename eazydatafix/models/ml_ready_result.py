import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from eazydatafix.core.dataset_loader import DatasetLoader
from eazydatafix.models.analysis_ready_result import AnalysisReadyResult
from eazydatafix.models.ml_ready_config import MLReadyConfig


@dataclass(frozen=True, slots=True)
class MLReadyIssue:
    """Describe a feature or target condition relevant to ML preparation."""

    code: str
    column: str
    severity: str
    message: str
    action: str


@dataclass(slots=True)
class MLPreprocessingArtifact:
    """Store training-fitted preprocessing parameters for deterministic reuse."""

    input_features: tuple[str, ...]
    numeric_features: tuple[str, ...]
    categorical_features: tuple[str, ...]
    dropped_features: dict[str, str]
    numeric_fill_values: dict[str, float]
    categorical_fill_values: dict[str, str]
    categories: dict[str, tuple[str, ...]]
    encoded_feature_names: dict[str, tuple[str, ...]]
    scale_parameters: dict[str, dict[str, float]]
    categorical_encoding: str
    scaling: str
    feature_names_out: tuple[str, ...]
    artifact_format_version: int = 1

    def transform(self, dataset: str | Path | pd.DataFrame) -> pd.DataFrame:
        """Apply the fitted preprocessing parameters to Analysis Ready features."""
        df = DatasetLoader.load(dataset).copy()
        required = [*self.numeric_features, *self.categorical_features]
        missing = [column for column in required if column not in df.columns]
        if missing:
            raise ValueError("Dataset is missing required feature columns: " + ", ".join(missing))

        transformed: dict[str, pd.Series] = {}
        for column in self.input_features:
            if column in self.dropped_features:
                continue
            if column in self.numeric_features:
                values = pd.to_numeric(df[column], errors="coerce").astype("float64")
                values = values.fillna(self.numeric_fill_values[column])
                values = self._scale(column, values)
                transformed[column] = values
                continue
            if column in self.categorical_features:
                values = df[column].astype("string").fillna(self.categorical_fill_values[column])
                if self.categorical_encoding == "ordinal":
                    mapping = {
                        category: index for index, category in enumerate(self.categories[column])
                    }
                    transformed[column] = values.map(mapping).fillna(-1).astype("float64")
                    continue
                for category, output_column in zip(
                    self.categories[column],
                    self.encoded_feature_names[column],
                ):
                    transformed[output_column] = values.eq(category).astype("int8")

        output = pd.DataFrame(transformed, index=df.index)
        return output.loc[:, list(self.feature_names_out)].reset_index(drop=True)

    def _scale(self, column: str, values: pd.Series) -> pd.Series:
        """Apply the training-fitted scaling parameters for one numeric feature."""
        parameters = self.scale_parameters.get(column)
        if parameters is None or self.scaling == "none":
            return values
        if self.scaling == "standard":
            return (values - parameters["mean"]) / parameters["scale"]
        return (values - parameters["minimum"]) / parameters["range"]

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible representation of the fitted artifact."""
        return {
            "artifact_format_version": self.artifact_format_version,
            "input_features": list(self.input_features),
            "numeric_features": list(self.numeric_features),
            "categorical_features": list(self.categorical_features),
            "dropped_features": dict(self.dropped_features),
            "numeric_fill_values": dict(self.numeric_fill_values),
            "categorical_fill_values": dict(self.categorical_fill_values),
            "categories": {column: list(values) for column, values in self.categories.items()},
            "encoded_feature_names": {
                column: list(values) for column, values in self.encoded_feature_names.items()
            },
            "scale_parameters": {
                column: dict(values) for column, values in self.scale_parameters.items()
            },
            "categorical_encoding": self.categorical_encoding,
            "scaling": self.scaling,
            "feature_names_out": list(self.feature_names_out),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "MLPreprocessingArtifact":
        """Restore a fitted artifact from a JSON-compatible dictionary."""
        version = int(payload.get("artifact_format_version", 0))
        if version != 1:
            raise ValueError(f"Unsupported ML artifact format version: {version}.")
        return cls(
            input_features=tuple(payload["input_features"]),
            numeric_features=tuple(payload["numeric_features"]),
            categorical_features=tuple(payload["categorical_features"]),
            dropped_features=dict(payload["dropped_features"]),
            numeric_fill_values={
                column: float(value) for column, value in payload["numeric_fill_values"].items()
            },
            categorical_fill_values=dict(payload["categorical_fill_values"]),
            categories={column: tuple(values) for column, values in payload["categories"].items()},
            encoded_feature_names={
                column: tuple(values) for column, values in payload["encoded_feature_names"].items()
            },
            scale_parameters={
                column: {name: float(value) for name, value in values.items()}
                for column, values in payload["scale_parameters"].items()
            },
            categorical_encoding=str(payload["categorical_encoding"]),
            scaling=str(payload["scaling"]),
            feature_names_out=tuple(payload["feature_names_out"]),
            artifact_format_version=version,
        )

    def to_json(self, path: str | Path) -> None:
        """Save fitted preprocessing parameters as deterministic JSON."""
        Path(path).write_text(
            json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    @classmethod
    def from_json(cls, path: str | Path) -> "MLPreprocessingArtifact":
        """Load fitted preprocessing parameters from JSON."""
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("ML preprocessing artifact must contain a JSON object.")
        return cls.from_dict(payload)

    def to_sklearn(self) -> object:
        """Return a scikit-learn transformer when the optional ML extra is installed."""
        try:
            from sklearn.preprocessing import FunctionTransformer
        except ImportError as error:
            raise ImportError(
                'Install scikit-learn support with: pip install "eazydatafix[ml]"'
            ) from error
        return FunctionTransformer(self.transform, validate=False)

    @staticmethod
    def encoded_name(column: str, category: str, index: int) -> str:
        """Return a collision-resistant deterministic one-hot feature name."""
        label = re.sub(r"[^a-z0-9]+", "_", category.casefold()).strip("_") or "value"
        return f"{column}__{index}_{label}"


@dataclass(slots=True)
class MLReadyResult:
    """Return leakage-safe train/test features and fitted preprocessing evidence."""

    target: str
    X_train: pd.DataFrame
    X_test: pd.DataFrame
    y_train: pd.Series
    y_test: pd.Series
    artifact: MLPreprocessingArtifact
    config: MLReadyConfig
    analysis_ready_result: AnalysisReadyResult
    issues: list[MLReadyIssue]
    changes: list[str]
    warnings: list[str]
    readiness_score: float

    @property
    def is_ready(self) -> bool:
        """Return whether the transformed split passes the configured ML gate."""
        has_errors = any(issue.severity == "error" for issue in self.issues)
        return (
            self.readiness_score >= self.config.minimum_readiness_score
            and not has_errors
            and not self.X_train.empty
            and not self.X_test.empty
        )

    @property
    def feature_names(self) -> list[str]:
        """Return transformed feature names in deterministic model-input order."""
        return list(self.artifact.feature_names_out)

    @property
    def train_dataset(self) -> pd.DataFrame:
        """Return transformed training features with the untouched target appended."""
        return pd.concat(
            [self.X_train, self.y_train.rename(self.target).reset_index(drop=True)],
            axis=1,
        )

    @property
    def test_dataset(self) -> pd.DataFrame:
        """Return transformed test features with the untouched target appended."""
        return pd.concat(
            [self.X_test, self.y_test.rename(self.target).reset_index(drop=True)],
            axis=1,
        )

    def save(self, directory: str | Path, prefix: str = "ml_ready") -> tuple[Path, ...]:
        """Save train/test CSV files and the reusable preprocessing artifact."""
        output_directory = Path(directory)
        output_directory.mkdir(parents=True, exist_ok=True)
        train_path = output_directory / f"{prefix}_train.csv"
        test_path = output_directory / f"{prefix}_test.csv"
        artifact_path = output_directory / f"{prefix}_preprocessing.json"
        self.train_dataset.to_csv(train_path, index=False)
        self.test_dataset.to_csv(test_path, index=False)
        self.artifact.to_json(artifact_path)
        return train_path, test_path, artifact_path
