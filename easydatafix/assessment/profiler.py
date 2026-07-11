from pathlib import Path

import pandas as pd

from easydatafix.core.dataset_loader import DatasetLoader
from easydatafix.core.type_mapper import TypeMapper
from easydatafix.models.dataset_profile import DatasetProfile


class DatasetProfiler:
    """
    Creates a structural profile of a dataset.
    """

    def profile(self, dataset) -> DatasetProfile:

        df = DatasetLoader.load(dataset)

        if isinstance(dataset, pd.DataFrame):
            file_name = "DataFrame"
            file_type = "dataframe"
        else:
            path = Path(dataset)
            file_name = path.name
            file_type = path.suffix.replace(".", "").lower()

        return DatasetProfile(
            file_name=file_name,
            file_type=file_type,
            rows=len(df),
            columns=len(df.columns),
            column_names=df.columns.tolist(),
            data_types=[TypeMapper.from_pandas(str(dtype)) for dtype in df.dtypes],
            memory_usage_bytes=int(df.memory_usage(deep=True).sum()),
        )
