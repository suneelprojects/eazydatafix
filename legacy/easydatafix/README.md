# easydatafix 0.3.0

This is the last release of the PyPI project **easydatafix** (0.1.0 and 0.2.0).
It is a compatibility shim. The maintained library is
[eazydatafix](https://pypi.org/project/eazydatafix/).

```bash
pip install eazydatafix
```

```python
import eazydatafix as edf
```

Importing `easydatafix` installs and imports `eazydatafix`, then emits a
`DeprecationWarning` that points at `eazydatafix`. Python hides
`DeprecationWarning` from imported modules by default, so this package enables
that warning for its own message. Attribute access, including
`from easydatafix import PipelineRecipe`, is forwarded to `eazydatafix`.
`easydatafix.__version__` stays `0.3.0`. The forwarded library version is
`easydatafix.__eazydatafix_version__`.

There will not be an `easydatafix` 0.4.0.

## Publish this package manually

The repository publish workflow builds and uploads **eazydatafix** only. It
does not publish this directory. Trusted publishing on that workflow is for
the `eazydatafix` PyPI project. Uploading `easydatafix` needs credentials that
can publish to the existing `easydatafix` project, such as an API token for
that project.

From a machine that already has those credentials:

```bash
cd legacy/easydatafix
python -m pip install --upgrade build twine
python -m build
python -m twine check dist/*
python -m pip install dist/easydatafix-0.3.0-py3-none-any.whl
python -W default -c "import easydatafix"
python -m twine upload dist/*
```

Check the warning in a clean environment before uploading. After a successful
upload, 0.3.0 is the latest `easydatafix` release and depends on
`eazydatafix>=2.0.0,<3`. Leave 0.1.0 and 0.2.0 in place so existing pins keep
installing. Yanking them is a separate decision and will break those pins.

Do not run the root `Publish to PyPI` workflow for this package, and do not
change `eazydatafix/_version.py` just to publish the shim.
