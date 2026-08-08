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
    assert result.semantic_roles == {
        "age": "numeric_measure",
        "income": "numeric_measure",
        "department": "categorical",
    }
    assert result.numeric_columns == ["age", "income"]
    assert result.categorical_columns == ["department"]
    assert result.identifier_columns == []
    assert result.datetime_columns == []
    assert result.boolean_columns == []
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


def test_eda_detects_semantic_roles_and_excludes_identifiers_from_numeric_analysis() -> None:
    employees = pd.DataFrame(
        {
            "id": [101, 102, 103, 104, 105],
            "name": ["Asha", "Ben", "Chen", "Divya", "Eli"],
            "email": [
                "asha@example.com",
                "ben@example.com",
                "chen@example.com",
                "divya@example.com",
                "eli@example.com",
            ],
            "phone": [
                9876543210,
                9876543211,
                None,
                9876543213,
                9876543214,
            ],
            "age": [25, 31, 29, 42, 37],
            "salary": [50000, 62000, 58000, 81000, 73000],
            "department": [
                "Engineering",
                "Finance",
                "Sales",
                "Legal",
                "Engineering",
            ],
            "joining_date": [
                "2022-01-15",
                "2021-06-20",
                "2023-03-10",
                "2020-11-05",
                "2022-09-01",
            ],
            "is_active": [True, True, False, True, False],
        }
    )

    result = edf.eda(employees)

    assert result.numeric_columns == ["age", "salary"]
    assert result.identifier_columns == ["id", "name", "email", "phone"]
    assert result.categorical_columns == ["department"]
    assert result.datetime_columns == ["joining_date"]
    assert result.boolean_columns == ["is_active"]
    assert result.semantic_roles == {
        "id": "identifier",
        "name": "identifier",
        "email": "identifier",
        "phone": "identifier",
        "age": "numeric_measure",
        "salary": "numeric_measure",
        "department": "categorical",
        "joining_date": "datetime",
        "is_active": "boolean",
    }
    assert set(result.numeric_statistics) == {"age", "salary"}
    assert set(result.correlation_matrix) == {"age", "salary"}
    assert all(
        set(correlations) == {"age", "salary"}
        for correlations in result.correlation_matrix.values()
    )
    assert set(result.categorical_summaries) == {"department"}
    assert (
        "Treat email as an identifier rather than a categorical feature." in result.recommendations
    )
    assert not any(
        "high-cardinality" in recommendation.lower() for recommendation in result.recommendations
    )


def test_eda_does_not_use_unique_ratio_alone_for_small_categorical_columns() -> None:
    dataset = pd.DataFrame(
        {
            "department": ["Sales", "Finance", "Legal", "Support", "Sales"],
            "age": [22, 28, 34, 40, 46],
        }
    )

    result = edf.eda(dataset)

    assert result.semantic_roles["department"] == "categorical"
    assert not any(
        "high-cardinality" in recommendation.lower() for recommendation in result.recommendations
    )


def test_eda_recommends_review_for_large_high_cardinality_categories() -> None:
    dataset = pd.DataFrame(
        {
            "segment": [f"segment_{index % 20}" for index in range(25)],
            "value": list(range(25)),
        }
    )

    result = edf.eda(dataset)

    assert result.semantic_roles["segment"] == "categorical"
    assert any(
        recommendation == "Review high-cardinality categorical columns: segment."
        for recommendation in result.recommendations
    )


def test_eda_detects_near_unique_text_identifiers_with_sufficient_rows() -> None:
    dataset = pd.DataFrame(
        {
            "external_reference": [
                *(f"reference_{index}" for index in range(19)),
                "reference_0",
            ],
            "value": list(range(20)),
        }
    )

    result = edf.eda(dataset)

    assert result.semantic_roles["external_reference"] == "identifier"
    assert "external_reference" in result.identifier_columns
    assert (
        "Treat external_reference as an identifier rather than a categorical feature."
        in result.recommendations
    )


def test_eda_only_parses_date_shaped_or_date_named_text_as_datetime() -> None:
    dataset = pd.DataFrame(
        {
            "event_day": ["2024-01-01", "2024-01-02", "2024-01-03"],
            "description": ["May", "June", "July"],
        }
    )

    result = edf.eda(dataset)

    assert result.semantic_roles["event_day"] == "datetime"
    assert result.semantic_roles["description"] == "categorical"


def test_eda_preserves_existing_public_apis() -> None:
    assert edf.__version__ == "1.0.0"
    assert callable(edf.profile)
    assert callable(edf.assess)
    assert callable(edf.assess_ai_readiness)
    assert callable(edf.fix)
    assert callable(edf.prepare)
    assert callable(edf.analysis_ready)
    assert callable(edf.eda)
