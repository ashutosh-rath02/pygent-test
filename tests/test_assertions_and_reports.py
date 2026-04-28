from __future__ import annotations

from agentcheck import AgentResult, ToolCall, expect
from agentcheck.report import render_markdown_report


def test_tool_count_assertions_pass_in_collected_mode():
    result = AgentResult(
        input="Research AgentCheck",
        final_output="Done",
        tool_calls=[
            ToolCall(name="search_docs", args={"query": "AgentCheck"}),
            ToolCall(name="search_docs", args={"query": "pytest for agents"}),
            ToolCall(name="summarize_notes", args={"length": "short"}),
        ],
        steps=3,
    )

    check = expect(result, collect=True)
    check.used_tool_times("summarize_notes", 1)
    check.used_tool_at_least("search_docs", 2)
    check.used_tool_at_most("search_docs", 2)
    check.verify()


def test_markdown_report_render_includes_summary_and_failures():
    markdown = render_markdown_report(
        {
            "created_at": "2026-04-28T00:00:00Z",
            "trace_file": ".agentcheck/traces/latest.json",
            "markdown_report_file": ".agentcheck/reports/latest.md",
            "reports": [
                {
                    "test_name": "test_booking_agent",
                    "total_runs": 5,
                    "passed_runs": 3,
                    "failed_runs": 2,
                    "success_rate": 60.0,
                    "failure_reasons": [
                        "Expected tool `booking_tool` to be called, but saw ['restaurant_search']. (2/5 runs)"
                    ],
                    "average_steps": 2.4,
                    "regression": False,
                }
            ],
            "baseline_comparison": {
                "summary": "Regression detected.",
                "regressions": [
                    {
                        "test_name": "test_booking_agent",
                        "previous_success_rate": 100.0,
                        "current_success_rate": 60.0,
                        "step_delta": 0.4,
                    }
                ],
            },
        }
    )

    assert "# AgentCheck Report" in markdown
    assert "## test_booking_agent" in markdown
    assert "### Failures" in markdown
    assert "Regression detected." in markdown
    assert "100.0% -> 60.0%" in markdown
