from pathlib import Path

import pandas as pd

from easydatafix.models.dataset_profile import DatasetProfile


class DatasetProfiler:
    """
    Creates a structural profile of a dataset.
    """

    def profile(self, file_path: str) -> DatasetProfile:
        path = Path(file_path)

        df = pd.read_csv(path)

        return DatasetProfile(
            file_name=path.name,
            file_type=path.suffix.replace(".", "").lower(),
            rows=len(df),
            columns=len(df.columns),
            column_names=df.columns.tolist(),
            data_types=[str(dtype) for dtype in df.dtypes],
            memory_usage_bytes=int(df.memory_usage(deep=True).sum()),
        )
