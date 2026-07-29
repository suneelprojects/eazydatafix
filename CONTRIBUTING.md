# Contributing to EazyDataFix

## Welcome

Thank you for considering a contribution to EazyDataFix. Contributions can
include:

- Bug fixes
- Tests
- Documentation
- Examples
- Data-quality rules
- Deterministic EDA improvements
- Reporting improvements
- Performance improvements
- Issue investigation

Not every proposal will fit the project, but focused issues and pull requests
make ideas easier to evaluate and review.

## Before contributing

Before starting work:

- Search existing [issues](https://github.com/suneelprojects/eazydatafix/issues)
  and
  [pull requests](https://github.com/suneelprojects/eazydatafix/pulls).
- Open an issue, or comment on an existing one, before beginning a large
  change.
- Keep each contribution focused on one objective.
- Avoid combining refactoring with unrelated features or fixes.
- Never commit private, confidential, or personally identifiable datasets.
- Use anonymised or synthetic datasets in tests, examples, and bug reports.

## Development setup

EazyDataFix requires Python 3.10 or later and is tested with Python 3.10–3.13.
Clone the repository and create an isolated environment:

```bash
git clone https://github.com/suneelprojects/eazydatafix.git
cd eazydatafix
python -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
python -m pip install pytest ruff black build
```

On Windows PowerShell, activate the environment with:

```powershell
venv\Scripts\Activate.ps1
```

On Windows Command Prompt, use:

```bat
venv\Scripts\activate.bat
```

The editable installation uses the package configuration in `pyproject.toml`.
For work that specifically requires Parquet support, install the existing
optional extra:

```bash
python -m pip install -e ".[parquet]"
```

The project does not currently define a combined development dependency extra,
so the test, lint, formatting, and build tools are installed explicitly.

## Branch workflow

Start from the latest `develop` branch. Do not develop directly on `main`, and
keep one clear objective per branch.

```bash
git checkout develop
git pull origin develop
git checkout -b <branch-name>
```

Use a short branch name that communicates the scope. For example:

```text
feature/notebook-export
fix/parquet-validation
docs/contributing-guide
test/agentic-eda-edge-cases
refactor/report-renderer
```

## Coding expectations

- Preserve deterministic behaviour.
- Do not introduce hidden LLM dependencies into deterministic workflows.
- Do not mutate caller-owned DataFrames unless the behaviour is explicit and
  documented.
- Maintain backward compatibility where reasonably possible.
- Add type hints to public and internal APIs where consistent with the
  codebase.
- Prefer small, composable functions with focused responsibilities.
- Add docstrings where they improve maintainability.
- Avoid unrelated formatting changes.
- Do not fabricate metrics, benchmarks, or supported capabilities.
- Document public API changes.

Follow the existing package structure and reuse existing engines, models, and
utilities before introducing new abstractions or dependencies.

## Testing and validation

Add tests for new behaviour and regression tests for bug fixes. Where relevant,
cover normal use, boundaries, invalid input, deterministic repetition, and
non-mutation of caller-owned DataFrames.

Run the complete test suite:

```bash
python -m pytest
```

The repository also configures Ruff, Black, and package builds. Before opening
a pull request, run:

```bash
ruff check .
black --check .
git diff --check
python -m build
```

The repository does not currently configure a type checker or a required
coverage command. Do not substitute a partial test selection for the complete
suite when preparing a pull request.

## Documentation

Update documentation when a change affects user behaviour, public APIs,
installation, outputs, supported capabilities, or planned milestones. Depending
on the contribution, the appropriate location may be:

- [`README.md`](README.md) for primary workflows and visitor-facing guidance
- The [documentation website](https://eazydatafix.com/docs) for detailed usage
- API documentation for public signatures, return values, and behaviour
- [`CHANGELOG.md`](CHANGELOG.md) for notable released changes
- [`ROADMAP.md`](ROADMAP.md) for approved milestone changes
- Examples when users benefit from a runnable demonstration

Not every contribution needs to update every document. Keep documentation
changes proportional to the contribution.

## Commit guidance

Use concise, action-oriented commit messages. Conventional-style prefixes are
recommended for readability but are not technically enforced by the
repository.

```text
fix: preserve boolean columns during EDA
feat: add notebook export
docs: improve installation guide
test: cover empty DataFrame handling
refactor: simplify report rendering
```

Keep commits focused and avoid including generated reports, build artifacts,
virtual environments, credentials, or personal datasets.

## Pull-request checklist

Before submitting a pull request, confirm:

- [ ] The branch has one focused objective.
- [ ] Tests were added or updated for changed behaviour.
- [ ] The complete test suite passes.
- [ ] Documentation was updated where required.
- [ ] No private datasets, credentials, generated reports, or build artifacts
      are included.
- [ ] No unrelated code or formatting changes are included.
- [ ] Backward compatibility was considered.
- [ ] Public API changes are documented.
- [ ] DataFrame mutation behaviour was verified.
- [ ] Deterministic results were preserved.

In the pull-request description, explain the problem, the chosen approach,
user-visible or developer-visible impact, compatibility considerations, and the
commands used for validation.

## Bug reports

Use [GitHub Issues](https://github.com/suneelprojects/eazydatafix/issues) and
include:

- EazyDataFix version
- Python version
- Operating system
- Installation method
- A minimal reproducible example
- Expected behaviour
- Actual behaviour
- The full traceback
- A sanitised dataset structure or small synthetic sample when data is needed

Remove credentials, private values, and personally identifiable information
before posting.

## Feature requests

Feature requests should explain:

- The problem being solved
- The current workaround
- The proposed behaviour
- Example usage
- The expected benefit
- Whether the proposal affects public APIs or deterministic behaviour

Open a focused
[GitHub issue](https://github.com/suneelprojects/eazydatafix/issues) before
building a large feature so the scope and architectural fit can be discussed.

## Security issues

Do not disclose vulnerabilities or sensitive exploit details in a public issue
or pull request. The repository does not currently document a dedicated private
security-reporting channel. Contact the maintainer through an available private
contact method on the
[repository owner's GitHub profile](https://github.com/suneelprojects), and
share only the information needed to coordinate a private report.

## Code of Conduct

Participation in EazyDataFix requires following the
[`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md).

## Licence

By submitting a contribution, you agree that it is provided under the
project's [MIT Licence](LICENSE).
