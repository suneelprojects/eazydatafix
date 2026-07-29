# EazyDataFix 0.3.0 Release Notes

EazyDataFix 0.3.0 introduces a complete deterministic Agentic EDA workflow:
understand a dataset, plan applicable analyses, execute them reproducibly,
generate traceable follow-up decisions, and export human-readable reports.
No LLM is required.

## Highlights

- `edf.eda(...)` produces structured exploratory analysis with semantic column
  roles and identifier-aware numeric statistics.
- `edf.plan_eda(...)` explains which follow-up analyses should run and why.
- `edf.execute_eda(...)` executes selected analyses through deterministic,
  failure-isolated handlers.
- `edf.run_agentic_eda(...)` combines understanding, planning, execution, and
  follow-up decisions into one JSON-ready result.
- `edf.export_agentic_eda_report(...)` creates standalone HTML, stable JSON,
  optional Markdown, and deterministic PNG visualisations.
- Shared dataset validation prevents workflow results from being used with a
  mismatched dataset.
- DataFrame inputs are copied and are not mutated by EDA, execution,
  orchestration, or reporting.
- Python 3.10–3.13 is supported and tested.

## Install

```bash
pip install eazydatafix==0.3.0
```

Parquet support remains optional:

```bash
pip install "eazydatafix[parquet]==0.3.0"
```

## Quick example

```python
import eazydatafix as edf

workflow = edf.run_agentic_eda("employees.csv")
report = edf.export_agentic_eda_report(
    workflow,
    dataset="employees.csv",
    output_dir="eda-report",
)

print(workflow.deterministic_final_summary)
print(report.generated_files)
```

## Upgrade notes

Version 0.3.0 does not remove or rename existing public APIs. Report
histograms and box plots require the optional original dataset because raw
observations are intentionally not reconstructed from summary statistics.

EazyDataFix 0.3.0 is available through GitHub Releases.
