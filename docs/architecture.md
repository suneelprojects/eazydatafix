# Easy Data Fix Architecture

## Vision

Easy Data Fix is an open-source Python framework that helps data professionals assess, validate, clean, and improve datasets with minimal code.

Our goal is to make dataset preparation as simple as:

```python
import easydatafix as edf

report = edf.assess("employees.csv")
report.summary()

result = edf.fix("employees.csv")

result.summary()
result.to_csv("employees_clean.csv")
```

---

# Design Principles

The framework follows these principles:

- Simple public API
- Modular architecture
- Plugin-based design
- Extensible components
- Consistent object-oriented API
- Production-ready code quality

---

# Public API

```python
edf.profile(...)
edf.assess(...)
edf.fix(...)
```

Each function returns a rich object instead of primitive values.

| Function | Returns |
|----------|----------|
| profile() | DatasetProfile |
| assess() | AssessmentReport |
| fix() | FixResult |

---

# Core Components

Easy Data Fix consists of six major modules.

```
Dataset Profiler
        │
        ▼
Assessment Engine
        │
        ▼
Validation Engine
        │
        ▼
Recommendation Engine
        │
        ▼
Fix Engine
        │
        ▼
Reporting
```

---

# Folder Structure

```
easydatafix/

assessment/
checks/

contracts/

core/

enums/

fix/

models/

recommendations/

rendering/

validation/
```

---

# Assessment Flow

```
CSV

↓

Read DataFrame

↓

Assessment Checks

↓

Quality Score

↓

Recommendations

↓

AssessmentReport
```

---

# Validation Flow

```
Assessment

↓

Validation Rules

↓

ValidationResult

↓

AssessmentReport
```

---

# Fix Flow

```
CSV

↓

Read DataFrame

↓

Before Assessment

↓

Fix Strategies

↓

Clean DataFrame

↓

After Assessment

↓

FixResult
```

---

# Plugin Architecture

Every assessment module implements:

```
Check
```

Every cleaning module implements:

```
FixStrategy
```

Future modules should integrate without changing the framework core.

---

# Development Philosophy

Every new feature should satisfy three questions.

1. Is it useful?
2. Is it extensible?
3. Is it easy to understand?

If not, redesign it.

---

# Roadmap

## v0.1

- Dataset Profiling
- Assessment
- Validation
- Recommendations
- Console Reports

## v0.2

- Automatic Cleaning
- Smart Fix Strategies
- CLI

## v0.3

- HTML Reports
- JSON Reports
- Markdown Reports

## v0.4

- AI Recommendations
- AI Cleaning

## v1.0

- Stable Release
- PyPI
- Documentation
- Website
- Enterprise Foundation
