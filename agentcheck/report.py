from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from .assertions import AssertionRecord
from .result import AgentResult


@dataclass(slots=True)
class TestRun:
    test_name: str
    run_id: str
    result: AgentResult
    assertions: list[AssertionRecord] = field(default_factory=list)
    passed: bool = True
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "test_name": self.test_name,
            "run_id": self.run_id,
            "result": self.result.to_dict(),
            "assertions": [asdict(item) for item in self.assertions],
            "passed": self.passed,
            "error": self.error,
        }


@dataclass(slots=True)
class TestReport:
    test_name: str
    total_runs: int
    passed_runs: int
    failed_runs: int
    success_rate: float
    failure_reasons: list[str]
    average_steps: float
    regression: bool | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class SessionReport:
    created_at: str
    reports: list[TestReport]
    baseline_comparison: dict[str, Any] = field(default_factory=dict)
    trace_file: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "created_at": self.created_at,
            "reports": [report.to_dict() for report in self.reports],
            "baseline_comparison": self.baseline_comparison,
            "trace_file": self.trace_file,
        }


def new_run_id() -> str:
    return uuid4().hex


def build_test_report(test_name: str, runs: list[TestRun]) -> TestReport:
    total_runs = len(runs)
    passed_runs = sum(1 for run in runs if run.passed)
    failed_runs = total_runs - passed_runs
    average_steps = sum(run.result.steps for run in runs) / total_runs if total_runs else 0.0
    failures = Counter()
    for run in runs:
        if run.error and not run.assertions:
            failures[run.error] += 1
        for assertion in run.assertions:
            if not assertion.passed:
                failures[assertion.message] += 1
    failure_reasons = [f"{message} ({count}/{total_runs} runs)" for message, count in failures.most_common()]
    return TestReport(
        test_name=test_name,
        total_runs=total_runs,
        passed_runs=passed_runs,
        failed_runs=failed_runs,
        success_rate=(passed_runs / total_runs) * 100 if total_runs else 0.0,
        failure_reasons=failure_reasons,
        average_steps=average_steps,
    )


def new_session_report(reports: list[TestReport]) -> SessionReport:
    return SessionReport(
        created_at=datetime.now(timezone.utc).isoformat(),
        reports=reports,
    )
