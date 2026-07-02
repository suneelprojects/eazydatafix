import pandas as pd


def autofix(file_path: str) -> pd.DataFrame:
    """
    Read a dataset and return it as a pandas DataFrame.

    Parameters
    ----------
    file_path : str
        Path to the CSV file.

    Returns
    -------
    pandas.DataFrame
    """

    print(f"📂 Reading: {file_path}")

    df = pd.read_csv(file_path)

    return df
