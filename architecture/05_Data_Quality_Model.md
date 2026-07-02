# Easy Data Fix - Data Quality Model

## Overview

Easy Data Fix evaluates datasets using measurable Data Quality Dimensions.

Each dimension contributes to an Overall Data Quality Score.

The goal is not only to detect issues but also to measure data quality objectively.

---

# Overall Quality Score

Score Range

0 – 100

Grade

A+ : 98–100

A : 90–97

B : 80–89

C : 70–79

D : Below 70

---

# Data Quality Dimensions

## 1. Completeness

Measures missing or empty values.

Examples

* Missing values
* Empty rows
* Empty columns

Weight (v1)

25%

---

## 2. Uniqueness

Measures duplicate information.

Examples

* Duplicate rows
* Duplicate columns
* Duplicate primary keys

Weight

20%

---

## 3. Consistency

Measures formatting consistency.

Examples

* Mixed date formats
* Mixed text capitalization
* Leading/trailing spaces
* Different representations of the same value

Weight

20%

---

## 4. Validity

Measures whether values satisfy expected rules.

Examples

* Invalid emails
* Invalid phone numbers
* Invalid dates
* Invalid numeric ranges

Weight

20%

---

## 5. Structure

Measures structural quality.

Examples

* Incorrect column names
* Wrong data types
* Unexpected schema

Weight

15%

---

# Assessment Output

The framework should produce:

Overall Quality Score

Overall Grade

Dimension Scores

Recommendations

Estimated Improvement Score

---

# Example Report

Overall Data Quality

91 / 100

Grade

A

Dimension Scores

Completeness

98

Uniqueness

94

Consistency

87

Validity

92

Structure

84

Recommendations

✓ Remove duplicate rows

✓ Standardize dates

✓ Convert Salary to numeric

✓ Trim whitespace

Estimated Score After Improvements

98 / 100

Grade A+

---

# Design Principles

* Every score must be explainable.
* Every recommendation must map to a measurable issue.
* Users should understand how the score was calculated.
* Scores should improve after approved fixes are applied.

