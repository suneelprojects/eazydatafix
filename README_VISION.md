# Why Easy Data Fix Exists

## The Problem

Every Data Scientist, Data Analyst and Data Engineer spends a significant amount of time preparing data before analysis.

Typical workflow:

- Read CSV
- Check missing values
- Remove duplicates
- Fix data types
- Validate emails
- Validate phone numbers
- Standardize dates
- Handle outliers
- Generate reports

Most people rewrite the same code for every project.

Easy Data Fix exists to eliminate this repetitive work.

---

# Mission

Make dataset preparation effortless.

Instead of writing hundreds of lines of pandas code, users should be able to write:

```python
import easydatafix as edf

report = edf.assess("sales.csv")
report.summary()

result = edf.fix("sales.csv")

result.summary()
```

---

# Vision

Become the most developer-friendly open-source framework for dataset quality assessment and automated cleaning.

---

# Philosophy

Simple API.

Powerful engine.

Extensible architecture.

Production-ready quality.

---

# Success Metric

A user should be productive within five minutes of installing Easy Data Fix.

If we achieve that, we've succeeded.

---

# Long-Term Goal

Easy Data Fix should become the standard preprocessing library that developers install before starting any data science project.
