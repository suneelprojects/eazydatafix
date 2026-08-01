# EazyDataFix 0.4.0 Release Notes

EazyDataFix 0.4.0 adds reproducible Jupyter Notebook export and explicit human
approval checkpoints to the deterministic Agentic EDA workflow. These features
remain LLM-free, preserve existing public APIs, and support Python 3.10–3.13.

## Deterministic Jupyter Notebook export

`edf.export_agentic_eda_notebook(...)` converts an existing
`AgenticEDAResult` into an unexecuted, ready-to-run notebook-format v4 file.
The notebook contains stable Markdown and executable code cells for dataset
loading, understanding, planning, execution, orchestration, findings,
recommendations, unresolved questions, and report export.

Notebook documents are generated as deterministic JSON using the Python
standard library, so Jupyter and `nbformat` are not required runtime
dependencies. File-based datasets use portable path references. DataFrame
inputs generate a deterministic JSON companion dataset beside the notebook,
allowing the exported notebook to execute independently without mutating the
caller-owned DataFrame.

```python
import eazydatafix as edf

workflow = edf.run_agentic_eda("employees.csv")
notebook = edf.export_agentic_eda_notebook(
    workflow,
    dataset="employees.csv",
    output_path="agentic-eda.ipynb",
)

print(notebook.generated_files)
```

The JSON-ready `AgenticEDANotebookResult` reports the notebook path, generated
companion files, cell count, notebook format version, and export status.

## Human Approval Checkpoints

The new two-phase approval workflow separates deterministic understanding and
planning from analysis execution:

- `edf.prepare_agentic_eda_approval(...)` creates a pending checkpoint without
  executing analysis steps.
- `edf.approve_agentic_eda_plan(...)` approves all selected steps or an
  explicit subset.
- `edf.reject_agentic_eda_plan(...)` records an explicit rejection that cannot
  be resumed.
- `edf.resume_agentic_eda(...)` executes only an approved plan and returns the
  existing `AgenticEDAResult` type.

```python
checkpoint = edf.prepare_agentic_eda_approval("employees.csv")

# Review checkpoint.eda_result and checkpoint.eda_plan.
approved = edf.approve_agentic_eda_plan(
    checkpoint,
    approved_step_ids=None,
    reviewer="Data owner",
    notes="Approved for deterministic execution",
)

workflow = edf.resume_agentic_eda("employees.csv", approved)
```

Subset approval is constrained to steps selected by the original planner.
Unknown, duplicate, skipped, and unplanned IDs fail clearly. Dependencies must
be approved explicitly; incomplete subsets fail before execution and no
additional steps are approved implicitly.

Each frozen, JSON-ready `AgenticEDAApprovalCheckpoint` contains copied dataset
understanding, the original plan, configuration, ordered decisions, reviewer
metadata, and deterministic summaries. SHA-256 fingerprints protect the
dataset and complete checkpoint decision state. Resume rejects changed
datasets, modified snapshots, approval-field tampering, and pending or rejected
checkpoints while reusing the stored understanding and approved plan.

The existing `edf.run_agentic_eda(...)` one-call workflow remains unchanged for
users who do not need an approval gate.

## Install

```bash
pip install eazydatafix==0.4.0
```

Parquet support remains optional:

```bash
pip install "eazydatafix[parquet]==0.4.0"
```

## Compatibility

- Python 3.10, 3.11, 3.12, and 3.13 are supported.
- No existing public APIs were removed or renamed.
- Notebook and approval workflows preserve caller-owned DataFrames.
- Notebook export remains compatible with existing deterministic report
  export.
