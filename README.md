## Easy Data Fix

Easy Data Fix provides deterministic data profiling, assessment, cleaning, and
exploratory data analysis for pandas datasets and supported files.

## Deterministic EDA

Generate a structured exploratory data analysis result without using an LLM.

```python
import easydatafix as edf

eda_result = edf.eda("employees.csv")

print(eda_result.shape)
print(eda_result.numeric_statistics)
print(eda_result.observations)
print(eda_result.recommendations)
```

`edf.eda(...)` accepts pandas DataFrames, CSV, Excel, JSON, and Parquet files.
