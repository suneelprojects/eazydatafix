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

    @staticmethod
    def load(dataset) -> pd.DataFrame:
        """
        Load a dataset into a pandas DataFrame.

        Supported inputs:

        - CSV
        - Excel (.xlsx/.xls)
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

        try:

            if extension == ".csv":
                return pd.read_csv(file_path)

            if extension in [".xlsx", ".xls"]:
                return pd.read_excel(file_path)

            raise InvalidDatasetError(
                f"Unsupported file format: {extension}"
            )

        except InvalidDatasetError:
            raise

        except Exception as exc:
            raise InvalidDatasetError(
                f"Unable to load dataset: {file_path}"
            ) from exc
