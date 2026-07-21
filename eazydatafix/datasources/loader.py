"""
Dataset loader.

This module exposes :class:`DatasetLoader`, the façade used by the rest of
the library to turn any supported dataset input into a
:class:`pandas.DataFrame`. It delegates the actual loading to the data
sources registered in :data:`default_registry`.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from eazydatafix.datasources.csv import CSVDataSource
from eazydatafix.datasources.dataframe import DataFrameDataSource
from eazydatafix.datasources.excel import ExcelDataSource
from eazydatafix.datasources.json import JSONDataSource
from eazydatafix.datasources.parquet import ParquetDataSource
from eazydatafix.datasources.registry import DataSourceRegistry
from eazydatafix.exceptions import (
    DatasetNotFoundError,
    InvalidDatasetError,
)


logger = logging.getLogger(__name__)


def build_default_registry() -> DataSourceRegistry:
    """
    Build a registry pre-populated with the built-in data sources.
    """
    registry = DataSourceRegistry()
    registry.register(DataFrameDataSource())
    registry.register(CSVDataSource())
    registry.register(ExcelDataSource())
    registry.register(JSONDataSource())
    registry.register(ParquetDataSource())
    return registry


#: Registry pre-populated with the built-in data sources.
default_registry: DataSourceRegistry = build_default_registry()


class DatasetLoader:
    """
    Loads datasets from supported sources.

    The loader delegates to a :class:`DataSourceRegistry`. By default it
    uses :data:`default_registry` which handles:

    - Pandas DataFrame
    - CSV
    - Excel (``.xlsx`` / ``.xls``)
    - JSON
    - Parquet
    """

    registry: DataSourceRegistry = default_registry

    @classmethod
    def load(cls, dataset) -> pd.DataFrame:
        """
        Load a dataset into a pandas DataFrame.
        """

        # In-memory DataFrame: skip path checks and delegate directly.
        if isinstance(dataset, pd.DataFrame):
            return cls.registry.resolve(dataset).load(dataset)

        if not isinstance(dataset, (str, Path)):
            raise InvalidDatasetError(
                "Unsupported dataset type: "
                f"{type(dataset).__name__}. Expected a pandas DataFrame "
                "or a path to a supported dataset file."
            )

        file_path = Path(dataset)

        if not file_path.exists():
            raise DatasetNotFoundError(
                f"Dataset not found: {file_path}"
            )

        data_source = cls.registry.resolve(file_path)
        data_source_name = getattr(
            data_source,
            "name",
            type(data_source).__name__,
        )

        logger.debug(
            "Loading dataset '%s' with '%s' data source.",
            file_path,
            data_source_name,
        )

        try:
            return data_source.load(file_path)

        except InvalidDatasetError:
            # Data source raised a specific, user-facing error; propagate as-is.
            raise

        except Exception as exc:
            logger.exception(
                "Unable to load dataset '%s' with '%s' data source.",
                file_path,
                data_source_name,
            )
            raise InvalidDatasetError(
                "Unable to load dataset "
                f"'{file_path}' using the '{data_source_name}' data source."
            ) from exc
