# Agentic EDA Roadmap

## Foundation: Deterministic EDA

The first Agentic EDA milestone is deterministic. `easydatafix.eda(...)` loads a
supported dataset and returns structured metrics, observations, and
recommendations without calling an LLM.

The foundation provides:

- Dataset shape, columns, and data types
- Missing-value and duplicate-row summaries
- Numeric descriptive statistics and correlations
- Categorical summaries and unique-value counts
- Deterministic observations and recommendations

## Next Milestone: Tool-Driven Analysis

The next phase will define tools that can inspect deterministic EDA results,
request focused follow-up analysis, and create reproducible analysis plans.

## Future Milestone: LLM Narratives

LLM-generated explanations will be optional and will use the deterministic EDA
result as their source of truth. No LLM output will replace calculated metrics.
