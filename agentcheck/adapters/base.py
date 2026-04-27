from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from agentcheck.result import AgentResult


class SupportsRun(Protocol):
    def run(self, prompt: str) -> Any:
        ...


@dataclass(slots=True)
class AdapterContext:
    prompt: str
    raw_result: Any


class BaseAdapter:
    def run(self, agent: SupportsRun, prompt: str) -> AgentResult:
        raise NotImplementedError
