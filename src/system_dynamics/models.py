"""
System Dynamics Stock-Flow DSL data models.

Provides lightweight dataclasses for DSL parsing, distinct from the
heavier stock_flow.py domain objects used by the ODE compiler.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Stock:
    """Stock."""
    name: str
    initial: float = 0.0
    unit: str = "units"

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("Stock name must be non-empty")

@dataclass
class Flow:
    """Flow."""
    name: str
    source: str
    target: str
    expression: str
    unit: str = ""

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("Flow name must be non-empty")

@dataclass
class Variable:
    """Variable."""
    name: str
    expression: str
    unit: str = ""

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("Variable name must be non-empty")

@dataclass
class Link:
    """Link."""
    source: str
    target: str
    polarity: str = "+"

    def __post_init__(self) -> None:
        if self.polarity not in ("+", "-"):
            raise ValueError(f"Polarity must be '+' or '-', got '{self.polarity}'")

@dataclass
class SFModel:
    """SFModel."""
    name: str
    stocks: list[Stock] = field(default_factory=list[Any])
    flows: list[Flow] = field(default_factory=list[Any])
    variables: list[Variable] = field(default_factory=list[Any])
    links: list[Link] = field(default_factory=list[Any])
    start_time: float = 0.0
    end_time: float = 10.0
    dt: float = 0.1

    def get_stock(self, name: str) -> Stock | None:
        """Get stock."""
        for s in self.stocks:
            if s.name == name:
                return s
        return None

    def get_variable(self, name: str) -> Variable | None:
        """Get variable."""
        for v in self.variables:
            if v.name == name:
                return v
        return None

    def validate(self) -> list[str]:
        """Validate."""
        errors: list[str] = []
        stock_names = {s.name for s in self.stocks}
        for fl in self.flows:
            if fl.source != "Stock" and fl.source not in stock_names:
                errors.append(f"Flow '{fl.name}' references unknown source '{fl.source}' (known stocks: {stock_names})")
            if fl.target != "Stock" and fl.target not in stock_names:
                errors.append(f"Flow '{fl.name}' references unknown target '{fl.target}' (known stocks: {stock_names})")
        return errors

__all__ = [
    "Stock",
    "Flow",
    "Variable",
    "Link",
    "SFModel",
]
