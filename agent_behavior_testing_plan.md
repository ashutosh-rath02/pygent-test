# Agent Behavior Testing Tool — Build Plan

## 1. Product Thesis

Developers building AI agents do not need another eval dashboard. They need a simple way to write tests that check whether an agent behaved correctly.

The product should be:

> A pytest-style behavioral regression testing library for AI agents.

It should help developers answer:

- Did the agent use the correct tool?
- Did it avoid unsafe or fake actions?
- Did it complete the task within a reasonable number of steps?
- Did a prompt, model, or orchestration change make the agent worse?
- Is the agent reliable across repeated runs, not just one lucky run?

The core product should be a Python library first, not a SaaS dashboard.

---

## 2. What We Are Not Building

We are not building:

- A LangSmith clone
- A generic LLM observability platform
- A prompt evaluation dashboard
- A model benchmark platform
- A security governance platform
- A research-heavy statistical framework only experts can use
- A tool that checks exact text output

If the product becomes "yet another eval tool," it loses.

---

## 3. Existing Market Reality

There are already tools in nearby spaces:

### AgentAssay

AgentAssay focuses on statistical regression testing, behavioral fingerprints, adaptive sampling, and confidence-aware verdicts.

It is closer to a testing engine or research-backed methodology.

### LangSmith / Langfuse / Braintrust / Arize Phoenix

These focus on tracing, monitoring, observability, datasets, and evaluation workflows.

They are useful, but heavier than what many developers need at the test-writing stage.

### Promptfoo / OpenAI Evals / DeepEval

These are useful for prompt and LLM output evaluation, but they are not primarily built around agent behavior assertions.

### AgentAssert / AgentTest-style tools

Some tools attempt testing syntax, but the space is still immature. Most are not yet the obvious default for agent developers.

---

## 4. Our Differentiation

The differentiation must be very clear:

> We are not the most mathematically advanced agent testing system.
> We are the easiest way for developers to write useful behavioral tests for agents.

### Existing tools focus on:

- traces
- dashboards
- datasets
- statistical methodology
- model scoring
- output evaluation
- production observability

### We focus on:

- simple test files
- behavioral assertions
- repeated runs
- regression detection
- clear failure explanations
- CI integration
- framework-agnostic adapters

The winning UX should feel like this:

```python
from agentcheck import agent_test, expect

@agent_test(runs=10)
def test_booking_agent(agent):
    result = agent.run("Book a table for 2 tonight")

    expect(result).used_tool("restaurant_search")
    expect(result).used_tool("booking_tool")
    expect(result).steps_less_than(8)
    expect(result).did_not_claim_confirmation_without_tool()
```

This is the whole product direction.

---

## 5. Proposed Product Name

Do not use `AgentAssay`.

Possible names:

- AgentCheck
- AgentSpec
- AgentTestKit
- BehaviorCheck
- TraceAssert
- AgentProof

Recommended working name:

> AgentCheck

Reason: simple, clear, developer-friendly.

---

## 6. Target User

Primary user:

- Python developer building agents
- Uses LangGraph, CrewAI, OpenAI Agents SDK, custom Python agents, or similar
- Wants to ship agents into production
- Needs confidence that changes do not break behavior

Secondary user:

- AI engineering teams
- Developer tools teams
- QA engineers working on agentic systems
- ML platform teams

Do not start with enterprise security or governance buyers.

---

## 7. MVP Goal

The MVP should let a developer install the package, write one test, run it multiple times, and see whether the agent behavior passed or regressed.

MVP command:

```bash
pip install pygent-test
agentcheck test
```

MVP output:

```text
Booking Agent Test
Runs: 10
Passed: 7
Failed: 3
Success rate: 70%

Failures:
- booking_tool was not called in 2 runs
- agent claimed booking confirmation without tool receipt in 1 run

Baseline success rate: 92%
Current success rate: 70%
Regression: YES
```

---

## 8. Core MVP Features

### 8.1 Test Decorator

Allow developers to mark a function as an agent behavior test.

```python
@agent_test(runs=10)
def test_refund_agent(agent):
    result = agent.run("I want a refund for my last order")
    expect(result).used_tool("order_lookup")
    expect(result).used_tool("refund_policy_check")
    expect(result).did_not_use_tool("refund_execute")
```

Required functionality:

- run the same test multiple times
- collect each result
- aggregate pass/fail rate
- save trace history

---

### 8.2 Agent Result Object

Every test run should produce a normalized result object.

```python
result.messages
result.tool_calls
result.steps
result.final_output
result.errors
result.cost
result.latency
result.metadata
```

This object is the foundation of the product.

---

### 8.3 Behavioral Assertions

The first version should support a small but strong set of assertions.

Required assertions:

```python
expect(result).used_tool("tool_name")
expect(result).did_not_use_tool("tool_name")
expect(result).used_tools_in_order(["search", "book"])
expect(result).steps_less_than(8)
expect(result).finished_successfully()
expect(result).did_not_error()
expect(result).final_output_contains("...")
expect(result).final_output_does_not_contain("...")
expect(result).did_not_claim_confirmation_without_tool()
```

Do not overload v1 with too many assertions.

The first magic moment should be tool-use and fake-confirmation detection.

---

### 8.4 Repeated Runs

Agents are nondeterministic. A single pass means very little.

The tool should run the same test multiple times:

```python
@agent_test(runs=20)
```

Then report:

- success rate
- failure rate
- common failure causes
- flaky behavior
- regression against baseline

---

### 8.5 Baseline Comparison

Store previous results locally.

Directory:

```text
.agentcheck/
  baselines/
  traces/
  reports/
```

Commands:

```bash
agentcheck test
agentcheck bless
agentcheck compare
```

Meaning:

- `test`: run tests
- `bless`: save current results as baseline
- `compare`: compare current results with baseline

Example:

```text
Previous success rate: 91%
Current success rate: 64%
Regression detected: YES
```

---

### 8.6 Failure Explanation

The tool should not only say pass/fail.

It should explain what changed.

Example:

```text
Regression reason:
- search_tool usage dropped from 100% to 55%
- average steps increased from 5.2 to 11.6
- final answer claimed booking success without booking_tool receipt in 4 runs
```

This is a major differentiator from pure statistical tools.

---

### 8.7 Framework Adapters

The internal trace format must be framework-agnostic.

Start with these adapters:

1. Plain Python function adapter
2. OpenAI Agents SDK adapter
3. LangGraph adapter
4. CrewAI adapter

Do not start with every framework.

Adapter responsibility:

- execute the agent
- capture messages
- capture tool calls
- capture steps
- capture final output
- convert everything into the normalized `AgentResult`

---

### 8.8 CLI

Required commands:

```bash
agentcheck test
agentcheck bless
agentcheck compare
agentcheck report
```

Nice-to-have later:

```bash
agentcheck init
agentcheck list
agentcheck replay
```

---

### 8.9 CI Support

The tool must work in GitHub Actions early.

Example:

```yaml
- name: Run agent behavior tests
  run: agentcheck test --fail-on-regression
```

Exit codes:

- `0`: tests passed
- `1`: behavior failed
- `2`: regression detected
- `3`: configuration error

---

## 9. V1 Architecture

### 9.1 Main Modules

```text
agentcheck/
  __init__.py
  testing.py
  assertions.py
  result.py
  runners.py
  baseline.py
  compare.py
  report.py
  cli.py
  adapters/
    base.py
    python.py
    openai_agents.py
    langgraph.py
    crewai.py
```

---

### 9.2 Core Data Model

```python
class ToolCall:
    name: str
    args: dict
    output: str | dict | None
    success: bool
    timestamp: str

class AgentResult:
    input: str
    final_output: str
    messages: list[dict]
    tool_calls: list[ToolCall]
    steps: int
    errors: list[str]
    latency: float | None
    cost: float | None
    metadata: dict

class TestRun:
    test_name: str
    run_id: str
    result: AgentResult
    assertions: list[AssertionResult]
    passed: bool

class TestReport:
    test_name: str
    total_runs: int
    passed_runs: int
    failed_runs: int
    success_rate: float
    failure_reasons: list[str]
    regression: bool | None
```

---

## 10. Key Design Principle

Do not hide everything behind AI scoring.

The product should prioritize deterministic behavioral checks first:

Good:

```python
expect(result).used_tool("booking_tool")
expect(result).steps_less_than(8)
```

Risky as default:

```python
expect(result).is_good_answer()
```

LLM-as-judge can come later, but v1 should focus on observable behavior.

---

## 11. What Makes This Different From AgentAssay

### AgentAssay

- research-backed
- statistical testing focus
- behavioral fingerprinting
- adaptive test budgets
- confidence intervals
- more engine-like

### Our product

- developer-first
- pytest-like syntax
- explicit behavioral assertions
- clear failure reasons
- CI-friendly
- framework adapters
- simple local workflow

The difference:

> AgentAssay tells you statistically whether behavior changed.
> AgentCheck tells developers exactly what behavior to test and what broke.

Long-term, we could even integrate AgentAssay-style statistical logic internally. But the user-facing product should stay simple.

---

## 12. First 5 Tests We Should Support

These should be the demo examples.

### 12.1 Booking Agent

Checks:

- searched availability
- called booking tool
- did not confirm without receipt
- completed within N steps

### 12.2 Refund Agent

Checks:

- looked up order
- checked policy
- did not issue refund without approval

### 12.3 Research Agent

Checks:

- used search tool
- cited sources
- did not invent citations
- stopped within N steps

### 12.4 Coding Agent

Checks:

- read target file
- edited correct file
- ran tests
- did not claim success if tests failed

### 12.5 Customer Support Agent

Checks:

- asked clarification when required
- did not expose private data
- escalated to human when policy required

---

## 13. MVP Development Sequence

### Week 1

Build:

- `AgentResult`
- `ToolCall`
- basic test runner
- `@agent_test`
- `expect(result)` syntax
- assertions for tool usage and steps
- plain Python adapter

Goal:

```python
agentcheck test
```

works for a simple fake agent.

---

### Week 2

Build:

- repeated runs
- local JSON trace storage
- baseline save/load
- pass rate reporting
- CLI output
- GitHub Action compatibility

Goal:

```bash
agentcheck bless
agentcheck test --fail-on-regression
```

works locally and in CI.

---

### Week 3

Build:

- LangGraph adapter
- OpenAI Agents SDK adapter
- better failure grouping
- HTML or Markdown report
- examples folder

Goal:

A real LangGraph/OpenAI demo passes and fails in understandable ways.

---

### Week 4

Build:

- CrewAI adapter
- docs
- landing README
- comparison page
- launch examples
- first public release

Goal:

Developers can install and understand the product in under 5 minutes.

---

## 14. Public README Structure

The README should not be long.

Recommended structure:

1. One-line pitch
2. Install
3. 30-second example
4. Why output tests fail for agents
5. Supported assertions
6. Supported frameworks
7. Regression testing
8. CI usage
9. Roadmap

Opening line:

> AgentCheck is pytest for AI agents. Test behavior, not exact text.

---

## 15. Launch Strategy

Launch to developers, not enterprises.

Channels:

- GitHub
- Hacker News
- Reddit r/LocalLLaMA
- Reddit r/MachineLearning
- LangChain/LangGraph community
- CrewAI community
- OpenAI developer forum
- Twitter/X AI dev community

Launch demo title:

> I built pytest for AI agents - it catches when your agent silently gets worse.

Demo must show a regression:

```text
Before prompt change: 90% success
After prompt change: 50% success
Reason: agent stopped calling booking_tool
```

---

## 16. Pricing Direction Later

Start open source.

Possible future paid layer:

- hosted dashboards
- team baselines
- test history
- CI reports
- flaky test analytics
- private trace storage
- compliance reports

But do not start with SaaS.

First win developer trust through open source.

---

## 17. Risks

### Risk 1: Existing tools move fast

Mitigation:

- focus on UX, not breadth
- launch quickly
- own the phrase "behavior tests for agents"

### Risk 2: Framework adapters are hard

Mitigation:

- start with plain Python
- define a simple adapter interface
- let community contribute adapters

### Risk 3: Agent behavior is hard to judge

Mitigation:

- avoid fuzzy judgment in v1
- use observable traces first
- add LLM-as-judge later as optional

### Risk 4: Developers do not want another tool

Mitigation:

- make it work with pytest
- make setup tiny
- make the first failure report obviously useful

---

## 18. Product Rules

These rules should guide every decision.

1. If it takes more than 5 minutes to understand, it is too complex.
2. If it requires a dashboard to be useful, it is too heavy.
3. If it only checks final text, it is not our product.
4. If it cannot run in CI, it is not production-ready.
5. If it does not explain what broke, it is not useful enough.
6. If it only works for one framework, it is not ambitious enough.
7. If it tries to solve all eval problems, it will fail.

---

## 19. Final MVP Definition

The MVP is successful when a developer can do this:

```bash
pip install pygent-test
```

Write this:

```python
from agentcheck import agent_test, expect

@agent_test(runs=10)
def test_agent(agent):
    result = agent.run("Book a table for two tonight")

    expect(result).used_tool("search_restaurants")
    expect(result).used_tool("create_booking")
    expect(result).steps_less_than(8)
    expect(result).did_not_claim_confirmation_without_tool()
```

Run this:

```bash
agentcheck test
```

And get this:

```text
FAILED: Behavior regression detected

Previous success rate: 90%
Current success rate: 60%

What changed:
- create_booking tool was not called in 4/10 runs
- agent claimed booking confirmation without tool receipt in 2/10 runs
```

That is the product.

---

## 20. Immediate Next Step

Build a fake-agent prototype first.

Do not integrate with LangGraph or CrewAI immediately.

First prove the core loop:

1. run agent N times
2. capture behavior
3. assert behavior
4. store baseline
5. detect regression
6. explain failure

Once that works, adapters are just distribution.
