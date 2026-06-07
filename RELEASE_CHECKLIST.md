# Release Checklist

## Before Push

- Run `python -m pytest tests -q`
- Run `python -m agentcheck.cli test examples`
- Run `python -m agentcheck.cli test framework_examples` if LangGraph dependencies are installed
- Run `python -m agentcheck.cli test regression_examples`
- Run `python -m agentcheck.cli test integration_examples` if `OPENAI_API_KEY` is set

## Baselines

- Save a healthy baseline for local demos:
  `python -m agentcheck.cli bless examples`
- Save a healthy baseline for LangGraph demos when ready:
  `python -m agentcheck.cli bless framework_examples`
- Save a healthy baseline for live OpenAI tests when ready:
  `python -m agentcheck.cli bless integration_examples`

## Repo Hygiene

- Make sure `.agentcheck/`, `venv/`, and build artifacts are ignored
- Avoid committing real API keys or secrets
- Prefer a dedicated virtualenv for live OpenAI testing

## Known Limitations

- Pytest cache warnings may appear in some Windows/OneDrive environments

## Good Demo Commands

Passing demo:

```bash
python -m agentcheck.cli test examples
```

Regression demo:

```bash
python -m agentcheck.cli bless examples
python -m agentcheck.cli test regression_examples
```

Live OpenAI demo:

```bash
python -m agentcheck.cli test integration_examples
```

LangGraph demo:

```bash
python -m agentcheck.cli test framework_examples
```
