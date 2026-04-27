# Publishing

## Important Naming Note

The package name `agentcheck` is already taken on PyPI.

This project is currently prepared to publish as:

- distribution name: `agentcheck-behavior`
- import name: `agentcheck`
- CLI command: `agentcheck`

That means users will install it with:

```bash
pip install agentcheck-behavior
```

and use it with:

```python
import agentcheck
```

or:

```bash
agentcheck test examples
```

## One-Time Setup

1. Create a PyPI account:
   `https://pypi.org/account/register/`
2. Create an API token:
   `https://pypi.org/manage/account/token/`
3. Optionally create a TestPyPI account:
   `https://test.pypi.org/account/register/`

## Build

Install the build tools:

```bash
python -m pip install --upgrade build twine
```

Build the package:

```bash
python -m build
```

This creates:

- `dist/*.tar.gz`
- `dist/*.whl`

## Validate

Check the artifacts before upload:

```bash
python -m twine check dist/*
```

## Upload To TestPyPI First

```bash
python -m twine upload --repository testpypi dist/*
```

Then test install:

```bash
python -m pip install --index-url https://test.pypi.org/simple/ agentcheck-behavior
```

## Upload To PyPI

```bash
python -m twine upload dist/*
```

## Recommended Pre-Release Checks

- `python -m pytest tests -q`
- `python -m agentcheck.cli test examples`
- `python -m agentcheck.cli test regression_examples --fail-on-regression`
- `python -m agentcheck.cli test integration_examples` if `OPENAI_API_KEY` is set

## After Publish

Verify the package can be installed in a fresh environment:

```bash
python -m venv .venv-publish-check
.venv-publish-check\\Scripts\\activate
python -m pip install agentcheck-behavior
python -c "import agentcheck; print(agentcheck.__all__)"
```
