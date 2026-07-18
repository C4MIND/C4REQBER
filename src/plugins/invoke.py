"""Plugin invocation helpers — bind common aliases so runners stay honest and working."""

from __future__ import annotations

import inspect
from typing import Any, Callable


# First-arg aliases used across cognitive plugins.
_TEXT_PARAM_NAMES = frozenset(
    {
        "problem",
        "context",
        "situation",
        "original",
        "question",
        "target",
        "challenge",
        "goal",
        "project",
        "decision",
        "hypothesis",
        "hypothesis_text",
    }
)


def invoke_plugin_execute(
    execute_fn: Callable[..., Any],
    *,
    problem: str = "",
    context: str = "",
    domain: str = "",
    **extra: Any,
) -> Any:
    """Call ``plugin.execute`` with signature-aware kwargs (no silent TypeError).

    Runners historically pass ``context=`` / ``problem=`` / ``domain=``. Many
    plugins expect ``target`` / ``situation`` / ``question`` etc. Bind the
    shared text into every matching parameter the callable accepts.
    """
    text = (problem or context or "").strip()
    ctx = (context or problem or "").strip()
    sig = inspect.signature(execute_fn)
    kwargs: dict[str, Any] = {}
    for name, param in sig.parameters.items():
        if name in _TEXT_PARAM_NAMES:
            # Prefer context for "context", problem/text for the rest.
            kwargs[name] = ctx if name == "context" else text
        elif name == "domain":
            kwargs[name] = domain
        elif name in extra:
            kwargs[name] = extra[name]
        elif param.kind == inspect.Parameter.VAR_KEYWORD:
            continue
        elif param.default is inspect.Parameter.empty and name not in kwargs:
            # Required unknown param — leave for TypeError with clear missing name.
            pass
    # Merge extras that match declared params
    for key, value in extra.items():
        if key in sig.parameters and key not in kwargs:
            kwargs[key] = value
    return execute_fn(**kwargs)
