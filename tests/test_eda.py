from pathlib import Path

import pandas as pd
import pytest

import easydatafix as edf


@pytest.fixture
def sample_dataframe() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "age": [20, 30, 30, None],
            "income": [100.0, 200.0, 200.0, 400.0],
            "department": ["Sales", "Engineering", "Engineering", "Sales"],
        }
    )


def test_eda_returns_deterministic_structured_result(
    sample_dataframe: pd.DataFrame,
) -> None:
    result = edf.eda(sample_dataframe)

    assert result.shape == (4, 3)
    assert result.column_names == ["age", "income", "department"]
    assert result.missing_values == {
        "age": 1,
        "income": 0,
        "department": 0,
    }
    assert result.duplicate_rows == 1
    assert result.numeric_columns == ["age", "income"]
    assert result.categorical_columns == ["department"]
    assert result.unique_value_counts["department"] == 2
    assert result.numeric_statistics["age"]["mean"] == 26.666666666666668
    assert result.categorical_summaries["department"]["most_frequent"] == "Sales"
    assert result.correlation_matrix["age"]["income"] is not None
    assert any("missing value" in observation.lower() for observation in result.observations)
    assert any("age" in recommendation for recommendation in result.recommendations)


@pytest.mark.parametrize("suffix", ["csv", "xlsx", "json", "parquet"])
def test_eda_supports_file_inputs(
    tmp_path: Path,
    sample_dataframe: pd.DataFrame,
    suffix: str,
) -> None:
    file_path = tmp_path / f"dataset.{suffix}"

    if suffix == "csv":
        sample_dataframe.to_csv(file_path, index=False)
    elif suffix == "xlsx":
        sample_dataframe.to_excel(file_path, index=False)
    elif suffix == "json":
        sample_dataframe.to_json(file_path, orient="records")
    else:
        sample_dataframe.to_parquet(file_path, index=False)

    result = edf.eda(file_path)

    assert result.shape == sample_dataframe.shape
    assert result.column_names == list(sample_dataframe.columns)
