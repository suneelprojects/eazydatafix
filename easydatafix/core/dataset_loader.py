from pathlib import Path

import pandas as pd

from easydatafix.exceptions import (
    DatasetNotFoundError,
    InvalidDatasetError,
)


class DatasetLoader:
    """
    Loads datasets from supported sources.
    """

    LOADERS = {
        ".csv": pd.read_csv,
        ".xlsx": pd.read_excel,
        ".xls": pd.read_excel,
        ".json": pd.read_json,
        ".parquet": pd.read_parquet,
    }

    @classmethod
    def load(cls, dataset) -> pd.DataFrame:
        """
        Load a dataset into a pandas DataFrame.

        Supported inputs:

        - CSV
        - Excel (.xlsx/.xls)
        - JSON
        - Parquet
        - Pandas DataFrame
        """

        # Already a DataFrame
        if isinstance(dataset, pd.DataFrame):
            return dataset.copy()

        if not isinstance(dataset, (str, Path)):
            raise InvalidDatasetError(
                f"Unsupported dataset type: {type(dataset).__name__}"
            )

        file_path = Path(dataset)

        if not file_path.exists():
            raise DatasetNotFoundError(
                f"Dataset not found: {file_path}"
            )

        extension = file_path.suffix.lower()

        loader = cls.LOADERS.get(extension)

        if loader is None:
            raise InvalidDatasetError(
                f"Unsupported file format: {extension}"
            )

        try:
            return loader(file_path)

        except Exception as exc:
            raise InvalidDatasetError(
                f"Unable to load dataset: {file_path}"
            ) from exc
