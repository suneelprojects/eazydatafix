# 🛠️ EasyDataFix

> A modern Python library for **data quality assessment, validation, and automated data cleaning**.

EasyDataFix helps data analysts, data scientists, machine learning engineers, and ETL developers quickly identify data quality issues and generate professional reports with just a few lines of code.

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
pip install easydatafix
```

---

# Quick Start

```python
import easydatafix as edf

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

EasyDataFix can generate reports in multiple formats.

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

# Why EasyDataFix?

EasyDataFix is designed to make data quality assessment simple and accessible.

Whether you're validating datasets before machine learning, preparing ETL pipelines, or cleaning business reports, EasyDataFix provides a consistent way to measure and improve data quality.

---

# Roadmap

### Version 0.1

- Assessment Engine
- Validation Engine
- Recommendation Engine
- Reporting Engine
- Auto Fix Foundation

### Version 0.2

- Data Profiling
- CLI Support
- Streamlit Dashboard
- SQL Support
- Apache Spark Support
- Interactive Charts
- AI Recommendations

---

# Contributing

Contributions are welcome.

Feel free to fork the repository, open issues, or submit pull requests.

Repository:

https://github.com/suneelprojects/easydatafix

---

# License

MIT License

---

Made with ❤️ by **Suneel Kumar Kola**
