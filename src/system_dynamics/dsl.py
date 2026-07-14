"""
Stock-Flow DSL parser.

Parses a plain-text DSL to produce an SFModel ready for simulation.
Supports STOCK, FLOW, PARAM, LINK, and TIME directives.
"""
from __future__ import annotations

from .models import Flow, Link, SFModel, Stock, Variable


def parse_dsl(dsl_text: str) -> SFModel:
    """Parse dsl."""
    lines = dsl_text.strip().split("\n")
    model = SFModel(name="parsed", end_time=10.0)

    for line_num, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()

        if not line or line.startswith("#"):
            continue

        try:
            parts = _tokenize(line)
        except ValueError:
            continue

        if not parts:
            continue

        cmd = parts[0].upper()

        if cmd == "STOCK":
            _parse_stock(model, parts, line_num)
        elif cmd == "FLOW":
            _parse_flow(model, parts, line_num)
        elif cmd == "PARAM":
            _parse_variable(model, parts, line_num)
        elif cmd == "LINK":
            _parse_link(model, parts, line_num)
        elif cmd == "TIME":
            _parse_time(model, parts, line_num)

    return model

def _tokenize(line: str) -> list[str]:
    parts: list[str] = []
    i = 0
    while i < len(line):
        if line[i].isspace():
            i += 1
            continue
        if line[i] == '"':
            j = line.index('"', i + 1)
            parts.append(line[i + 1 : j])
            i = j + 1
            continue
        if line[i] in ("+", "-") and i + 1 < len(line) and (line[i + 1].isdigit() or line[i + 1] == "."):
            j = i + 1
            while j < len(line) and (line[j].isdigit() or line[j] == "."):
                j += 1
            parts.append(line[i:j])
            i = j
            continue
        j = i
        while j < len(line) and not line[j].isspace():
            j += 1
        parts.append(line[i:j])
        i = j
    return parts

def _parse_stock(model: SFModel, parts: list[str], line_num: int) -> None:
    if len(parts) < 2:
        raise ValueError(f"Line {line_num}: STOCK requires at least a name")
    name = parts[1]
    initial = 0.0
    unit = "units"
    if len(parts) >= 3:
        try:
            initial = float(parts[2])
        except ValueError:
            raise ValueError(f"Line {line_num}: invalid initial value '{parts[2]}' for stock '{name}'") from None
    if len(parts) >= 4:
        unit = parts[3]
    model.stocks.append(Stock(name=name, initial=initial, unit=unit))

def _parse_flow(model: SFModel, parts: list[str], line_num: int) -> None:
    if len(parts) < 4:
        raise ValueError(f"Line {line_num}: FLOW requires name, source, target")
    name = parts[1]
    source = parts[2]
    target = parts[3]
    expression = "0"
    unit = ""
    if len(parts) > 4:
        expression = " ".join(parts[4:])
    model.flows.append(Flow(name=name, source=source, target=target, expression=expression, unit=unit))

def _parse_variable(model: SFModel, parts: list[str], line_num: int) -> None:
    if len(parts) < 3:
        raise ValueError(f"Line {line_num}: PARAM requires name and expression")
    name = parts[1]
    expression = " ".join(parts[2:])
    model.variables.append(Variable(name=name, expression=expression))

def _parse_link(model: SFModel, parts: list[str], line_num: int) -> None:
    if len(parts) < 3:
        raise ValueError(f"Line {line_num}: LINK requires source and target")
    source = parts[1]
    target = parts[2]
    polarity = "+"
    if len(parts) >= 4 and parts[3] in ("+", "-"):
        polarity = parts[3]
    model.links.append(Link(source=source, target=target, polarity=polarity))

def _parse_time(model: SFModel, parts: list[str], line_num: int) -> None:
    if len(parts) < 3:
        raise ValueError(f"Line {line_num}: TIME requires start_time and end_time")
    try:
        model.start_time = float(parts[1])
        model.end_time = float(parts[2])
    except ValueError:
        raise ValueError(f"Line {line_num}: invalid time values '{parts[1]}' '{parts[2]}'") from None

def dsl_to_string(model: SFModel) -> str:
    """Dsl to string."""
    lines: list[str] = []
    for s in model.stocks:
        lines.append(f"STOCK {s.name} {s.initial} {s.unit}")
    for v in model.variables:
        lines.append(f"PARAM {v.name} {v.expression}")
    for fl in model.flows:
        lines.append(f"FLOW {fl.name} {fl.source} {fl.target} {fl.expression}")
    for lnk in model.links:
        lines.append(f"LINK {lnk.source} {lnk.target} {lnk.polarity}")
    lines.append(f"TIME {model.start_time} {model.end_time}")
    return "\n".join(lines)

__all__ = [
    "parse_dsl",
    "dsl_to_string",
]
