from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from agentcheck import AgentResult, ToolCall, expect
from agentcheck.baseline import load_baseline, save_baseline, suite_baseline_path
from agentcheck.compare import compare_reports
from agentcheck.report import render_markdown_report, write_github_step_summary


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
            "suite_id": "framework_examples",
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
                "summary": "Regression detected in 1 of 1 matched test(s).",
                "matched_tests": ["test_booking_agent"],
                "current_only_tests": [],
                "baseline_only_tests": [],
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
    assert "- Suite: `framework_examples`" in markdown
    assert "## test_booking_agent" in markdown
    assert "### Failures" in markdown
    assert "Regression detected in 1 of 1 matched test(s)." in markdown
    assert "- Matched tests: `test_booking_agent`" in markdown
    assert "### Regressions" in markdown
    assert "100.0% -> 60.0%" in markdown


def test_compare_reports_flags_suite_mismatch():
    comparison = compare_reports(
        [{"test_name": "test_booking_agent", "success_rate": 100.0, "average_steps": 2.0}],
        [{"test_name": "test_langgraph_research_agent", "success_rate": 100.0, "average_steps": 3.0}],
        current_suite="examples",
        baseline_suite="framework_examples",
    )

    assert comparison["suite_mismatch"] is True
    assert comparison["regressions"] == []
    assert "Baseline suite mismatch" in comparison["summary"]
    assert comparison["matched_tests"] == []


def test_compare_reports_flags_suite_mismatch_even_when_test_names_overlap():
    comparison = compare_reports(
        [{"test_name": "test_booking_agent", "success_rate": 0.0, "average_steps": 2.0}],
        [{"test_name": "test_booking_agent", "success_rate": 100.0, "average_steps": 2.0}],
        current_suite="regression_examples",
        baseline_suite="examples",
    )

    assert comparison["suite_mismatch"] is True
    assert comparison["regressions"] == []


def test_compare_reports_allows_legacy_comparison_when_suite_ids_are_missing():
    comparison = compare_reports(
        [{"test_name": "test_booking_agent", "success_rate": 0.0, "average_steps": 2.0}],
        [{"test_name": "test_booking_agent", "success_rate": 100.0, "average_steps": 2.0}],
    )

    assert comparison["suite_mismatch"] is False
    assert len(comparison["regressions"]) == 1
    assert comparison["matched_tests"] == ["test_booking_agent"]
    assert comparison["current_only_tests"] == []
    assert comparison["baseline_only_tests"] == []


def test_compare_reports_tracks_unmatched_tests():
    comparison = compare_reports(
        [
            {"test_name": "test_booking_agent", "success_rate": 100.0, "average_steps": 2.0},
            {"test_name": "test_research_agent", "success_rate": 100.0, "average_steps": 3.0},
        ],
        [
            {"test_name": "test_booking_agent", "success_rate": 100.0, "average_steps": 2.0},
            {"test_name": "test_weather_agent", "success_rate": 100.0, "average_steps": 4.0},
        ],
    )

    assert comparison["suite_mismatch"] is False
    assert comparison["matched_tests"] == ["test_booking_agent"]
    assert comparison["current_only_tests"] == ["test_research_agent"]
    assert comparison["baseline_only_tests"] == ["test_weather_agent"]
    assert comparison["summary"] == "No regression detected across 1 matched test(s)."


def test_suite_baselines_are_isolated(monkeypatch):
    workspace_tmp = Path(".build-tmp") / f"baseline-test-{uuid4().hex}"
    monkeypatch.setattr("agentcheck.storage.BASELINE_DIR", workspace_tmp)
    monkeypatch.setattr("agentcheck.baseline.BASELINE_DIR", workspace_tmp)
    monkeypatch.setattr("agentcheck.baseline.BASELINE_FILE", workspace_tmp / "latest.json")

    first_suite = str(workspace_tmp / "examples")
    second_suite = str(workspace_tmp / "framework_examples")
    first_data = {"suite_id": first_suite, "reports": [{"test_name": "test_booking_agent"}]}
    second_data = {"suite_id": second_suite, "reports": [{"test_name": "test_langgraph_agent"}]}

    first_path = save_baseline(first_data, first_suite)
    second_path = save_baseline(second_data, second_suite)

    assert first_path != second_path
    assert first_path == suite_baseline_path(first_suite)
    assert second_path == suite_baseline_path(second_suite)
    assert load_baseline(first_suite) == first_data
    assert load_baseline(second_suite) == second_data
    assert load_baseline(str(workspace_tmp / "missing_suite")) is None


def test_write_github_step_summary_writes_markdown():
    summary_path = Path(".build-tmp") / f"step-summary-{uuid4().hex}.md"
    markdown = "# AgentCheck Report\n"

    written = write_github_step_summary(markdown, str(summary_path))

    assert written is True
    assert summary_path.read_text(encoding="utf-8") == markdown
