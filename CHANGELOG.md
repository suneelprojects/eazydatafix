# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog:
https://keepachangelog.com/en/1.1.0/

This project follows Semantic Versioning:
https://semver.org/

---

## [Unreleased]

### Planned for v0.6.0

- Controlled, auditable cleaning with configurable missing-value markers,
  column-level rules, dry-run previews, and structured change logs.
- A unified deterministic `edf.run(...)` workflow for profile, assessment,
  cleaning, and EDA.

### Planned release milestones

- v0.7.0: preparation and feature readiness.
- v0.8.0: validation, schema inference, and data contracts.
- v0.9.0: CLI, configuration, batch processing, structured logs, and extensions.
- v1.0.0: stable public API, migration support, compatibility, and hardening.

---

## [0.5.0] - 2026-08-04

### Added

- Optional grounded AI narratives through
  `edf.generate_agentic_eda_narrative(...)`.
- Provider-neutral narrative adapter contract and optional OpenAI Responses API
  adapter, installable with `eazydatafix[openai]`.
- JSON-ready `AgenticEDANarrative`, `NarrativeClaim`, `NarrativeEvidence`, and
  `AgenticEDANarrativeConfig` models.
- Optional inclusion of an already validated narrative in Agentic EDA HTML,
  JSON, and Markdown reports.
- Evidence-reference sections in human-readable HTML and Markdown reports.

### Reliability

- Narrative providers receive only compact evidence from a completed
  deterministic workflow, never the raw dataset.
- Every generated narrative claim must cite supplied deterministic evidence.
  Invalid JSON, uncited claims, duplicate citations, unknown citations,
  invented numbers, unsupported causal language, insufficient lexical support,
  and over-limit sections fail with explicit errors.
- Narrative evidence is immutable during provider execution, and each narrative
  is bound to its exact workflow using a SHA-256 fingerprint.
- Narrative generation never reruns or modifies the deterministic workflow.

### Limitations

- Deterministic grounding checks are guardrails, not proof of semantic truth;
  AI-written narratives still require human review.

---

## [0.4.0] - 2026-08-01

### Added

- Two-phase human approval checkpoints through
  `edf.prepare_agentic_eda_approval(...)`,
  `edf.approve_agentic_eda_plan(...)`,
  `edf.reject_agentic_eda_plan(...)`, and `edf.resume_agentic_eda(...)`.
- Frozen, JSON-ready `AgenticEDAApprovalCheckpoint` models containing copied
  dataset understanding, the original deterministic plan, preserved
  configuration, ordered approval decisions, reviewer metadata, and SHA-256
  dataset and snapshot-integrity fingerprints.
- Full-plan and subset approval without allowing skipped, unknown, duplicate,
  or arbitrarily added execution steps.
- Dependency-incomplete subsets fail during approval with explicit guidance;
  required steps are never approved implicitly.
- Deterministic Jupyter Notebook export through
  `edf.export_agentic_eda_notebook(...)`.
- Notebook-format v4 output with stable Markdown and executable code cells for
  dataset understanding, planning, execution, orchestration, findings, and
  report export.
- Deterministic JSON companion datasets for DataFrame inputs.
- JSON-ready `AgenticEDANotebookResult` artifact metadata.

### Reliability

- Pending checkpoint preparation performs understanding and planning only; no
  analysis plan step executes before human approval.
- Resume rejects pending and rejected checkpoints, validates the supplied
  dataset fingerprint and all checkpoint decision fields, and reuses
  checkpoint understanding and planning results without recomputing them.
- Approval and resume copy caller-owned DataFrames and checkpoint snapshots.
- Notebook and companion artifacts are written atomically.
- Supplied datasets are validated against the existing workflow before output
  directories or files are created.
- Notebook export copies DataFrame inputs and does not mutate caller-owned
  datasets or workflow results.

### Compatibility

- No existing public APIs were removed or renamed.
- Version 0.4.0 supports Python 3.10–3.13.

---

## [0.3.0] - 2026-07-28

### Added

- Deterministic exploratory data analysis through `edf.eda(...)`, including
  dataset shape, data types, missingness, duplicates, descriptive statistics,
  categorical summaries, unique counts, and correlations.
- Semantic role detection for numeric measures, categorical dimensions,
  identifiers, datetimes, and booleans. Identifier-like numeric columns are
  excluded from measure statistics and correlations.
- Deterministic follow-up planning through `edf.plan_eda(...)`, with selected
  and skipped steps, reasons, priorities, required columns, dependencies,
  warnings, and summary.
- Deterministic plan execution through `edf.execute_eda(...)`, including
  modular handlers for quality, distributions, outliers, skewness, class
  imbalance, correlations, and datetime trends.
- End-to-end deterministic orchestration through
  `edf.run_agentic_eda(...)`, with traceable findings, follow-up actions,
  visualisation recommendations, unresolved domain questions, warnings, and
  overall status.
- Agentic EDA report export through `edf.export_agentic_eda_report(...)`.
  Standalone HTML and stable JSON are generated by default, with optional
  Markdown output.
- Deterministic PNG visualisations for supported orchestrator
  recommendations using matplotlib without an interactive backend.
- JSON-ready workflow, execution, planning, action, visualisation, question,
  finding, and report artifact models.
- Python 3.10, 3.11, 3.12, and 3.13 CI coverage.

### Changed

- Dataset/result validation is shared by deterministic execution and report
  export, preventing mismatched results from being reused with another
  dataset.
- Histograms and box plots require an optional matching dataset during report
  export. Recommendations are recorded as skipped when raw observations are
  unavailable rather than inferring or fabricating values.
- Package version metadata now reads from one authoritative module while
  remaining available as `eazydatafix.__version__`.
- Packaging metadata, documentation, exports, formatting, and linting were
  audited for the 0.3.0 release.

### Reliability

- DataFrame inputs are copied before deterministic analysis, execution, and
  reporting. Public workflows do not mutate caller-owned DataFrames.
- Deterministic ordering is preserved across plans, execution records,
  decisions, report sections, JSON output, and artifact filenames.
- Safe step, chart, and renderer failures are isolated and represented in
  structured status and warning fields.
- Source distributions and wheels are validated through a clean-environment
  installation and public API smoke test.

### Compatibility

- No existing public APIs were removed or renamed.
- Version 0.3.0 supports Python 3.10–3.13.

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

- Initial public release of EazyDataFix
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
