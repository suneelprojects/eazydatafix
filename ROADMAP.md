# EazyDataFix Roadmap

## Active product direction

EazyDataFix is now focused on deterministic data transformation that produces
Analysis Ready, ML Ready, and Power BI Ready datasets. AI narratives, AI
readiness, and Agentic EDA remain available for v1 compatibility, but active
feature development in those areas is paused.

Readiness profiles will compose the existing assessment, cleaning, preparation,
and contract components. They will not duplicate transformation engines.

## v1.1.0: Transformation foundation

- [x] Execute datatype conversion through the controlled cleaning pipeline
- [x] Add confidence thresholds for numeric and datetime conversion
- [x] Convert numeric text, currency, percentage, boolean, and date values
- [x] Protect identifiers, emails, phone numbers, and leading zeroes
- [x] Preserve dry-run previews and structured change auditing
- [ ] Add explicit per-column target datatype rules
- [ ] Report rejected and uncertain conversions without changing their values
- [ ] Pass cleaning configuration through JSON/YAML CLI workflows
- [ ] Add golden-dataset regression coverage for transformation idempotency

## v1.2.0: Analysis Ready profile

- [ ] Compose assess, fix, prepare, and validate as one readiness workflow
- [ ] Return before/after readiness scores, changes, warnings, and validation
- [ ] Detect constant, nearly empty, invalid, and inconsistent category columns
- [ ] Add configurable date-part derivation and outlier flagging
- [ ] Preserve the existing `analysis_ready(...)` DataFrame return contract

## v1.3.0: ML Ready profile

- [ ] Require explicit target selection for supervised workflows
- [ ] Split training and test data before fitting learned transformations
- [ ] Add numeric and categorical imputation, encoding, and optional scaling
- [ ] Detect identifiers, constant features, high cardinality, and leakage risks
- [ ] Return reusable preprocessing artifacts through an optional `ml` extra
- [ ] Do not train, rank, or evaluate machine-learning models

## v1.4.0: Power BI Ready profile

- [ ] Enforce consistent Power BI-compatible field types and names
- [ ] Validate keys and relationship cardinality
- [ ] Flatten supported nested records deterministically
- [ ] Generate an optional canonical date table
- [ ] Export validated CSV, Excel, and Parquet datasets with a readiness report
- [ ] Do not generate `.pbix` reports or dashboards

## Release quality requirements

- [ ] No caller-owned DataFrame mutation
- [ ] Deterministic output and ordering
- [ ] Idempotent transformations where the configured operation is idempotent
- [ ] Dry-run proposals match applied transformations
- [ ] Every destructive change is represented in the audit
- [ ] Public Python and CLI workflows remain backward compatible

## Completed foundation

The following milestones are released and remain supported.

### Agentic EDA Foundation

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

### Milestone 8: Controlled, Auditable Cleaning — Released in v1.0.0
- [x] Configurable missing-value marker detection
- [x] Column-level cleaning rules and dry-run previews
- [x] Structured before/after cleaning change logs
- [x] Unified profile → assess → fix → EDA workflow

### Milestone 9: Preparation and Feature Readiness — Released in v1.0.0
- [x] Reliable type and date conversion controls
- [x] Duplicate, outlier, text, and category preparation controls
- [x] Structured preparation reports

### Milestone 10: Validation and Contracts — Released in v1.0.0
- [x] Schema inference and expected-schema validation
- [x] Reusable quality rules with explicit pass/fail reports
- [x] Pipeline-friendly validation contracts

### Milestone 11: Production Workflows — Released in v1.0.0
- [x] `edf` command-line interface with JSON/YAML configuration
- [x] Batch and multi-file processing with structured logs and exit codes
- [x] Lightweight extension interface for supported custom steps

### Milestone 12: Stable API — Released in v1.0.0
- [x] Consolidated public API, formal result/report objects, and errors
- [x] Compatibility test suite and migration guidance for necessary breaks
- [x] Complete release verification

## Current release

EazyDataFix v1.0.0 is the current stable production release. The complete path
from data-quality foundations through controlled cleaning, preparation, data
contracts, Agentic EDA, reporting, and production CLI workflows is shipped.

The next release line follows the transformation-first milestones defined at
the top of this roadmap. Hackathon and user feedback will refine priorities
within those milestones without breaking the stable v1 API.
