from pathlib import Path

import pandas as pd
import pytest

import eazydatafix as edf
from eazydatafix.models.eda_result import EDAResult


@pytest.fixture
def sample_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "age": [20, 30, 30, None],
            "income": [100.0, 200.0, 200.0, 400.0],
            "department": [
                "Sales",
                "Engineering",
                "Engineering",
                "Engineering",
            ],
        }
    )


def test_eda_returns_deterministic_structured_result(
    sample_df: pd.DataFrame,
) -> None:
    result = edf.eda(sample_df)

    assert isinstance(result, EDAResult)
    assert result.shape == (4, 3)
    assert result.column_names == [
        "age",
        "income",
        "department",
    ]
    assert result.data_types == {
        "age": "Decimal",
        "income": "Decimal",
        "department": "Text",
    }
    assert result.missing_values == {
        "age": 1,
        "income": 0,
        "department": 0,
    }
    assert result.duplicate_rows == 1
    assert result.numeric_columns == ["age", "income"]
    assert result.categorical_columns == ["department"]
    assert result.unique_value_counts == {
        "age": 2,
        "income": 3,
        "department": 2,
    }
    assert result.numeric_statistics["age"]["mean"] == pytest.approx(26.6666666667)
    assert result.categorical_summaries["department"] == {
        "count": 4,
        "missing_count": 0,
        "unique_count": 2,
        "most_frequent": "Engineering",
        "most_frequent_count": 3,
    }
    assert result.correlation_matrix["age"]["income"] is not None
    assert any("missing value" in observation.lower() for observation in result.observations)
    assert any("duplicate" in recommendation.lower() for recommendation in result.recommendations)


def test_eda_is_deterministic_and_does_not_mutate_input(
    sample_df: pd.DataFrame,
) -> None:
    original = sample_df.copy(deep=True)

    first = edf.eda(sample_df)
    second = edf.eda(sample_df)

    assert first == second
    pd.testing.assert_frame_equal(sample_df, original)


@pytest.mark.parametrize(
    "suffix",
    ["csv", "xlsx", "json", "parquet"],
)
def test_eda_supports_file_inputs(
    tmp_path: Path,
    sample_df: pd.DataFrame,
    suffix: str,
) -> None:
    file_path = tmp_path / f"dataset.{suffix}"

    if suffix == "csv":
        sample_df.to_csv(file_path, index=False)
    elif suffix == "xlsx":
        sample_df.to_excel(file_path, index=False)
    elif suffix == "json":
        sample_df.to_json(file_path, orient="records")
    else:
        pytest.importorskip("pyarrow")
        sample_df.to_parquet(file_path, index=False)

    result = edf.eda(file_path)

    assert result.shape == sample_df.shape
    assert result.column_names == list(sample_df.columns)


def test_eda_handles_empty_dataframe() -> None:
    result = edf.eda(pd.DataFrame())

    assert result.shape == (0, 0)
    assert result.numeric_statistics == {}
    assert result.categorical_summaries == {}
    assert result.correlation_matrix == {}
    assert result.duplicate_rows == 0


def test_eda_preserves_existing_public_apis() -> None:
    assert edf.__version__ == "0.2.1"
    assert callable(edf.profile)
    assert callable(edf.assess)
    assert callable(edf.assess_ai_readiness)
    assert callable(edf.fix)
    assert callable(edf.prepare)
    assert callable(edf.analysis_ready)
    assert callable(edf.eda)
