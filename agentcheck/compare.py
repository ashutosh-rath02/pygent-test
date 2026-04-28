from __future__ import annotations

from typing import Any


def compare_reports(
    current: list[dict[str, Any]],
    baseline: list[dict[str, Any]] | None,
    *,
    current_suite: str | None = None,
    baseline_suite: str | None = None,
) -> dict[str, Any]:
    if baseline is None:
        return {
            "available": False,
            "suite_mismatch": False,
            "regressions": [],
            "summary": "No baseline found.",
        }

    if current_suite and baseline_suite and current_suite != baseline_suite:
        return {
            "available": True,
            "suite_mismatch": True,
            "regressions": [],
            "summary": (
                "Baseline suite mismatch: "
                f"current `{current_suite}` vs baseline `{baseline_suite}`. "
                "Suite identities must match exactly. "
                "Run `agentcheck bless <path>` for this suite."
            ),
        }

    baseline_map = {report["test_name"]: report for report in baseline}
    overlapping_names = {report["test_name"] for report in current if report["test_name"] in baseline_map}

    if not overlapping_names:
        return {
            "available": True,
            "suite_mismatch": True,
            "regressions": [],
            "summary": (
                "Baseline suite mismatch: "
                f"current `{current_suite}` vs baseline `{baseline_suite}`. "
                "The reports do not share any test names. "
                "Run `agentcheck bless <path>` for this suite."
            ),
        }
    regressions: list[dict[str, Any]] = []
    for report in current:
        previous = baseline_map.get(report["test_name"])
        if previous is None:
            continue
        if report["success_rate"] < previous["success_rate"]:
            regressions.append(
                {
                    "test_name": report["test_name"],
                    "previous_success_rate": previous["success_rate"],
                    "current_success_rate": report["success_rate"],
                    "step_delta": report["average_steps"] - previous.get("average_steps", 0.0),
                }
            )
    summary = "Regression detected." if regressions else "No regression detected."
    return {"available": True, "suite_mismatch": False, "regressions": regressions, "summary": summary}
