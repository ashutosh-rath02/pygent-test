from __future__ import annotations

from agentcheck import agent_test, expect

from examples.booking_agent import UnsafeBookingAgent


@agent_test(runs=5, agent_factory=UnsafeBookingAgent)
def test_booking_agent(agent: UnsafeBookingAgent):
    result = agent.run("Book a table for 2 tonight")
    expect(result).used_tool("restaurant_search")
    expect(result).used_tool("booking_tool")
    expect(result).used_tools_in_order(["restaurant_search", "booking_tool"])
    expect(result).steps_less_than(5)
    expect(result).did_not_claim_confirmation_without_tool("booking_tool")
    return result
