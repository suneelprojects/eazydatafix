# EazyDataFix Development Instructions

## About the Project

EazyDataFix is a Python library that helps users assess, clean, prepare, and validate datasets for analytics, machine learning, business intelligence, and AI.

## Architecture Principles

- Reuse existing classes whenever possible.
- Do not duplicate engines.
- Keep public APIs backward compatible.
- Prefer composition over inheritance.
- Keep code modular and maintainable.

## Coding Standards

- Follow the existing folder structure.
- Add type hints to public APIs.
- Add docstrings to all public classes and methods.
- Use descriptive variable names.
- Keep functions focused on a single responsibility.

## Testing

- Add unit tests for all new functionality.
- Do not break existing tests.
- Preserve backward compatibility.

## Important

- Do not introduce unnecessary dependencies.
- Before implementing a feature, analyze the existing architecture.
- Reuse AssessmentEngine, FixEngine, and PrepareEngine whenever applicable.
- When modifying existing files, preserve existing functionality unless explicitly instructed.
