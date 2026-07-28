# Agentic EDA Deterministic Orchestrator

## Purpose

The orchestrator is the fourth deterministic stage of the Agentic EDA
pipeline. It composes existing engines and promotes their structured outputs
into traceable workflow decisions:

```text
dataset
  -> EDAEngine
  -> EDAPlanner
  -> EDAExecutor
  -> FollowUpDecisionEngine
  -> AgenticEDAResult
```

`eazydatafix.run_agentic_eda(dataset, config=None)` is the public façade. No
stage calls an LLM.

## Responsibilities

- `AgenticEDAOrchestrator` coordinates the existing EDA, planner, and executor
  components and preserves their outputs in the final result.
- `FollowUpDecisionEngine` reads successful step outputs and deterministically
  generates actions, visualisations, unresolved questions, and priority
  findings.
- `AgenticEDAConfig` validates three established analysis thresholds, two
  output toggles, and one recommendation limit.
- `AgenticEDAResult` retains all workflow stages, warnings, final status, and a
  deterministic summary.

The orchestrator does not calculate missingness, outliers, skewness,
correlations, class balance, or datetime statistics. Those calculations remain
owned by executor handlers.

## Configuration

Configuration intentionally stays small and stable:

- `correlation_threshold`: absolute correlation ratio in `(0, 1]`
- `outlier_iqr_multiplier`: positive IQR multiplier
- `class_imbalance_threshold`: dominant-class ratio in `(0, 1]`
- `enable_visualisation_recommendations`
- `enable_unresolved_questions`
- `max_recommendations_per_category`

The configured thresholds are passed to the existing deterministic handlers.
Default values preserve the standalone `execute_eda(...)` behaviour.

## Reliability and Traceability

- The datasource system supplies a copy of DataFrame inputs, so the workflow
  does not mutate caller-owned data.
- EDA results and plans are passed explicitly to the executor and validated by
  it against the supplied dataset.
- A safe handler failure remains a step-level failure. Decisions are generated
  only from successful step outputs, and the final status preserves
  `success`, `partial_failure`, or `failure`.
- Iteration follows planner and executor order. Priority findings use a stable
  high-to-low ordering.
- All recommendation records include type, target columns, reason, priority,
  source step, and prerequisites.

## JSON-ready Output

`AgenticEDAResult.to_dict()` recursively converts the complete workflow to
JSON-compatible native structures:

```text
{
  "eda_result": {...},
  "eda_plan": {...},
  "execution_result": {...},
  "follow_up_actions": [
    {
      "type": "outlier_review",
      "target_columns": ["salary"],
      "reason": "...",
      "priority": "medium",
      "source_step": "outlier_analysis",
      "prerequisites": [
        "Use the configured IQR multiplier of 1.5.",
        "Confirm domain-valid ranges."
      ]
    }
  ],
  "unresolved_questions": [...],
  "recommended_visualisations": [
    {
      "type": "box_plot",
      "target_columns": ["salary"],
      "reason": "...",
      "priority": "medium",
      "source_step": "outlier_analysis",
      "prerequisites": ["Numeric values are available."]
    }
  ],
  "priority_findings": [...],
  "workflow_warnings": [],
  "deterministic_final_summary": "...",
  "overall_status": "success"
}
```

The structure is intended for API responses, audit logs, notebooks, and future
presentation layers without hidden runtime state.
