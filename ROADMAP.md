# AgentCheck Roadmap

This roadmap is meant to keep AgentCheck focused.

The goal is not to build every possible eval feature.
The goal is to make agent behavior testing simple, useful, and repeatable.

## Guiding Principle

AgentCheck should help developers answer:

- did the agent behave correctly?
- did that behavior regress?
- what specifically broke?

## Done

These are already working today:

- repeated-run behavioral tests with `@agent_test(...)`
- normalized `AgentResult` and `ToolCall` models
- core assertions:
  - `used_tool(...)`
  - `did_not_use_tool(...)`
  - `used_tools_in_order([...])`
  - `steps_less_than(...)`
  - `finished_successfully()`
  - `did_not_error()`
  - `final_output_contains(...)`
  - `final_output_does_not_contain(...)`
  - `did_not_claim_confirmation_without_tool(...)`
- collected assertion mode with `verify()`
- local traces, reports, and baselines
- regression detection
- CLI commands:
  - `test`
  - `bless`
  - `compare`
  - `report`
- pytest integration
- plain Python adapter
- OpenAI Agents SDK adapter
- local demo agents
- intentional regression demo
- live OpenAI integration tests
- smoke-test script

## Now

These are the next highest-priority items.

### 1. Better Reports

- Markdown report output
- clearer summaries of what changed
- better run-to-run failure grouping

Why:
- this improves the core developer experience immediately

### 2. A Few More High-Value Assertions

Candidate additions:

- `used_tool_times(tool_name, count)`
- `used_tool_at_least(tool_name, count)`
- `used_tool_at_most(tool_name, count)`

Why:
- these are broadly useful and easy to explain

### 3. Onboarding Improvements

- easier "first real agent test" flow
- stronger templates/examples
- less setup friction

Why:
- adoption depends heavily on how quickly someone gets to a working test

## Next

These should happen after the core loop is polished.

### 4. LangGraph Adapter

Why:
- likely high demand
- useful proof of framework breadth

### 5. Another Framework Adapter Based on Demand

Candidates:

- CrewAI
- smolagents
- another framework that real users request

Why:
- adapter work should follow demand, not guesses

### 6. Better Regression Analysis

- stronger baseline comparisons
- better flaky test visibility
- clearer summaries of changes in success rate and behavior

Why:
- this deepens the value of repeated runs

## Later

These are real possibilities, but not immediate priorities.

### 7. CI-Focused Output Improvements

- richer CI summaries
- artifact-friendly report formats
- nicer pull-request visibility

### 8. More Safety-Oriented Assertions

Examples:

- clarification checks
- forbidden content or policy checks
- private-data exposure checks

These should only be added if they stay broadly reusable.

### 9. Hosted or Team Workflows

Possible future directions:

- hosted history
- team baselines
- private trace storage
- flaky-test analytics

Only worth doing if the core library proves genuinely useful first.

## Not Right Now

These are explicitly not current priorities:

- building a dashboard-first product
- adding lots of niche assertions
- trying to solve all eval problems
- turning the project into a benchmark platform
- depending heavily on fuzzy LLM-as-judge scoring in v1

## What Success Looks Like

In the near term, success means:

- a developer can install the package quickly
- write one useful behavioral test
- run it repeatedly
- save a baseline
- detect a regression
- understand what broke without digging through raw traces

## Contributor-Friendly Areas

Good places for contributors to help:

- new adapters
- report output improvements
- better examples
- test coverage
- documentation improvements
- a few broadly useful new assertions
