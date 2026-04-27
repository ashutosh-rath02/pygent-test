from __future__ import annotations

import inspect
from dataclasses import dataclass
from typing import Any, Callable


@dataclass(slots=True)
class AgentTestDefinition:
    func: Callable[..., Any]
    name: str
    runs: int
    agent_factory: Callable[[], Any] | None = None


REGISTERED_TESTS: list[AgentTestDefinition] = []


def agent_test(*, runs: int = 1, agent_factory: Callable[[], Any] | None = None):
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        definition = AgentTestDefinition(
            func=func,
            name=func.__name__,
            runs=runs,
            agent_factory=agent_factory,
        )
        setattr(func, "__agentcheck_test__", definition)
        REGISTERED_TESTS.append(definition)
        return func

    return decorator


def resolve_test_argument(definition: AgentTestDefinition) -> tuple[list[Any], dict[str, Any]]:
    signature = inspect.signature(definition.func)
    if not signature.parameters:
        return [], {}
    if len(signature.parameters) != 1:
        raise TypeError(
            f"Test `{definition.name}` must accept zero arguments or one agent argument for MVP support."
        )
    if definition.agent_factory is None:
        raise TypeError(
            f"Test `{definition.name}` expects an agent argument, but no `agent_factory` was provided."
        )
    return [definition.agent_factory()], {}
