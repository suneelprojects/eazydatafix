import os

import pandas as pd

from easydatafix.exceptions import (
    DatasetNotFoundError,
    InvalidDatasetError,
)


class DatasetLoader:
    """
    Loads datasets from supported file formats.
    """

    @staticmethod
    def load(file_path: str) -> pd.DataFrame:
        """
        Load a dataset into a pandas DataFrame.
        """

        try:
            extension = os.path.splitext(file_path)[1].lower()

            if extension == ".csv":
                return pd.read_csv(file_path)

            if extension in [".xlsx", ".xls"]:
                return pd.read_excel(file_path)

            raise InvalidDatasetError(
                f"Unsupported file format: {extension}"
            )

        except FileNotFoundError as exc:
            raise DatasetNotFoundError(
                f"Dataset not found: {file_path}"
            ) from exc

        except InvalidDatasetError:
            raise

        except Exception as exc:
            raise InvalidDatasetError(
                f"Unable to load dataset: {file_path}"
            ) from exc
