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

### Milestone 8: Controlled, Auditable Cleaning — Ready for v1.0.0
- [x] Configurable missing-value marker detection
- [x] Column-level cleaning rules and dry-run previews
- [x] Structured before/after cleaning change logs
- [x] Unified profile → assess → fix → EDA workflow

### Milestone 9: Preparation and Feature Readiness — Ready for v1.0.0
- [x] Reliable type and date conversion controls
- [x] Duplicate, outlier, text, and category preparation controls
- [x] Structured preparation reports

### Milestone 10: Validation and Contracts — Ready for v1.0.0
- [x] Schema inference and expected-schema validation
- [x] Reusable quality rules with explicit pass/fail reports
- [x] Pipeline-friendly validation contracts

### Milestone 11: Production Workflows — Ready for v1.0.0
- [x] `edf` command-line interface with JSON/YAML configuration
- [x] Batch and multi-file processing with structured logs and exit codes
- [x] Lightweight extension interface for supported custom steps

### Milestone 12: Stable API — Ready for v1.0.0
- [x] Consolidated public API, formal result/report objects, and errors
- [x] Compatibility test suite and migration guidance for necessary breaks
- [x] Complete release verification

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
