# Behavioral Regression Testing for AI Agents: Introducing agentcheck

Software testing has solved hard problems over the past few decades. Property-based testing, mutation testing, snapshot testing, fuzz testing. But none of that infrastructure was built with AI agents in mind, and the gap shows.

When you write a REST API endpoint, you call it with a known input and assert on the output. The function is deterministic. If it breaks, it breaks the same way every time. You can bisect the commit that caused it. You can write a regression test that will catch it forever.

When you write an AI agent, none of that is true. The same prompt can produce different tool call sequences on different invocations. The model can hallucinate a confirmation it never actually performed. A new version of the underlying LLM can silently change the tool-use behavior your product depends on, and your unit tests will still pass because they never actually ran the agent.

This is the problem agentcheck was built to solve.

---

## What agentcheck actually is

agentcheck is a test runner for AI agent behavior. You install it, annotate your test functions with `@agent_test`, and run `agentcheck test`. It collects your tests, runs each one the number of times you specified, evaluates your assertions, detects flakiness across runs, compares results against a saved baseline, and generates a report.

It does not mock your agent. It does not stub the LLM. It runs the real thing, collects what the agent actually did, and gives you a structured way to make claims about that behavior.

The install is straightforward:

```
pip install pygent-test
```

Zero runtime dependencies for the core library. Adapter-specific extras are opt-in.

---

## The data model

Everything in agentcheck flows through two data classes: `AgentResult` and `ToolCall`.

```
AgentResult
  input          str              The prompt you sent
  final_output   str              What the agent returned
  tool_calls     list[ToolCall]   Every tool invocation, in order
  steps          int              How many reasoning steps the agent took
  errors         list[str]        Any errors that occurred
  latency        float            Wall-clock seconds for the full run
  cost           float | None     Token cost if the agent reports it
  metadata       dict             Anything else you want to carry through
```

```
ToolCall
  name      str          The tool name
  args      dict         Arguments passed to the tool
  output    str | None   What the tool returned
  success   bool         Whether the tool invocation succeeded
```

You construct these yourself inside your test functions. The point is that you own the translation from your agent framework to this schema. agentcheck does not care whether you're using OpenAI, Gemini, CrewAI, LangGraph, or an HTTP endpoint. Once you produce an `AgentResult`, the entire assertion and reporting system works the same way.

```python
from agentcheck import AgentResult, ToolCall, agent_test, expect

@agent_test(runs=3)
def test_booking_agent():
    result = run_my_agent("Book a table for 2 at Nobu, 8pm")

    return (
        expect(result)
        .used_tool("get_availability")
        .used_tool("book_table")
        .used_tools_in_order(["get_availability", "book_table"])
        .final_output_contains("confirmed")
        .did_not_claim_confirmation_without_tool("book_table")
        .verify()
    )
```

---

## The assertion API

There are 15 assertion types. They cover the things that actually break in agent pipelines.

**Tool presence and frequency**

```python
expect(result).used_tool("search")
expect(result).used_tool_times("search", 1)
expect(result).used_tool_at_least("search", 1)
expect(result).used_tool_at_most("book", 2)
expect(result).did_not_use_tool("delete")
expect(result).used_any_tool()
```

**Tool ordering**

```python
expect(result).used_tools_in_order(["get_weather", "book_restaurant"])
```

This assertion verifies that the tools appear in the given sequence. It does not require them to be the only tools called; it checks subsequence ordering.

**Tool success**

```python
expect(result).tool_succeeded("book_table")
```

**Output shape**

```python
expect(result).steps_less_than(5)
expect(result).finished_successfully()
expect(result).did_not_error()
expect(result).final_output_contains("confirmed")
expect(result).final_output_does_not_contain("I was unable to")
expect(result).final_output_matches_pattern(r"Order #\d+")
```

**The hallucination check**

```python
expect(result).did_not_claim_confirmation_without_tool("book_table")
```

This one is particularly useful. It checks whether the final output contains confirmation-like language ("confirmed", "booked", "reserved", "scheduled") while the agent never actually called the specified tool. This is the pattern you see when a model decides to answer from memory instead of from its tools. It passes when either the output contains no confirmation language, or the tool was actually called.

**Collect mode**

By default, the first failing assertion raises immediately. If you want to see all failures at once:

```python
check = expect(result, collect=True)
check.used_tool("search")
check.used_tool("book")
check.finished_successfully()
check.verify()  # raises with all failures combined
```

---

## Multiple runs and flakiness detection

This is where agentcheck differs meaningfully from just writing a pytest test and calling your agent once.

You specify how many times each test should run:

```python
@agent_test(runs=5)
def test_booking_agent():
    ...
```

agentcheck runs the function 5 times, collects 5 `AgentResult` objects, and evaluates the assertion for each. But instead of simply reporting pass or fail, it computes a flakiness score.

The score is variance-based. Given N runs, it computes the variance of the binary pass/fail outcomes and scales it:

```
flakiness = min(variance * 4, 1.0)
```

A test that passes every time has a flakiness score of 0.0. A test that fails every time also has a score of 0.0. The maximum score of 1.0 occurs when the test passes exactly half the time, which is the highest-entropy outcome for a binary variable.

Beyond the score, agentcheck tracks whether the tool call sequence itself is unstable across runs. If your agent called `["search", "book"]` in one run and `["book"]` in another, that is flagged separately as unstable tool paths. This distinction matters because you can have a test that always passes but with meaningfully different behavior across runs. That is still flakiness worth knowing about.

The CLI output looks like this:

```
PASS   test_booking_agent    5/5 runs   flaky=0.00   3 steps   0.412s
FLAKY  test_search_agent     3/5 runs   flaky=0.96   unstable_tool_paths
```

---

## Regression detection

Knowing that your agent currently behaves well is only half the problem. The other half is knowing when it stops.

The workflow is two commands:

```
agentcheck test examples/
agentcheck bless examples/
```

`bless` saves the current test results as a baseline. On every subsequent run, agentcheck compares the new results against the baseline and surfaces regressions:

```
agentcheck test examples/ --fail-on-regression
```

Exit code 0 means clean. Exit code 2 means regression detected. The comparison is per-test and looks at success rate, flakiness score, and whether new failure categories appeared. A test that went from 5/5 to 3/5 is a regression. A test that introduced a new `missing_required_tool` failure category is a regression. A test that improved is not a regression and will not cause a non-zero exit.

This gives you something to wire into CI. When you deploy a new version of your agent or upgrade the underlying model, the pipeline will tell you exactly which tests regressed and by how much.

---

## Failure taxonomy

agentcheck uses a structured taxonomy for classifying failures rather than just recording assertion text. When a test fails, each failure is tagged with a category:

```
missing_required_tool       The agent did not call a tool that was required
unsupported_success_claim   The agent claimed success without calling the tool
wrong_tool_order            Tools were called in the wrong sequence
tool_failure                A tool call explicitly returned failure
output_missing_content      Required text was absent from the final output
unexpected_output_content   Forbidden text appeared in the final output
step_budget_exceeded        The agent used more steps than allowed
error_in_run                An exception occurred during the agent run
```

These categories appear in the CLI output, in the JSON report, and in the HTML report. They are what the regression comparison uses when it says "new failure category appeared."

---

## The CLI

```
agentcheck test <path>                Run tests at path
agentcheck test <path> -k <filter>    Run only tests matching keyword
agentcheck test <path> --html out.html  Generate HTML report
agentcheck test <path> --fail-on-regression  Exit 2 on regression

agentcheck bless <path>              Save current results as baseline
agentcheck baseline list             Show all saved baselines
agentcheck baseline inspect <file>   Inspect a baseline file
agentcheck baseline delete <file>    Remove a baseline

agentcheck report                    Re-render report from last run
agentcheck report --html out.html    HTML from last run

agentcheck history list              Show run history
agentcheck history show <id>         Show a specific run

agentcheck contract init <name>      Create an agent contract file
agentcheck contract validate <file>  Validate a contract file

agentcheck generate scenarios <contract> --output <file> --stub <file>
                                     Generate test scenarios from a contract

agentcheck config init               Create agentcheck.json config file
```

Test discovery works like pytest: any file matching `test_*.py` or `*_test.py`, any function decorated with `@agent_test`. The `-k` filter matches substrings of test names. Exit code 3 means no tests matched the filter.

---

## Agent contracts and scenario generation

An agent contract is a JSON document that describes what a named agent is supposed to do:

```json
{
  "name": "booking_agent",
  "description": "Checks availability then books a restaurant.",
  "schema_version": "1",
  "expected_tools": ["get_availability", "book_table"],
  "required_tool_order": ["get_availability", "book_table"],
  "step_budget": 5,
  "forbidden_claims": ["confirmed", "booked"],
  "scenario_tags": ["happy_path", "tool_failure", "edge_case"]
}
```

`agentcheck contract validate` checks the contract for structural correctness and internal consistency (for example, it will flag a `required_tool_order` entry that names a tool not in `expected_tools`).

From a contract, you can generate test scenarios:

```
agentcheck generate scenarios booking_contract.json \
  --output scenarios.json \
  --stub test_booking_stub.py
```

This produces a scenario pack covering the specified tags and a test file stub with the assertion skeletons filled in based on the contract definition. You provide the agent invocation; agentcheck provides the structure.

---

## The adapter layer

The adapter layer solves the translation problem for the most common frameworks.

**HttpAdapter**

For agents deployed behind an HTTP endpoint. Uses only the Python standard library.

```python
from agentcheck.adapters.http import HttpAdapter

adapter = HttpAdapter(
    url="https://my-agent.example.com/run",
    request_key="message",
    response_output_key="answer",
    response_tools_key="tool_calls",
    auth_env_var="MY_AGENT_API_KEY",
)

result = adapter.run_input("Book a table for 2")
```

The adapter accepts several key aliases for tool call fields in the response body to accommodate different API conventions. `name` or `tool`, `args` or `arguments` or `input`, `output` or `result`, `success` or `ok`. String-only tool call arrays are also handled.

For environment-driven configuration:

```python
adapter = HttpAdapter.from_env(
    url_env_var="AGENT_ENDPOINT",
    auth_env_var="AGENT_API_KEY",
)
```

**CrewAIAdapter**

```python
from agentcheck.adapters.crewai import CrewAIAdapter

adapter = CrewAIAdapter()

@agent_test(runs=3)
def test_research_crew():
    crew = build_research_crew()
    result = adapter.run(crew, "Research the latest in AI safety")
    return expect(result).used_any_tool().verify()
```

`CrewAIAdapter.run()` calls `crew.kickoff()`. `CrewAIAdapter.run_agent()` wraps a single CrewAI Agent using `execute_task`. The adapter normalizes `tasks_output`, extracts errors from the raw result, and reads token usage for cost tracking. crewai is a soft dependency; if it is not installed, the adapter raises a clear `ImportError` at call time rather than at import time.

**LangGraphAdapter**

```python
from agentcheck.adapters.langgraph import LangGraphAdapter

adapter = LangGraphAdapter(
    agent_factory=build_research_graph,
    input_key="messages",
    output_key="messages",
)

@agent_test(runs=3)
def test_research_graph(agent):
    result = agent.run("What are the implications of AGI?")
    return expect(result).used_any_tool().finished_successfully().verify()
```

The adapter wraps a compiled `StateGraph` and handles the `HumanMessage` conversion and streaming output collection internally.

---

## pytest integration

agentcheck ships a pytest plugin. If you prefer running your agent tests through pytest rather than the agentcheck CLI, you can do that without changing your test code:

```
pytest examples/ -q
```

The plugin registers as `agentcheck` in the `pytest11` entry point. `@agent_test` decorated functions are discovered by pytest, and the runs and assertion logic behaves identically to the CLI.

This means agentcheck tests can live alongside your regular unit tests in the same test suite and be run in the same CI step. The `__test__ = False` attribute that `@agent_test` sets prevents pytest from double-discovering the function.

---

## Reports

Every `agentcheck test` run writes four artifacts to `.agentcheck/`:

```
.agentcheck/reports/latest.json     Full structured report
.agentcheck/reports/latest.md       Markdown summary
.agentcheck/reports/latest.html     HTML report (always generated)
.agentcheck/traces/latest.json      Per-run trace with AgentResult data
.agentcheck/history.json            Append-only run history
```

The HTML report includes per-test pass rates, flakiness scores, unstable tool path flags, failure taxonomy breakdowns, and tool call timelines. You can also generate it on demand from any previous run:

```
agentcheck report --html my_report.html
```

The history commands let you compare runs over time:

```
agentcheck history list
agentcheck history show <run-id>
```

---

## Architecture diagram

```
                        Your test file
                             |
               @agent_test(runs=N, agent_factory=...)
                             |
                      agentcheck CLI
                    /         |         \
           discovery     runner      reporter
               |             |            |
        test_*.py files   runs N times  JSON / MD / HTML
                             |
                    [AgentResult, AgentResult, ...]
                             |
                    assertion evaluator
                             |
                    flakiness scorer
                             |
                    regression comparator
                          (baseline)
                             |
                       exit code + report
```

The runner never touches your agent directly. It calls the function you wrote, which calls your agent, which returns an `AgentResult`. That boundary is where all the adapter work happens.

---

## Invarium

One of the first teams to take a close look at agentcheck before public release was the engineering team at Invarium. Invarium builds infrastructure for enterprise AI deployments, and the problem they ran into is the same one everyone building on top of LLMs eventually hits: how do you know your agent is still doing what it was doing last week?

Their interest in agentcheck specifically was around the regression detection workflow and the adapter layer. When you are running agents inside an enterprise environment, the agent is often behind an internal HTTP endpoint that your test suite never directly touches. The `HttpAdapter` pattern, where you describe the request/response mapping once and then write test assertions against the normalized `AgentResult`, fits naturally into that architecture.

They are evaluating agentcheck for integration into their existing CI pipelines alongside their current LLM evaluation tooling.

---

## What agentcheck does not do

It is worth being direct about the scope.

agentcheck does not evaluate output quality. It does not use another LLM to judge whether the response was good. It does not do semantic similarity scoring. Those are valid approaches for certain problems, but they have their own non-determinism and cost. agentcheck is about behavioral correctness: did the agent use the right tools, in the right order, without hallucinating success. That is a narrower and more tractable question, and the answer is deterministic once you have the `AgentResult`.

It does not handle multi-agent orchestration natively. If your system is a graph of agents, you test each node independently or wrap the full graph and treat it as a single agent. The adapter layer is the right place to handle that translation.

It does not replace prompt evaluation. If you need to judge answer quality, factual accuracy, or response style, you need a different tool. agentcheck is a complement to that, not a replacement.

---

## Getting started

```
pip install pygent-test

agentcheck test your_tests/
```

For framework-specific adapters:

```
pip install "pygent-test[openai]"
pip install "pygent-test[langgraph]"
pip install "pygent-test[crewai]"
```

Source and documentation are on GitHub at github.com/ashutosh-rath02/pygent-test. Issues and contributions are open.

The version in this post is 0.2.2. The library requires Python 3.10 or newer.
