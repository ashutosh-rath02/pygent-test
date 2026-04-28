# AgentCheck

AgentCheck is pytest for AI agents. Test behavior, not exact text.

Install from PyPI:

```bash
pip install pygent-test
```

Install from source:

```bash
python -m pip install -e .
```

Optional framework extras:

```bash
pip install "pygent-test[langgraph]"
pip install "pygent-test[openai]"
```

## What It Does

AgentCheck helps you verify agent behavior such as:

- which tools were used
- whether tools were used in the expected order
- whether the agent stayed within a step budget
- whether the agent claimed success without tool evidence
- whether behavior regressed against a saved baseline

## Current Status

This repo already supports:

- repeated-run behavioral tests with `@agent_test(...)`
- local baseline and regression comparison
- CLI commands: `test`, `bless`, `compare`, `report`
- pytest integration
- a plain Python adapter
- an OpenAI Agents SDK adapter
- a LangGraph adapter
- real live OpenAI agent tests in `integration_examples/`

## Quick Start

```bash
python -m pip install -e .
python -m agentcheck.cli test examples
```

## Minimal Example

```python
from agentcheck import agent_test, expect
from examples.booking_agent import SimpleBookingAgent


@agent_test(runs=5, agent_factory=SimpleBookingAgent)
def test_booking_agent(agent: SimpleBookingAgent):
    result = agent.run("Book a table for 2 tonight")

    check = expect(result, collect=True)
    check.used_tool("restaurant_search")
    check.used_tool("booking_tool")
    check.steps_less_than(5)
    check.did_not_claim_confirmation_without_tool("booking_tool")
    check.verify()
    return result
```

## Real Agent Testing

AgentCheck has been exercised against:

- real OpenAI Agents SDK agents
- real local LangGraph graphs built with `StateGraph`

Use the included repo live suite:

```bash
python -m agentcheck.cli test integration_examples
```

or:

```bash
python -m pytest integration_examples -q
```

The included live tests cover:

- a single-tool weather assistant
- a multi-tool research assistant

LangGraph support is tested through the regular unit suite and normalizes the common
`invoke({"messages": [...]})` flow into `AgentResult`.

Run the local LangGraph example with:

```bash
python -m agentcheck.cli test framework_examples
```

## Documentation

Use these docs depending on what you need:

- [TECHNICAL_GUIDE.md](TECHNICAL_GUIDE.md)
  Detailed developer guide covering architecture, assertions, adapters, and workflows
- [ADAPTER_GUIDE.md](ADAPTER_GUIDE.md)
  How adapters are structured and how to build a new one
- [REAL_WORLD_TESTING.md](REAL_WORLD_TESTING.md)
  Real OpenAI Agents SDK testing setup and examples
- [ROADMAP.md](ROADMAP.md)
  What is done, what is next, and what is planned later

## Included Demos

Passing local demo:

```bash
python -m agentcheck.cli test examples
```

Intentional failure demo:

```bash
python -m agentcheck.cli test regression_examples --fail-on-regression
```

## Commands

- `python -m agentcheck.cli test <path>`
- `python -m agentcheck.cli bless <path>`
- `python -m agentcheck.cli compare`
- `python -m agentcheck.cli report`

## Smoke Test

If you are working from a source checkout, run a quick end-to-end validation with:

```bash
python scripts/smoke_test.py
```

To include the live OpenAI integration tests:

```bash
python scripts/smoke_test.py --with-live
```

Every `agentcheck test` run also writes:

- JSON report: `.agentcheck/reports/latest.json`
- Markdown report: `.agentcheck/reports/latest.md`

Baselines are guarded against unrelated suites. If the current run and the saved
baseline do not share any test names, AgentCheck warns instead of silently
pretending the comparison is valid.

## Pytest

AgentCheck tests can also run through `pytest`:

```bash
python -m pytest examples -q
python -m pytest tests -q
python -m pytest integration_examples -q
```

Decorated `@agent_test(...)` functions are collected as AgentCheck test items, and each item still runs its configured repeated-run behavior.

## Assertions

Current built-in assertions:

- `used_tool(...)`
- `used_tool_times(...)`
- `used_tool_at_least(...)`
- `used_tool_at_most(...)`
- `did_not_use_tool(...)`
- `used_tools_in_order([...])`
- `steps_less_than(...)`
- `finished_successfully()`
- `did_not_error()`
- `final_output_contains(...)`
- `final_output_does_not_contain(...)`
- `did_not_claim_confirmation_without_tool(...)`

Use fail-fast assertions:

```python
expect(result).used_tool("restaurant_search")
```

Use collected assertions when you want one run to report multiple failures:

```python
check = expect(result, collect=True)
check.used_tool("restaurant_search")
check.used_tool("booking_tool")
check.did_not_claim_confirmation_without_tool("booking_tool")
check.verify()
```

## Roadmap

This is the first step.

Near-term priorities:

- cleaner regression summaries
- better onboarding for testing a real agent in under 5 minutes
- more adapters based on actual user demand

Longer-term directions:

- stronger regression analysis
- better flakiness reporting
- richer CI workflows
- optional hosted features only if the core library proves valuable

For a more detailed breakdown, see [ROADMAP.md](ROADMAP.md).
