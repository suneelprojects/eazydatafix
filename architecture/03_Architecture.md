# Easy Data Fix Framework Architecture

## Overview

Easy Data Fix is an open-source Data Quality Framework designed around a pipeline architecture.

The framework follows a structured lifecycle that transforms raw data into trusted, validated data.

---

# Framework Lifecycle

Raw Dataset

↓

Assessment Engine

↓

Recommendation Engine

↓

Improvement Engine

↓

Validation Engine

↓

Reporting Engine

↓

Trusted Dataset

---

# Core Engines

## 1. Assessment Engine

Purpose

Evaluate the quality of incoming datasets.

Responsibilities

* Dataset profiling
* Dataset summary
* Duplicate detection
* Missing value analysis
* Data type analysis
* Date detection
* Text consistency analysis
* Initial quality scoring

Output

Assessment Report

---

## 2. Recommendation Engine

Purpose

Recommend actions without modifying the dataset.

Responsibilities

* Identify issues
* Suggest fixes
* Estimate impact
* Explain recommendations

Output

Recommendation Report

---

## 3. Improvement Engine

Purpose

Apply approved transformations.

Responsibilities

* Remove duplicates
* Handle missing values
* Standardize text
* Fix data types
* Normalize dates
* Rename columns
* Other approved improvements

Output

Improved Dataset

---

## 4. Validation Engine

Purpose

Verify that improvements were successful.

Responsibilities

* Recalculate quality score
* Validate schema
* Compare before/after
* Detect remaining issues

Output

Validation Report

---

## 5. Reporting Engine

Purpose

Generate human-readable reports.

Responsibilities

* Summary
* Quality score
* Improvements applied
* Remaining issues
* Export to HTML
* Export to JSON
* Export to PDF

Output

Final Data Quality Report

---

# Design Principles

* Single Responsibility Principle
* Modular architecture
* Extensible plugin system
* Explainable recommendations
* Transparent transformations
* Beginner-friendly API
* Enterprise-ready architecture

---

# Public Workflow

```python
import easydatafix as edf

report = edf.assess("employees.csv")

report.summary()

report.recommend()

clean_df = report.apply()

validation = edf.validate(clean_df)

validation.export("report.html")
```

---

# Long-Term Vision

Easy Data Fix will evolve into a complete Data Quality Platform consisting of:

* Python Framework
* CLI
* REST API
* Web Application
* Jupyter Extension
* VS Code Extension
* AI Recommendation Engine
* Enterprise Edition

