# EazyDataFix 0.5.0 Release Notes

EazyDataFix 0.5.0 adds optional, evidence-cited AI narratives to completed
deterministic Agentic EDA workflows. Calculated metrics remain authoritative,
existing non-AI workflows remain unchanged, and no API key or AI dependency is
required unless the narrative feature is used.

## Optional grounded AI narratives

`edf.generate_agentic_eda_narrative(...)` converts a completed
`AgenticEDAResult` into a concise, business-facing narrative. Providers receive
an immutable compact evidence brief rather than the raw dataset, and every
claim must cite evidence IDs supplied by EazyDataFix.

```python
import eazydatafix as edf
from eazydatafix.narratives import OpenAINarrativeProvider

workflow = edf.run_agentic_eda("employees.csv")
provider = OpenAINarrativeProvider(model="your-openai-model")

narrative = edf.generate_agentic_eda_narrative(workflow, provider)

report = edf.export_agentic_eda_report(
    workflow,
    output_dir="eda-report",
    formats=["html", "json", "markdown"],
    narrative=narrative,
)
```

The narrative layer is provider-neutral. The built-in OpenAI Responses API
adapter is optional and installed through the `openai` extra.

## Grounding and integrity guardrails

- Every claim must cite supplied deterministic evidence.
- Unknown, duplicate, missing, or malformed citations are rejected.
- Invented numbers, unsupported causal language, and insufficient lexical
  support are rejected before a narrative result is returned.
- Evidence is immutable while a provider runs.
- A SHA-256 workflow fingerprint prevents a narrative generated for one
  workflow from being attached to another.
- HTML and Markdown reports include an evidence-reference section for human
  review.

These checks are deterministic guardrails, not proof that AI-written text is
semantically true. Narratives should still be reviewed before they are used for
decisions.

## Compatibility

- Python 3.10, 3.11, 3.12, and 3.13 are supported.
- No existing public APIs were removed or renamed.
- Deterministic EDA, reporting, notebook export, and approval checkpoints do
  not require an LLM or API key.
- Narrative generation does not rerun or modify the deterministic workflow.
- Caller-owned DataFrames remain unmodified.

## Install

```bash
pip install eazydatafix==0.5.0
```

Install the optional OpenAI adapter with:

```bash
pip install "eazydatafix[openai]==0.5.0"
```

Parquet support remains optional:

```bash
pip install "eazydatafix[parquet]==0.5.0"
```
