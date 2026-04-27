from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .result import AgentResult


@dataclass(slots=True)
class AssertionRecord:
    name: str
    passed: bool
    message: str


class BehaviorAssertionError(AssertionError):
    def __init__(self, record: AssertionRecord, result: AgentResult):
        super().__init__(record.message)
        self.record = record
        self.result = result


class Expectation:
    def __init__(self, result: AgentResult):
        self.result = result

    def _tool_names(self) -> list[str]:
        return [tool.name for tool in self.result.tool_calls]

    def _check(self, name: str, passed: bool, success_message: str, failure_message: str) -> "Expectation":
        record = AssertionRecord(
            name=name,
            passed=passed,
            message=success_message if passed else failure_message,
        )
        if not passed:
            raise BehaviorAssertionError(record, self.result)
        return self

    def used_tool(self, tool_name: str) -> "Expectation":
        names = self._tool_names()
        return self._check(
            "used_tool",
            tool_name in names,
            f"Observed tool `{tool_name}`.",
            f"Expected tool `{tool_name}` to be called, but saw {names or 'no tools'}.",
        )

    def did_not_use_tool(self, tool_name: str) -> "Expectation":
        names = self._tool_names()
        return self._check(
            "did_not_use_tool",
            tool_name not in names,
            f"Tool `{tool_name}` was not used.",
            f"Expected tool `{tool_name}` to be avoided, but it was called.",
        )

    def used_tools_in_order(self, tool_names: Iterable[str]) -> "Expectation":
        ordered = list(tool_names)
        seen = self._tool_names()
        position = 0
        for name in seen:
            if position < len(ordered) and name == ordered[position]:
                position += 1
        return self._check(
            "used_tools_in_order",
            position == len(ordered),
            f"Observed tools in order {ordered}.",
            f"Expected tools in order {ordered}, but saw {seen or 'no tools'}.",
        )

    def steps_less_than(self, limit: int) -> "Expectation":
        return self._check(
            "steps_less_than",
            self.result.steps < limit,
            f"Completed in {self.result.steps} steps, below limit {limit}.",
            f"Expected fewer than {limit} steps, but saw {self.result.steps}.",
        )

    def finished_successfully(self) -> "Expectation":
        return self._check(
            "finished_successfully",
            not self.result.errors and bool(self.result.final_output.strip()),
            "Run finished successfully.",
            "Expected a successful finish, but errors were present or final output was empty.",
        )

    def did_not_error(self) -> "Expectation":
        return self._check(
            "did_not_error",
            not self.result.errors,
            "Run completed without errors.",
            f"Expected no errors, but saw: {self.result.errors}.",
        )

    def final_output_contains(self, text: str) -> "Expectation":
        return self._check(
            "final_output_contains",
            text in self.result.final_output,
            f"Final output contained `{text}`.",
            f"Expected final output to contain `{text}`.",
        )

    def final_output_does_not_contain(self, text: str) -> "Expectation":
        return self._check(
            "final_output_does_not_contain",
            text not in self.result.final_output,
            f"Final output did not contain `{text}`.",
            f"Expected final output to avoid `{text}`.",
        )

    def did_not_claim_confirmation_without_tool(self, required_tool: str | None = None) -> "Expectation":
        confirmation_phrases = (
            "booked",
            "confirmed",
            "reservation complete",
            "refund issued",
            "completed successfully",
        )
        final_output = self.result.final_output.lower()
        claims_success = any(phrase in final_output for phrase in confirmation_phrases)
        successful_tools = [tool.name for tool in self.result.tool_calls if tool.success]
        tool_to_check = required_tool
        if tool_to_check is None and successful_tools:
            tool_to_check = successful_tools[-1]
        has_supporting_tool = bool(tool_to_check and tool_to_check in successful_tools)
        passed = not claims_success or has_supporting_tool
        detail = tool_to_check or "a successful tool call"
        return self._check(
            "did_not_claim_confirmation_without_tool",
            passed,
            "No unsupported confirmation claim detected.",
            f"Agent claimed success in final output without evidence from {detail}.",
        )


def expect(result: AgentResult) -> Expectation:
    return Expectation(result)
