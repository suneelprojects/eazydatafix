from pathlib import Path

import pandas as pd

from eazydatafix.core.dataset_loader import DatasetLoader
from eazydatafix.models.data_contract import (
    ContractCheckResult,
    ContractValidationReport,
    DataContract,
    QualityRule,
    SchemaField,
)


class ContractEngine:
    """Infers and validates deterministic dataset schemas and quality rules."""

    def infer_schema(self, dataset: str | Path | pd.DataFrame) -> DataContract:
        """Infer deterministic field names, pandas dtypes, and nullability."""
        dataframe = DatasetLoader.load(dataset)
        fields = tuple(
            SchemaField(
                name=str(column),
                data_type=str(dataframe[column].dtype),
                nullable=bool(dataframe[column].isna().any()),
            )
            for column in dataframe.columns
        )
        return DataContract(fields=fields)

    def validate(
        self,
        dataset: str | Path | pd.DataFrame,
        contract: DataContract,
        rules: tuple[QualityRule, ...] = (),
    ) -> ContractValidationReport:
        """Validate an input against a contract and optional ordered quality rules."""
        dataframe = DatasetLoader.load(dataset)
        results: list[ContractCheckResult] = []
        expected = {field.name: field for field in contract.fields}

        for field in contract.fields:
            if field.name not in dataframe.columns:
                results.append(
                    ContractCheckResult("required_column", field.name, False, "Column is missing.")
                )
                continue
            actual_dtype = str(dataframe[field.name].dtype)
            results.append(
                ContractCheckResult(
                    "data_type",
                    field.name,
                    actual_dtype == field.data_type,
                    f"Expected {field.data_type}; found {actual_dtype}.",
                )
            )
            if not field.nullable:
                missing = int(dataframe[field.name].isna().sum())
                results.append(
                    ContractCheckResult(
                        "nullability",
                        field.name,
                        missing == 0,
                        f"{missing} missing value(s) found.",
                    )
                )

        if not contract.allow_extra_columns:
            for column in dataframe.columns:
                if column not in expected:
                    results.append(
                        ContractCheckResult(
                            "extra_column", str(column), False, "Column is not allowed."
                        )
                    )

        for rule in rules:
            results.append(self._evaluate_rule(dataframe, rule))

        ordered = tuple(results)
        return ContractValidationReport(
            contract=contract,
            results=ordered,
            passed=all(result.passed for result in ordered),
        )

    @staticmethod
    def _evaluate_rule(dataframe: pd.DataFrame, rule: QualityRule) -> ContractCheckResult:
        """Evaluate one explicit quality rule with an explanatory result."""
        if rule.column not in dataframe.columns:
            return ContractCheckResult(rule.name, rule.column, False, "Column is missing.")
        series = dataframe[rule.column]
        if rule.rule_type == "not_null":
            failures = int(series.isna().sum())
            return ContractCheckResult(
                rule.name, rule.column, failures == 0, f"{failures} null value(s)."
            )
        if rule.rule_type == "unique":
            failures = int(series.duplicated().sum())
            return ContractCheckResult(
                rule.name, rule.column, failures == 0, f"{failures} duplicate value(s)."
            )
        if not pd.api.types.is_numeric_dtype(series):
            return ContractCheckResult(
                rule.name, rule.column, False, "Rule requires a numeric column."
            )
        if rule.rule_type == "min":
            failures = int((series.dropna() < rule.value).sum())
            return ContractCheckResult(
                rule.name, rule.column, failures == 0, f"{failures} value(s) below {rule.value}."
            )
        failures = int((series.dropna() > rule.value).sum())
        return ContractCheckResult(
            rule.name, rule.column, failures == 0, f"{failures} value(s) above {rule.value}."
        )
