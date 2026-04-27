# AgentCheck

AgentCheck is pytest for AI agents. Test behavior, not exact text.

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

AgentCheck has been exercised against real OpenAI Agents SDK agents.

Use the included live suite:

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

Integration guide:

- [REAL_WORLD_TESTING.md](REAL_WORLD_TESTING.md)

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

## Release Readiness

Before pushing or sharing the repo, use:

- [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md)
