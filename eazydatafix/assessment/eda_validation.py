from pathlib import Path

import pandas as pd

from eazydatafix.core.dataset_loader import DatasetLoader
from eazydatafix.models.eda_result import EDAResult


def load_eda_frame(
    dataset: str | Path | pd.DataFrame,
) -> pd.DataFrame:
    """
    Load and normalise a dataset for deterministic EDA consumers.

    Args:
        dataset: A DataFrame or supported dataset path.

    Returns:
        A copied DataFrame whose column labels are strings.

    Raises:
        ValueError: If string-normalised column labels would not be unique.
    """
    dataframe = DatasetLoader.load(dataset)
    column_names = [str(column) for column in dataframe.columns]

    if len(set(column_names)) != len(column_names):
        raise ValueError(
            "Dataset columns must remain unique when converted to strings "
            "for deterministic EDA processing."
        )

    dataframe.columns = column_names
    return dataframe


def validate_eda_result(
    dataframe: pd.DataFrame,
    result: EDAResult,
) -> None:
    """
    Validate that an EDA result corresponds to a supplied DataFrame.

    Args:
        dataframe: Normalised DataFrame to validate.
        result: Existing deterministic EDA result.

    Raises:
        ValueError: If shape, columns, missingness, duplicates, or uniqueness differ.
    """
    if tuple(dataframe.shape) != result.shape:
        raise ValueError(
            "The EDAResult shape does not match the supplied dataset: "
            f"expected {tuple(dataframe.shape)}, received {result.shape}."
        )

    if list(dataframe.columns) != result.column_names:
        raise ValueError("The EDAResult column names or order do not match the supplied dataset.")

    missing_values = {column: int(dataframe[column].isna().sum()) for column in dataframe.columns}

    if missing_values != result.missing_values:
        raise ValueError("The EDAResult missing-value summary does not match the supplied dataset.")

    duplicate_rows = int(dataframe.duplicated().sum())

    if duplicate_rows != result.duplicate_rows:
        raise ValueError("The EDAResult duplicate count does not match the supplied dataset.")

    unique_value_counts = {
        column: int(dataframe[column].nunique(dropna=True)) for column in dataframe.columns
    }

    if unique_value_counts != result.unique_value_counts:
        raise ValueError("The EDAResult unique-value counts do not match the supplied dataset.")
