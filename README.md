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

    expect(result).used_tool("restaurant_search")
    expect(result).used_tool("booking_tool")
    expect(result).steps_less_than(5)
    expect(result).did_not_claim_confirmation_without_tool("booking_tool")
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
