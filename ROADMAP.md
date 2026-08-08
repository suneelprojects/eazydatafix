# EazyDataFix Roadmap

## Agentic EDA Foundation

### Milestone 1: Deterministic Analysis
- [x] Structured exploratory data analysis result
- [x] DataFrame, CSV, Excel, JSON, and Parquet input support
- [x] Deterministic observations and recommendations
- [x] Numeric, categorical, missing-value, duplicate, and correlation summaries

### Milestone 2: Deterministic Analysis Planner
- [x] Analysis-plan generation
- [x] Selected and skipped step explanations
- [x] Priorities, required columns, and step dependencies
- [x] Planner warnings and deterministic summary

### Milestone 3: Deterministic Analysis Execution
- [x] Modular deterministic analysis handlers
- [x] Reproducible step outputs and execution ordering
- [x] Dataset/result validation and step-level failure isolation
- [x] JSON-ready execution result

### Milestone 4: Deterministic Agentic EDA Orchestration
- [x] End-to-end dataset understanding, planning, and execution coordination
- [x] Traceable deterministic follow-up actions and priority findings
- [x] Structured visualisation recommendations and unresolved domain questions
- [x] Validated threshold configuration, feature toggles, and JSON-ready output

### Milestone 5: Deterministic Reporting and Visualisation Artifacts
- [x] Standalone HTML and JSON reports with optional Markdown
- [x] Recommended visualisations rendered as deterministic PNG artifacts
- [x] Honest raw-data chart gating with supplied-dataset validation
- [x] JSON-ready artifact tracking and partial-failure reporting

### Milestone 6: Notebook Export and Human Approval
- [x] Notebook artifact export
- [x] Human approval checkpoints for domain-dependent decisions
- [x] Dataset fingerprint validation before approved execution
- [x] Full-plan approval, subset approval, and explicit rejection
- [x] Explicit dependency-completeness validation for subset approvals

### Milestone 7: Grounded Presentation — Released in v0.5.0
- [x] Optional LLM narratives grounded exclusively in deterministic metrics

### Milestone 8: Controlled, Auditable Cleaning — Planned for v0.6.0
- [ ] Configurable missing-value marker detection
- [ ] Column-level cleaning rules and dry-run previews
- [ ] Structured before/after cleaning change logs
- [ ] Unified profile → assess → fix → EDA workflow

### Milestone 9: Preparation and Feature Readiness — Planned for v0.7.0
- [ ] Reliable type and date conversion controls
- [ ] Duplicate, outlier, text, and category preparation controls
- [ ] Structured preparation reports

### Milestone 10: Validation and Contracts — Planned for v0.8.0
- [ ] Schema inference and expected-schema validation
- [ ] Reusable quality rules with explicit pass/fail reports
- [ ] Pipeline-friendly validation contracts

### Milestone 11: Production Workflows — Planned for v0.9.0
- [ ] `edf` command-line interface with JSON/YAML configuration
- [ ] Batch and multi-file processing with structured logs and exit codes
- [ ] Lightweight extension interface for supported custom steps

### Milestone 12: Stable API — Planned for v1.0.0
- [ ] Consolidated public API, formal result/report objects, and errors
- [ ] Compatibility test suite and migration guidance for necessary breaks
- [ ] Complete tutorials, reliability hardening, and release verification

## Version 0.1

### File Support
- [ ] CSV
- [ ] Excel

### Data Cleaning
- [ ] Remove duplicate rows
- [ ] Remove duplicate columns
- [ ] Trim extra spaces
- [ ] Standardize column names
- [ ] Remove empty rows
- [ ] Remove empty columns
- [ ] Fix data types
- [ ] Detect date columns
- [ ] Standardize date formats
- [ ] Detect boolean columns
- [ ] Remove special characters
- [ ] Normalize text
- [ ] Handle missing values
- [ ] Generate cleaning report

### Export
- [ ] CSV
- [ ] Excel

### Reports
- [ ] Summary
- [ ] Changes made
- [ ] Statistics
