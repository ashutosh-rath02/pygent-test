from __future__ import annotations

from typing import Any


def compare_reports(current: list[dict[str, Any]], baseline: list[dict[str, Any]] | None) -> dict[str, Any]:
    if baseline is None:
        return {"available": False, "regressions": [], "summary": "No baseline found."}

    baseline_map = {report["test_name"]: report for report in baseline}
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
    return {"available": True, "regressions": regressions, "summary": summary}
