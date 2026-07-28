# Easy Data Fix Roadmap

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

### Next Milestone: Grounded Presentation and Export
- [ ] Notebook and visualisation artifact export
- [ ] Optional LLM narratives grounded exclusively in deterministic metrics
- [ ] Human approval checkpoints for domain-dependent decisions

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
