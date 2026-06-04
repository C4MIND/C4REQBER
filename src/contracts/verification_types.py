"""Shared verification types — no implementation, no imports from src.*"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class BackendType(StrEnum):
    """Formal verification backends."""
    Z3 = "z3"
    LEAN4 = "lean4"
    COQ = "coq"
    DAFNY = "dafny"
    AGDA = "agda"
    HOARE = "hoare"


@dataclass
class VerificationResult:
    """Result of formal verification attempt."""
    backend: str
    claim: str
    status: str
    proof_text: str = ""
    error_message: str = ""
    iterations: int = 0
    execution_time_ms: int = 0
    was_timeout: bool = False
    timing_info: dict[str, Any] = field(default_factory=dict)
    proof_code: str = ""
