from __future__ import annotations

from pathlib import Path

import pandas as pd


class DatasetLoader:
    """Loads supported dataset inputs into pandas DataFrames."""

    @classmethod
    def load(
        cls,
        dataset: str | Path | pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Load a supported dataset input.

        Args:
            dataset: A pandas DataFrame or supported dataset file path.

        Returns:
            A pandas DataFrame containing the dataset.

        Raises:
            FileNotFoundError: If the dataset file does not exist.
            ValueError: If the dataset type or file format is unsupported.
        """

        if isinstance(dataset, pd.DataFrame):
            return dataset.copy()

        if not isinstance(dataset, (str, Path)):
            raise ValueError("Dataset must be a pandas DataFrame or a supported file path.")

        path = Path(dataset)

        if not path.exists():
            raise FileNotFoundError(f"Dataset file not found: {path}")

        readers = {
            ".csv": pd.read_csv,
            ".xlsx": pd.read_excel,
            ".xls": pd.read_excel,
            ".json": pd.read_json,
            ".parquet": pd.read_parquet,
        }

        reader = readers.get(path.suffix.lower())

        if reader is None:
            raise ValueError("Unsupported dataset format: " f"{path.suffix or 'no file extension'}")

        return reader(path)
