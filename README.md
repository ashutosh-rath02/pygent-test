# AgentCheck

AgentCheck is pytest for AI agents. Test behavior, not exact text.

## Quick Start

```bash
python -m pip install -e .
agentcheck test
```

## Example

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

Try the included demo:

```bash
agentcheck test examples
agentcheck bless examples
```

Try the intentional failure demo:

```bash
agentcheck test regression_examples
```

## Commands

- `agentcheck test`
- `agentcheck bless`
- `agentcheck compare`
- `agentcheck report`

## Pytest

AgentCheck tests can also run through `pytest`:

```bash
pytest examples
pytest tests
pytest regression_examples
```

Decorated `@agent_test(...)` functions are collected as AgentCheck test items, and each item still runs its configured repeated-run behavior.

## Assertion Modes

Use the default mode for fail-fast checks:

```python
expect(result).used_tool("restaurant_search")
```

Use `collect=True` when you want one run to report multiple behavior failures:

```python
check = expect(result, collect=True)
check.used_tool("restaurant_search")
check.used_tool("booking_tool")
check.did_not_claim_confirmation_without_tool("booking_tool")
check.verify()
```
