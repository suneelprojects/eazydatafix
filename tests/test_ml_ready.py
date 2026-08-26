import importlib.util

import pandas as pd
import pytest

import eazydatafix as edf


def _ml_config(**overrides: object) -> edf.MLReadyConfig:
    """Return deterministic no-shuffle configuration for split-sensitive tests."""
    values = {"test_size": 0.20, "shuffle": False, **overrides}
    return edf.MLReadyConfig(**values)


def test_ml_ready_fits_imputation_encoding_and_scaling_on_training_only() -> None:
    """Test rows cannot influence fitted preprocessing parameters or categories."""
    dataset = pd.DataFrame(
        {
            "value": [1.0, 2.0, None, 4.0, 5.0, 6.0, 7.0, 8.0, 1000.0, None],
            "segment": ["a", "b", "a", "b", "a", "b", "a", "b", "unseen", "unseen"],
            "outcome": [0, 1, 0, 1, 0, 1, 0, 1, 0, 1],
        }
    )
    original = dataset.copy(deep=True)

    result = edf.ml_ready(
        dataset,
        target="outcome",
        config=_ml_config(scaling="standard"),
    )

    assert result.artifact.numeric_fill_values["value"] == 5.0
    assert result.artifact.scale_parameters["value"]["mean"] == 4.75
    assert result.artifact.scale_parameters["value"]["scale"] == pytest.approx(2.222048604328897)
    assert result.artifact.categories["segment"] == ("a", "b")
    assert len(result.X_train) == 8
    assert len(result.X_test) == 2
    assert not result.X_train.isna().any().any()
    assert not result.X_test.isna().any().any()
    assert all(pd.api.types.is_numeric_dtype(dtype) for dtype in result.X_train.dtypes)
    assert any(issue.code == "unknown_category" for issue in result.issues)
    assert result.is_ready is True
    pd.testing.assert_frame_equal(dataset, original)


def test_ml_ready_detects_and_excludes_unsafe_features() -> None:
    """Identifiers, constants, high cardinality, dates, and leakage are audited."""
    rows = 20
    target = [0, 1] * 10
    dataset = pd.DataFrame(
        {
            "customer_id": [f"C{index:03d}" for index in range(rows)],
            "constant": ["same"] * rows,
            "session_token": [f"token-{index}" for index in range(rows)],
            "outcome_copy": target,
            "recorded_date": pd.date_range("2026-01-01", periods=rows, freq="D"),
            "safe_value": list(range(rows)),
            "outcome": target,
        }
    )

    result = edf.ml_ready(dataset, target="outcome", config=_ml_config())

    assert result.artifact.dropped_features == {
        "customer_id": "identifier",
        "constant": "constant",
        "session_token": "high cardinality",
        "outcome_copy": "potential target leakage",
        "recorded_date": "unsupported datetime feature",
    }
    assert result.feature_names == ["safe_value"]
    assert set(issue.code for issue in result.issues) >= {
        "identifier_feature",
        "constant_feature",
        "high_cardinality",
        "leakage_risk",
        "unsupported_feature",
    }
    assert result.is_ready is True


def test_ml_ready_artifact_round_trip_reuses_exact_training_parameters(tmp_path) -> None:
    """Saved artifacts transform new Analysis Ready rows without refitting."""
    dataset = pd.DataFrame(
        {
            "age": [20, 25, 30, 35, 40, 45, 50, 55, 60, 65],
            "city": ["Hyd", "Vizag"] * 5,
            "hired": [0, 1] * 5,
        }
    )
    result = edf.ml_ready(
        dataset,
        target="hired",
        config=_ml_config(scaling="minmax"),
    )
    artifact_path = tmp_path / "preprocessing.json"
    result.artifact.to_json(artifact_path)
    restored = edf.MLPreprocessingArtifact.from_json(artifact_path)
    new_data = pd.DataFrame({"age": [25, None], "city": ["Hyd", "New City"]})

    expected = result.artifact.transform(new_data)
    actual = restored.transform(new_data)

    pd.testing.assert_frame_equal(actual, expected)
    assert restored.feature_names_out == result.artifact.feature_names_out
    assert actual.loc[1].filter(like="city__").sum() == 0


def test_ml_ready_supports_explicit_imputation_ordinal_encoding_and_minmax() -> None:
    """Alternative preprocessing controls remain fitted and fully numeric."""
    dataset = pd.DataFrame(
        {
            "value": [1.0, None, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
            "group": ["a", None, "b", "a", "b", "a", "b", "a", "b", "a"],
            "target": [0, 1] * 5,
        }
    )
    result = edf.ml_ready(
        dataset,
        target="target",
        config=_ml_config(
            numeric_imputation="zero",
            categorical_imputation="constant",
            categorical_fill_value="missing",
            categorical_encoding="ordinal",
            scaling="minmax",
        ),
    )

    assert result.artifact.numeric_fill_values["value"] == 0.0
    assert result.artifact.categorical_fill_values["group"] == "missing"
    assert result.artifact.categories["group"] == ("a", "b", "missing")
    assert result.feature_names == ["value", "group"]
    assert result.X_train.min().min() >= 0.0
    assert not result.X_train.isna().any().any()


def test_ml_ready_result_saves_splits_and_artifact(tmp_path) -> None:
    """A result exports reusable data splits without producing a trained model."""
    dataset = pd.DataFrame(
        {
            "feature": list(range(10)),
            "group": ["a", "b"] * 5,
            "target": [0, 1] * 5,
        }
    )

    result = edf.ml_ready(dataset, target="target", config=_ml_config())
    paths = result.save(tmp_path, prefix="churn")

    assert all(path.exists() for path in paths)
    assert pd.read_csv(paths[0]).columns[-1] == "target"
    assert pd.read_csv(paths[1]).columns[-1] == "target"
    assert edf.MLPreprocessingArtifact.from_json(paths[2]).feature_names_out
    assert not hasattr(result, "model")
    assert not hasattr(result, "predictions")


def test_ml_ready_resolves_normalized_target_and_drops_missing_labels() -> None:
    """Target selection remains explicit across column normalization and missing labels."""
    dataset = pd.DataFrame(
        {
            "Feature Value": list(range(10)),
            "Outcome Label": [0, 1, 0, 1, None, 1, 0, 1, 0, 1],
        }
    )

    result = edf.ml_ready(dataset, target="Outcome Label", config=_ml_config())

    assert result.target == "outcome_label"
    assert len(result.y_train) + len(result.y_test) == 9
    assert any(issue.code == "missing_target" for issue in result.issues)


def test_ml_ready_requires_an_explicit_existing_target() -> None:
    """Supervised preparation never guesses the target column."""
    dataset = pd.DataFrame({"feature": [1, 2], "label": [0, 1]})

    with pytest.raises(TypeError):
        edf.ml_ready(dataset)  # type: ignore[call-arg]
    with pytest.raises(ValueError, match="was not found"):
        edf.ml_ready(dataset, target="missing")


def test_ml_ready_single_class_target_fails_readiness_gate() -> None:
    """A transformed dataset with one training class is reported as not ML Ready."""
    dataset = pd.DataFrame(
        {
            "feature": list(range(10)),
            "outcome": [1] * 10,
        }
    )

    result = edf.ml_ready(dataset, target="outcome", config=_ml_config())

    assert any(issue.code == "single_class_target" for issue in result.issues)
    assert result.is_ready is False


@pytest.mark.parametrize(
    "analysis_config",
    [
        edf.AnalysisReadyConfig(fix_config=edf.FixConfig()),
        edf.AnalysisReadyConfig(
            fix_config=edf.FixConfig(missing_value_strategy="keep", dry_run=True)
        ),
        edf.AnalysisReadyConfig(
            fix_config=edf.FixConfig(missing_value_strategy="keep"),
            prepare_config=edf.PrepareConfig(outlier_action="cap"),
        ),
    ],
)
def test_ml_ready_rejects_pre_split_learned_or_dry_run_transformations(
    analysis_config: edf.AnalysisReadyConfig,
) -> None:
    """Imputation and fitted outlier handling cannot inspect the future test split."""
    with pytest.raises(ValueError):
        edf.MLReadyConfig(analysis_ready_config=analysis_config)


def test_ml_ready_artifact_offers_optional_sklearn_interoperability() -> None:
    """The artifact exposes a clear optional-extra boundary for scikit-learn."""
    dataset = pd.DataFrame({"feature": list(range(10)), "target": [0, 1] * 5})
    artifact = edf.ml_ready(dataset, target="target", config=_ml_config()).artifact

    if importlib.util.find_spec("sklearn") is None:
        with pytest.raises(ImportError, match=r"eazydatafix\[ml\]"):
            artifact.to_sklearn()
    else:
        transformer = artifact.to_sklearn()
        transformed = transformer.transform(pd.DataFrame({"feature": [1, 2]}))
        assert transformed.shape == (2, 1)
