from easydatafix.assessment.profiler import DatasetProfiler


def test_dataset_profiler():
    profiler = DatasetProfiler()

    profile = profiler.profile("data/employees.csv")

    assert profile.rows == 3
    assert profile.columns == 4
    assert profile.file_name == "employees.csv"
    assert profile.file_type == "csv"
    assert profile.column_names == ["id", "name", "age", "salary"]
