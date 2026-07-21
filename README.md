# 🛠️ EazyDataFix

[![PyPI version](https://img.shields.io/pypi/v/eazydatafix)](https://pypi.org/project/eazydatafix/)
[![Python Versions](https://img.shields.io/pypi/pyversions/eazydatafix)](https://pypi.org/project/eazydatafix/)
[![License](https://img.shields.io/github/license/suneelprojects/eazydatafix)](LICENSE)
[![Downloads](https://img.shields.io/pypi/dm/eazydatafix)](https://pypi.org/project/eazydatafix/)
[![GitHub Release](https://img.shields.io/github/v/release/suneelprojects/eazydatafix)](https://github.com/suneelprojects/eazydatafix/releases)
[![GitHub Stars](https://img.shields.io/github/stars/suneelprojects/eazydatafix?style=social)](https://github.com/suneelprojects/eazydatafix)

> A modern Python library for **data quality assessment, validation, and automated data cleaning**.

EazyDataFix helps data analysts, data scientists, machine learning engineers, and ETL developers quickly identify data quality issues and generate professional reports with just a few lines of code.

---

# 🌐 Documentation

📚 **Documentation Website**

https://eazydatafix.com

📖 **API Reference**

https://eazydatafix.com/docs

---

# 🚀 Quick Links

- 📦 PyPI — https://pypi.org/project/eazydatafix/
- 🌍 Documentation — https://eazydatafix.com
- 📖 API Reference — https://eazydatafix.com/docs
- 💻 GitHub — https://github.com/suneelprojects/eazydatafix

---

## ✨ Features

- 📊 Data Quality Assessment
- ✅ Missing Value Detection
- 🔍 Duplicate Detection
- ✔️ Data Validation
- 🧹 Data Consistency Checks
- 🎯 Data Accuracy Checks
- ⏱️ Timeliness Checks
- 💡 Intelligent Recommendations
- 📄 Console Report
- 🌐 HTML Report
- 📑 PDF Report
- 📈 Excel Report
- 📋 CSV Report
- 📦 JSON Report
- 📝 Markdown Report

---

# Installation

```bash
pip install eazydatafix
```

For Parquet support:

```bash
pip install eazydatafix[parquet]
```

---

# Core APIs

```python
import eazydatafix as edf

edf.profile(...)

edf.assess(...)

edf.fix(...)

edf.analysis_ready(...)
```

---

# Quick Start

```python
import eazydatafix as edf

report = edf.assess("employees.csv")

report.summary()

report.to_html()

report.to_pdf()

report.to_excel()

report.to_json()

report.to_csv()

report.to_markdown()
```

---

# Example Console Output

```
======================================================================
                       🛠️ EASY DATA FIX REPORT
======================================================================

Overall Score : 90.37

Grade         : A

Completeness  : 96.97%

Uniqueness    : 100.00%

Validity      : 55.00%

Consistency   : 100.00%

Accuracy      : 100.00%

Timeliness    : 100.00%
```

---

# Supported Quality Dimensions

| Dimension | Status |
|-----------|--------|
| Completeness | ✅ |
| Uniqueness | ✅ |
| Validity | ✅ |
| Consistency | ✅ |
| Accuracy | ✅ |
| Timeliness | ✅ |

---

# Report Formats

EazyDataFix can generate reports in multiple formats.

```python
report.summary()

report.to_html()

report.to_pdf()

report.to_excel()

report.to_json()

report.to_csv()

report.to_markdown()
```

---

# Supported Data Sources

EazyDataFix accepts datasets in a variety of formats.

Both `edf.assess(...)` and `edf.fix(...)` work with:

- Pandas `DataFrame`
- CSV files
- Excel files (`.xlsx` / `.xls`)
- JSON files
- Parquet files

Loading is handled by the modular `eazydatafix.datasources` package, allowing custom data source plugins.

```python
import pandas as pd

from eazydatafix.datasources import (
    DataSource,
    default_registry,
)


class TSVDataSource(DataSource):

    name = "tsv"

    def can_load(self, source):
        from pathlib import Path
        return isinstance(source, Path) and source.suffix.lower() == ".tsv"

    def load(self, source):
        return pd.read_csv(source, sep="\t")


default_registry.register(TSVDataSource())

# edf.assess(...) and edf.fix(...) now support TSV files.
```

---

# Why EazyDataFix?

EazyDataFix is designed to make data quality assessment simple and accessible.

Whether you're validating datasets before machine learning, preparing ETL pipelines, or cleaning business reports, EazyDataFix provides a consistent way to measure and improve data quality with minimal code.

---

# Roadmap

## ✅ Completed

- Assessment Engine
- Validation Engine
- Recommendation Engine
- Reporting Engine
- Auto Fix Foundation

## 🚀 Coming Soon

- Data Profiling
- CLI Support
- Streamlit Dashboard
- SQL Support
- Apache Spark Support
- Interactive Charts
- AI Recommendations

---

# Contributing

Contributions are always welcome.

Feel free to:

- ⭐ Star the repository
- 🐛 Report bugs
- 💡 Suggest features
- 🔧 Submit pull requests

GitHub Repository:

https://github.com/suneelprojects/eazydatafix

Documentation:

https://eazydatafix.com

---

# License

MIT License

---

Made with ❤️ by **Suneel Kumar Kola**

🌐 https://eazydatafix.com
