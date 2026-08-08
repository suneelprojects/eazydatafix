from dataclasses import asdict, dataclass


@dataclass(frozen=True, slots=True)
class SchemaField:
    """Defines one expected dataset column for a deterministic data contract."""

    name: str
    data_type: str
    nullable: bool = True


@dataclass(frozen=True, slots=True)
class DataContract:
    """Defines expected columns, data types, and extra-column policy."""

    fields: tuple[SchemaField, ...]
    allow_extra_columns: bool = True


@dataclass(frozen=True, slots=True)
class QualityRule:
    """Defines a reusable deterministic column quality rule."""

    name: str
    column: str
    rule_type: str
    value: float | None = None

    def __post_init__(self) -> None:
        """Validate supported quality-rule definitions."""
        if self.rule_type not in {"not_null", "unique", "min", "max"}:
            raise ValueError("rule_type must be one of: not_null, unique, min, max.")
        if self.rule_type in {"min", "max"} and self.value is None:
            raise ValueError(f"{self.rule_type} rules require a numeric value.")


@dataclass(frozen=True, slots=True)
class ContractCheckResult:
    """Represents one pass/fail data-contract or quality-rule evaluation."""

    name: str
    column: str | None
    passed: bool
    message: str


@dataclass(frozen=True, slots=True)
class ContractValidationReport:
    """Contains deterministic contract results suitable for pipeline decisions."""

    contract: DataContract
    results: tuple[ContractCheckResult, ...]
    passed: bool

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-ready representation with stable result ordering."""
        return {
            "passed": self.passed,
            "contract": {
                "allow_extra_columns": self.contract.allow_extra_columns,
                "fields": [asdict(field) for field in self.contract.fields],
            },
            "results": [asdict(result) for result in self.results],
        }
