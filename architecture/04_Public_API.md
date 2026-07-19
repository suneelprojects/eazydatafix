# Easy Data Fix Public API

## Design Philosophy

The public API should be:

* Easy to learn
* Easy to read
* Difficult to misuse
* Consistent
* Predictable

Users should never interact with internal modules.

---

# Framework Entry Point

```python
import eazydatafix as edf
```

---

# Assessment

```python
report = edf.assess("employees.csv")
```

Returns an AssessmentReport object.

---

# Assessment Report

```python
report.summary()

report.show()

report.quality_score()

report.recommend()

report.export("assessment.html")
```

---

# Improvement

```python
clean_df = report.apply()
```

or

```python
clean_df = report.apply(
    duplicates=True,
    missing_values=True,
    datatypes=True,
    dates=True,
    text=True
)
```

---

# Validation

```python
validation = edf.validate(clean_df)
```

---

# Validation Report

```python
validation.summary()

validation.show()

validation.export("validation.html")
```

---

# File Support

```python
edf.assess("employees.csv")

edf.assess("employees.xlsx")

edf.assess("employees.parquet")
```

Future versions may support databases and cloud storage.

---

# AI Assistant (Future)

```python
assistant = edf.ai()

assistant.explain(report)

assistant.suggest()

assistant.generate_code()
```

---

# Plugin System (Future)

```python
edf.install_plugin("gst-validator")

edf.install_plugin("medical-record-validator")
```

---

# API Design Principles

* Readable
* Discoverable
* Consistent naming
* Minimal parameters
* Strong defaults
* Explicit over implicit
* Beginner-friendly
* Enterprise-ready

