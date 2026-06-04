"""Shared C4 types — no implementation, no imports from src.*"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Protocol


class TimeAxis(IntEnum):
    """T-axis: Temporal orientation"""
    PAST = 0
    PRESENT = 1
    FUTURE = 2


class ScaleAxis(IntEnum):
    """S-axis: Level of abstraction"""
    CONCRETE = 0
    ABSTRACT = 1
    META = 2


class AgencyAxis(IntEnum):
    """A-axis: Perspective"""
    SELF = 0
    OTHER = 1
    SYSTEM = 2


@dataclass(frozen=True)
class C4State:
    """A single state in C4Space Z_3^3."""
    T: int  # TimeAxis
    S: int  # ScaleAxis
    A: int  # AgencyAxis

    def to_tuple(self) -> tuple[int, int, int]:
        return (self.T, self.S, self.A)

    @classmethod
    def from_tuple(cls, t: tuple[int, int, int]) -> C4State:
        return cls(T=t[0], S=t[1], A=t[2])


class C4Space(Protocol):
    """Protocol for C4 space implementations."""

    def fingerprint(self, text: str) -> str:
        ...

    def navigate(self, start: C4State, target: C4State) -> list[C4State]:
        ...

    def distance(self, a: C4State, b: C4State) -> int:
        ...


@dataclass
class C4Path:
    """A navigation path through C4Space."""
    states: list[C4State] = field(default_factory=list)
    operators: list[str] = field(default_factory=list)

    def __len__(self) -> int:
        return len(self.states)
