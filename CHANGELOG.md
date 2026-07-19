# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog:
https://keepachangelog.com/en/1.1.0/

This project follows Semantic Versioning:
https://semver.org/

---

## [0.1.3] - 2026-07-11

### Added

- Modular Data Source architecture under `eazydatafix.datasources`
  (`DataSource`, `DataSourceRegistry`, `DatasetLoader`, `default_registry`,
  `build_default_registry`).
- JSON data source (`.json`) — accepted by `edf.assess`, `edf.fix`, and
  `edf.profile`.
- Parquet data source (`.parquet`) — accepted by `edf.assess`, `edf.fix`,
  and `edf.profile`.
- Pandas DataFrame is now also accepted by `edf.profile(...)` (previously
  only `edf.assess(...)` and `edf.fix(...)` supported DataFrames).
- Extensibility: user-defined data sources can be plugged in via
  `default_registry.register(...)`.
- Optional install extra `eazydatafix[parquet]` which pulls in `pyarrow`.
- Friendly, actionable error when a user attempts to load a `.parquet`
  file without a backend installed (tells them to run
  `pip install eazydatafix[parquet]`).
- Regression test suite covering every data source across the public API
  (`tests/test_datasources.py`, `tests/test_dataset_profiler_formats.py`).

### Changed

- `eazydatafix.core.dataset_loader.DatasetLoader` is now a thin
  backward-compatible re-export of the new
  `eazydatafix.datasources.loader.DatasetLoader`. Existing imports
  continue to work unchanged.
- `DatasetProfiler` now routes all inputs through `DatasetLoader`, so
  `edf.profile(...)` supports every format the library supports
  (previously CSV-only).

### Fixed

- `edf.profile(<xlsx>)` no longer crashes with `UnicodeDecodeError`.
- `edf.profile(<parquet>)` no longer crashes with `UnicodeDecodeError`.
- `edf.profile(<json>)` no longer silently returns zero rows.
- `edf.profile(<DataFrame>)` no longer crashes with `TypeError`.

### Internal

- Extracted per-format loading into dedicated classes: `CSVDataSource`,
  `ExcelDataSource`, `JSONDataSource`, `ParquetDataSource`,
  `DataFrameDataSource`.
- Loader dispatch is now registry-driven, opening the door for future
  non-file data sources (databases, cloud storage, APIs) without
  touching the loader.

### Compatibility

- **No breaking API changes.** `edf.assess`, `edf.fix`, `edf.profile`,
  `FixConfig`, `AssessmentEngine`, `FixEngine`, `Report`, and
  `DatasetProfiler` keep their names and call signatures.

---

## [0.1.0] - 2026-07-07

### Added

- Initial public release of EasyDataFix
- Dataset profiling engine
- Data quality assessment engine
- Completeness checks
- Uniqueness checks
- Validation engine
- Recommendation engine
- Data quality scoring
- Console report generation
- HTML report export
- PDF report export
- Excel report export
- CSV report export
- JSON report export
- Markdown report export
- GitHub Actions CI pipeline
- Automated unit tests
- Python 3.10–3.13 support
- TestPyPI package publishing
