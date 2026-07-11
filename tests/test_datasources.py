"""
Tests for the ``easydatafix.datasources`` package.
"""

from pathlib import Path

import pandas as pd
import pytest

from easydatafix.core.dataset_loader import (
    DatasetLoader as ShimDatasetLoader,
)
from easydatafix.datasources import (
    CSVDataSource,
    DataFrameDataSource,
    DataSource,
    DataSourceRegistry,
    DatasetLoader,
    ExcelDataSource,
    JSONDataSource,
    ParquetDataSource,
    default_registry,
)
from easydatafix.exceptions import (
    DatasetNotFoundError,
    InvalidDatasetError,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_df() -> pd.DataFrame:

    return pd.DataFrame(
        {
            "id": [1, 2, 3],
            "name": ["Alice", "Bob", "Carol"],
            "age": [30, 25, 40],
        }
    )


# ---------------------------------------------------------------------------
# Backward-compatibility
# ---------------------------------------------------------------------------


class TestBackwardCompatibility:

    def test_shim_reexports_same_class(self) -> None:

        assert ShimDatasetLoader is DatasetLoader

    def test_default_registry_is_prepopulated(self) -> None:

        source_types = {
            type(s) for s in default_registry.sources()
        }

        assert CSVDataSource in source_types
        assert ExcelDataSource in source_types
        assert JSONDataSource in source_types
        assert ParquetDataSource in source_types
        assert DataFrameDataSource in source_types


# ---------------------------------------------------------------------------
# DatasetLoader
# ---------------------------------------------------------------------------


class TestDatasetLoader:

    def test_load_dataframe_returns_copy(
        self,
        sample_df: pd.DataFrame,
    ) -> None:

        result = DatasetLoader.load(sample_df)

        assert result is not sample_df
        assert result.equals(sample_df)

    def test_load_csv(
        self,
        tmp_path: Path,
        sample_df: pd.DataFrame,
    ) -> None:

        file_path = tmp_path / "data.csv"
        sample_df.to_csv(file_path, index=False)

        result = DatasetLoader.load(file_path)

        assert list(result.columns) == list(sample_df.columns)
        assert len(result) == len(sample_df)

    def test_load_csv_from_string_path(
        self,
        tmp_path: Path,
        sample_df: pd.DataFrame,
    ) -> None:

        file_path = tmp_path / "data.csv"
        sample_df.to_csv(file_path, index=False)

        result = DatasetLoader.load(str(file_path))

        assert len(result) == len(sample_df)

    def test_load_excel(
        self,
        tmp_path: Path,
        sample_df: pd.DataFrame,
    ) -> None:

        file_path = tmp_path / "data.xlsx"
        sample_df.to_excel(file_path, index=False)

        result = DatasetLoader.load(file_path)

        assert list(result.columns) == list(sample_df.columns)
        assert len(result) == len(sample_df)

    def test_load_json(
        self,
        tmp_path: Path,
        sample_df: pd.DataFrame,
    ) -> None:

        file_path = tmp_path / "data.json"
        sample_df.to_json(file_path, orient="records")

        result = DatasetLoader.load(file_path)

        assert set(result.columns) == set(sample_df.columns)
        assert len(result) == len(sample_df)

    def test_load_parquet(
        self,
        tmp_path: Path,
        sample_df: pd.DataFrame,
    ) -> None:

        pytest.importorskip("pyarrow")

        file_path = tmp_path / "data.parquet"
        sample_df.to_parquet(file_path, index=False)

        result = DatasetLoader.load(file_path)

        assert list(result.columns) == list(sample_df.columns)
        assert len(result) == len(sample_df)

    def test_missing_file_raises(
        self,
        tmp_path: Path,
    ) -> None:

        with pytest.raises(DatasetNotFoundError):
            DatasetLoader.load(tmp_path / "does_not_exist.csv")

    def test_unsupported_extension_raises(
        self,
        tmp_path: Path,
    ) -> None:

        file_path = tmp_path / "data.txt"
        file_path.write_text("hello")

        with pytest.raises(InvalidDatasetError) as exc:
            DatasetLoader.load(file_path)

        assert "No data source available" in str(exc.value)

    def test_unsupported_input_type_raises(self) -> None:

        with pytest.raises(InvalidDatasetError) as exc:
            DatasetLoader.load(12345)

        assert "Unsupported dataset type" in str(exc.value)

    def test_corrupt_file_raises(
            self,
            tmp_path: Path,
        ) -> None:
        """
        With a Parquet backend installed, a corrupt ``.parquet`` file must
        surface as a generic ``Unable to load dataset`` error from the
        loader (i.e. the low-level pandas exception is wrapped).
        """

        pytest.importorskip("pyarrow")

        file_path = tmp_path / "data.parquet"
        file_path.write_text("not a real parquet file")

        with pytest.raises(InvalidDatasetError) as exc:
            DatasetLoader.load(file_path)

        assert "Unable to load dataset" in str(exc.value)

    def test_parquet_without_backend_reports_friendly_error(
            self,
            tmp_path: Path,
        ) -> None:
        """
        Without a Parquet backend installed, loading a ``.parquet`` file
        must raise the friendly install-me error instead of the pandas
        internal ImportError.
        """

        try:
            import pyarrow  # noqa: F401
            pytest.skip("pyarrow is installed; friendly error not applicable")
        except ImportError:
            pass

        try:
            import fastparquet  # noqa: F401
            pytest.skip("fastparquet is installed; friendly error not applicable")
        except ImportError:
            pass

        file_path = tmp_path / "data.parquet"
        file_path.write_text("irrelevant contents")

        with pytest.raises(InvalidDatasetError) as exc:
            DatasetLoader.load(file_path)

        assert "easydatafix[parquet]" in str(exc.value)


# ---------------------------------------------------------------------------
# Individual data sources
# ---------------------------------------------------------------------------


class TestDataSources:

    def test_dataframe_source_can_load(
        self,
        sample_df: pd.DataFrame,
    ) -> None:

        source = DataFrameDataSource()

        assert source.can_load(sample_df) is True
        assert source.can_load("foo.csv") is False

        loaded = source.load(sample_df)

        assert loaded is not sample_df
        assert loaded.equals(sample_df)

    def test_csv_source_can_load(self) -> None:

        source = CSVDataSource()

        assert source.can_load(Path("a.csv")) is True
        assert source.can_load(Path("a.CSV")) is True
        assert source.can_load(Path("a.xlsx")) is False
        assert source.can_load("a.csv") is False  # not a Path

    def test_excel_source_can_load(self) -> None:

        source = ExcelDataSource()

        assert source.can_load(Path("a.xlsx")) is True
        assert source.can_load(Path("a.xls")) is True
        assert source.can_load(Path("a.csv")) is False

    def test_json_source_can_load(self) -> None:

        source = JSONDataSource()

        assert source.can_load(Path("a.json")) is True
        assert source.can_load(Path("a.csv")) is False

    def test_parquet_source_can_load(self) -> None:

        source = ParquetDataSource()

        assert source.can_load(Path("a.parquet")) is True
        assert source.can_load(Path("a.csv")) is False


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


class TestDataSourceRegistry:

    def test_resolve_returns_matching_source(
        self,
        sample_df: pd.DataFrame,
    ) -> None:

        registry = DataSourceRegistry()
        registry.register(DataFrameDataSource())
        registry.register(CSVDataSource())

        assert isinstance(
            registry.resolve(sample_df),
            DataFrameDataSource,
        )
        assert isinstance(
            registry.resolve(Path("a.csv")),
            CSVDataSource,
        )

    def test_resolve_raises_when_no_match(self) -> None:

        registry = DataSourceRegistry()
        registry.register(CSVDataSource())

        with pytest.raises(InvalidDatasetError):
            registry.resolve(Path("a.txt"))

    def test_custom_data_source_can_be_registered(
        self,
        tmp_path: Path,
    ) -> None:

        class TSVDataSource(DataSource):

            name = "tsv"

            def can_load(self, source) -> bool:
                return (
                    isinstance(source, Path)
                    and source.suffix.lower() == ".tsv"
                )

            def load(self, source) -> pd.DataFrame:
                return pd.read_csv(source, sep="\t")

        registry = DataSourceRegistry()
        registry.register(TSVDataSource())

        file_path = tmp_path / "data.tsv"
        file_path.write_text("a\tb\n1\t2\n3\t4\n")

        resolved = registry.resolve(file_path)

        assert isinstance(resolved, TSVDataSource)

        df = resolved.load(file_path)

        assert list(df.columns) == ["a", "b"]
        assert len(df) == 2
