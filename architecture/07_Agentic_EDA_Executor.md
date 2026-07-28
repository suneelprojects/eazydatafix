# Agentic EDA Deterministic Executor

## Purpose

The executor is the third deterministic stage of the Agentic EDA pipeline:

1. `eazydatafix.eda(dataset)` calculates reusable dataset facts.
2. `eazydatafix.plan_eda(result)` selects and explains follow-up analyses.
3. `eazydatafix.execute_eda(dataset, result, plan)` executes only selected steps.

No stage calls an LLM.

## Components

- `EDAExecutor` validates inputs, preserves plan order, checks dependencies, and
  records step-level outcomes.
- `EDAAnalysisHandler` defines the contract for deterministic execution tools.
- Quality handlers cover missing values, duplicates, and identifier exclusion.
- Numeric handlers cover distributions, IQR outliers, skewness, and correlation.
- Categorical handlers cover category, boolean, and class distributions.
- The datetime handler covers parsing, range, and year/month frequencies.
- `EDAExecutionResult` retains the EDA result and plan alongside execution
  records, warnings, order, summary, and overall status.

## Reliability

An explicitly supplied `EDAResult` is checked against dataset shape, column
order, missing counts, duplicate count, and unique-value counts. A global
mismatch raises an error because executing that result would be unsafe.

Missing required columns, failed dependencies, unknown handlers, and safe
handler exceptions are recorded as failed steps. Remaining independent steps
continue. The loader and handlers operate on copies and do not mutate the
caller’s DataFrame.

## Output Structure

`EDAExecutionResult.to_dict()` produces a JSON-ready structure:

```text
{
  "eda_result": {...},
  "eda_plan": {...},
  "executed_steps": [
    {
      "name": "outlier_analysis",
      "status": "success",
      "reason": "...",
      "priority": "medium",
      "required_columns": ["age", "salary"],
      "dependencies": ["numeric_distribution_analysis"],
      "output": {
        "iqr_multiplier": 1.5,
        "columns": {
          "salary": {
            "lower_bound": 12000.0,
            "upper_bound": 108000.0,
            "outlier_count": 1,
            "outlier_percentage": 2.5
          }
        }
      },
      "error": null
    }
  ],
  "skipped_steps": [...],
  "execution_order": [...],
  "warnings": [...],
  "deterministic_summary": "...",
  "status": "success"
}
```

Step outputs contain native values, lists, and dictionaries so they can be
serialised and reproduced without hidden runtime state.
