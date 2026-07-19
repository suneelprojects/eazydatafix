"""
Regression tests for :class:`DatasetProfiler` across every data source.
"""

from pathlib import Path

import pandas as pd
import pytest

from eazydatafix.assessment.profiler import DatasetProfiler


@pytest.fixture
def sample_df() -> pd.DataFrame:

    return pd.DataFrame(
        {
            "id": [1, 2, 3],
            "name": ["Alice", "Bob", "Carol"],
            "age": [30, 25, 40],
        }
    )


class TestDatasetProfilerFormats:

    def test_profile_dataframe(
        self,
        sample_df: pd.DataFrame,
    ) -> None:

        profile = DatasetProfiler().profile(sample_df)

        assert profile.file_name == "DataFrame"
        assert profile.file_type == "dataframe"
        assert profile.rows == 3
        assert profile.columns == 3
        assert profile.column_names == ["id", "name", "age"]
        assert len(profile.data_types) == 3

    def test_profile_csv(
        self,
        tmp_path: Path,
        sample_df: pd.DataFrame,
    ) -> None:

        file_path = tmp_path / "data.csv"
        sample_df.to_csv(file_path, index=False)

        profile = DatasetProfiler().profile(file_path)

        assert profile.file_name == "data.csv"
        assert profile.file_type == "csv"
        assert profile.rows == 3
        assert profile.columns == 3

    def test_profile_excel(
        self,
        tmp_path: Path,
        sample_df: pd.DataFrame,
    ) -> None:

        file_path = tmp_path / "data.xlsx"
        sample_df.to_excel(file_path, index=False)

        profile = DatasetProfiler().profile(file_path)

        assert profile.file_name == "data.xlsx"
        assert profile.file_type == "xlsx"
        assert profile.rows == 3
        assert profile.columns == 3

    def test_profile_json(
        self,
        tmp_path: Path,
        sample_df: pd.DataFrame,
    ) -> None:

        file_path = tmp_path / "data.json"
        sample_df.to_json(file_path, orient="records")

        profile = DatasetProfiler().profile(file_path)

        assert profile.file_name == "data.json"
        assert profile.file_type == "json"
        assert profile.rows == 3
        assert profile.columns == 3

    def test_profile_parquet(
        self,
        tmp_path: Path,
        sample_df: pd.DataFrame,
    ) -> None:

        pytest.importorskip("pyarrow")

        file_path = tmp_path / "data.parquet"
        sample_df.to_parquet(file_path, index=False)

        profile = DatasetProfiler().profile(file_path)

        assert profile.file_name == "data.parquet"
        assert profile.file_type == "parquet"
        assert profile.rows == 3
        assert profile.columns == 3
