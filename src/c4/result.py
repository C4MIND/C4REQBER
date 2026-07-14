# SPDX-License-Identifier: AGPL-3.0
# Copyright (c) 2026 c4reqber Contributors
from __future__ import annotations

from typing import Any, TypedDict


class C4Result(TypedDict, total=False):
    """C4Result."""
    status: str
    data: Any
    errors: list[str]
    metadata: dict[str, Any]
    warnings: list[str]


VALID_STATUSES = frozenset({"success", "error", "partial", "not_applicable"})


def validate_result(result: dict[str, Any]) -> dict[str, Any]:
    """Validate result."""
    if not isinstance(result, dict):
        raise ValueError(f"Expected dict, got {type(result).__name__}")
    status = result.get("status", "")
    if status and status not in VALID_STATUSES:
        raise ValueError(
            f"Invalid status '{status}'. Must be one of: {', '.join(sorted(VALID_STATUSES))}"
        )
    if status == "error" and not result.get("errors"):
        raise ValueError("Status 'error' requires non-empty 'errors' list")
    if status == "success" and "data" not in result:
        raise ValueError("Status 'success' requires 'data' key")
    errors = result.get("errors")
    if errors is not None and not isinstance(errors, list):
        raise ValueError("'errors' must be a list[str]")
    warnings = result.get("warnings")
    if warnings is not None and not isinstance(warnings, list):
        raise ValueError("'warnings' must be a list[str]")
    metadata = result.get("metadata")
    if metadata is not None and not isinstance(metadata, dict):
        raise ValueError("'metadata' must be a dict")
    return result
