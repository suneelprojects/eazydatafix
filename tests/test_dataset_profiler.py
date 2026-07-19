from eazydatafix.assessment.profiler import DatasetProfiler


def test_dataset_profiler(
    data_dir,
) -> None:

    profiler = DatasetProfiler()

    profile = profiler.profile(
        data_dir / "profiler.csv",
    )

    assert profile.file_name == "profiler.csv"
    assert profile.file_type == "csv"

    assert profile.rows == 3
    assert profile.columns == 4

    assert profile.column_names == [
        "id",
        "name",
        "age",
        "salary",
    ]

    assert profile.memory_usage_bytes > 0

    assert len(profile.data_types) == 4
