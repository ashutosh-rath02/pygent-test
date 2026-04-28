from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .baseline import load_baseline, save_baseline
from .compare import compare_reports
from .discovery import collect_registered_tests, discover_test_files, import_test_file
from .report import SessionReport, render_markdown_report
from .runners import run_test_suite
from .storage import REPORT_DIR, TRACE_DIR, ensure_artifact_dirs, read_json, write_json


EXIT_SUCCESS = 0
EXIT_BEHAVIOR_FAILED = 1
EXIT_REGRESSION = 2
EXIT_CONFIG_ERROR = 3


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agentcheck")
    subparsers = parser.add_subparsers(dest="command", required=True)

    for command in ("test", "bless", "compare", "report"):
        subparser = subparsers.add_parser(command)
        if command in {"test", "bless"}:
            subparser.add_argument("path", nargs="?", default=".")
            subparser.add_argument("--fail-on-regression", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    ensure_artifact_dirs()

    if args.command in {"test", "bless"}:
        return _run_tests(Path(args.path), bless=args.command == "bless", fail_on_regression=args.fail_on_regression)
    if args.command == "compare":
        return _compare_only()
    if args.command == "report":
        return _report_only()
    return EXIT_CONFIG_ERROR


def _run_tests(root: Path, *, bless: bool, fail_on_regression: bool) -> int:
    _load_tests(root)
    definitions = collect_registered_tests()
    if not definitions:
        print("No AgentCheck tests found.")
        return EXIT_CONFIG_ERROR

    reports, session, trace_payload = run_test_suite(definitions)
    current_data = [report.to_dict() for report in reports]
    baseline_data = load_baseline()
    comparison = compare_reports(current_data, baseline_data["reports"] if baseline_data else None)
    session.baseline_comparison = comparison

    trace_path = TRACE_DIR / "latest.json"
    report_path = REPORT_DIR / "latest.json"
    markdown_report_path = REPORT_DIR / "latest.md"
    session.trace_file = str(trace_path)
    session.markdown_report_file = str(markdown_report_path)
    write_json(trace_path, trace_payload)
    write_json(report_path, session.to_dict())
    markdown_report_path.write_text(render_markdown_report(session), encoding="utf-8")
    _print_session_summary(session)

    if bless:
        save_baseline({"reports": current_data})
        print(f"\nBaseline saved to {Path('.agentcheck/baselines/latest.json')}")

    any_behavior_failures = any(report.failed_runs for report in reports)
    any_regression = bool(comparison["regressions"])
    if fail_on_regression and any_regression:
        return EXIT_REGRESSION
    if any_behavior_failures:
        return EXIT_BEHAVIOR_FAILED
    return EXIT_SUCCESS


def _compare_only() -> int:
    latest_report = REPORT_DIR / "latest.json"
    baseline = load_baseline()
    if not latest_report.exists() or baseline is None:
        print("Latest report or baseline is missing.")
        return EXIT_CONFIG_ERROR
    report_data = read_json(latest_report)
    comparison = compare_reports(report_data["reports"], baseline["reports"])
    _print_comparison(comparison)
    return EXIT_REGRESSION if comparison["regressions"] else EXIT_SUCCESS


def _report_only() -> int:
    latest_report = REPORT_DIR / "latest.json"
    if not latest_report.exists():
        print("No report found. Run `agentcheck test` first.")
        return EXIT_CONFIG_ERROR
    report_data = read_json(latest_report)
    _print_session_summary_dict(report_data)
    return EXIT_SUCCESS


def _load_tests(root: Path) -> None:
    for file_path in discover_test_files(root):
        import_test_file(file_path)


def _print_session_summary(session: SessionReport) -> None:
    _print_session_summary_dict(session.to_dict())


def _print_session_summary_dict(session_data: dict) -> None:
    for report in session_data["reports"]:
        print(report["test_name"])
        print(f"Runs: {report['total_runs']}")
        print(f"Passed: {report['passed_runs']}")
        print(f"Failed: {report['failed_runs']}")
        print(f"Success rate: {report['success_rate']:.1f}%")
        print(f"Average steps: {report['average_steps']:.1f}")
        if report["failure_reasons"]:
            print("\nFailures:")
            for reason in report["failure_reasons"]:
                print(f"- {reason}")
        print()
    _print_comparison(session_data.get("baseline_comparison", {}))
    if session_data.get("markdown_report_file"):
        print(f"Markdown report: {session_data['markdown_report_file']}")


def _print_comparison(comparison: dict) -> None:
    if not comparison:
        return
    print(comparison["summary"])
    for regression in comparison.get("regressions", []):
        print(
            f"- {regression['test_name']}: "
            f"{regression['previous_success_rate']:.1f}% -> {regression['current_success_rate']:.1f}% "
            f"(step delta {regression['step_delta']:+.1f})"
        )


if __name__ == "__main__":
    sys.exit(main())
