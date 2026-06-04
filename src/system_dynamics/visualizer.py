"""
Causal Loop Diagram (CLD) text renderer.

Produces ASCII-art and Graphviz DOT representations of system dynamics
models for rapid visual inspection.
"""
from __future__ import annotations

from .models import SFModel


def render_ascii(model: SFModel) -> str:
    """Render ascii."""
    lines: list[str] = []
    lines.append(f"┌─ CLD: {model.name} {'─' * max(1, 50 - len(model.name))}")
    lines.append("│")

    node_map: dict[str, str] = {}
    for _i, s in enumerate(model.stocks):
        symbol = f"[{s.name}]"
        node_map[s.name] = symbol
        lines.append(f"│  {symbol} = {s.initial:.1f} {s.unit}")

    for v in model.variables:
        symbol = f"({v.name})"
        node_map[v.name] = symbol
        lines.append(f"│  {symbol} = {v.expression}")

    if model.links:
        lines.append("│")
        lines.append("│  Causality:")

    for lnk in model.links:
        src_sym = node_map.get(lnk.source, lnk.source)
        tgt_sym = node_map.get(lnk.target, lnk.target)
        arrow = "──▶ +" if lnk.polarity == "+" else "──▶ -"
        lines.append(f"│    {src_sym} {arrow} {tgt_sym}")

    lines.append("│")
    lines.append(f"│  Flows ({len(model.flows)}):")
    for fl in model.flows:
        src = fl.source if fl.source != "Stock" else "○"
        tgt = fl.target if fl.target != "Stock" else "○"
        lines.append(f"│    {src} ──{fl.name}──▶ {tgt}  [{fl.expression}]")

    lines.append("│")
    lines.append(f"│  T = [{model.start_time}, {model.end_time}], dt = {model.dt}")
    lines.append(f"└{'─' * 62}")
    return "\n".join(lines)

def render_dot(model: SFModel, horizontal: bool = False) -> str:
    """Render dot."""
    lines: list[str] = []
    rankdir = "LR" if horizontal else "TB"
    lines.append(f"digraph {model.name} {{")
    lines.append(f'  rankdir={rankdir};')
    lines.append('  labelloc="t";')
    lines.append(f'  label="{model.name}";')
    lines.append('  fontsize=16;')
    lines.append('  node [fontname="Helvetica"];')
    lines.append('  edge [fontname="Helvetica", fontsize=11];')

    for s in model.stocks:
        lines.append(f'  "{s.name}" [shape=box, style=filled, fillcolor="#cfe2ff", '
                     f'label="{s.name}\\n({s.initial} {s.unit})"];')

    for v in model.variables:
        lines.append(f'  "{v.name}" [shape=ellipse, style=filled, fillcolor="#fff3cd", '
                     f'label="{v.name}\\n{v.expression}"];')

    for fl in model.flows:
        src = fl.source if fl.source != "Stock" else "cloud_src"
        tgt = fl.target if fl.target != "Stock" else "cloud_tgt"
        if src == "cloud_src":
            lines.append(f'  "{src}" [shape=none, label=""];')
        if tgt == "cloud_tgt":
            lines.append(f'  "{tgt}" [shape=none, label=""];')
        lines.append(f'  "{src}" -> "{tgt}" [label="{fl.name}\\n{fl.expression}", '
                     f'fontsize=10, style=dashed];')

    for lnk in model.links:
        polarity_label = "S" if lnk.polarity == "+" else "O"
        color = "#198754" if lnk.polarity == "+" else "#dc3545"
        lines.append(f'  "{lnk.source}" -> "{lnk.target}" [label=" {polarity_label}", '
                     f'color="{color}", fontcolor="{color}"];')

    lines.append("}")
    return "\n".join(lines)

def detect_loops(model: SFModel) -> list[tuple[list[str], bool]]:
    """Detect loops."""
    loops: list[tuple[list[str], bool]] = []
    adj: dict[str, list[tuple[str, str]]] = {}

    for lnk in model.links:
        adj.setdefault(lnk.source, []).append((lnk.target, lnk.polarity))

    def dfs(start: str, current: str, path: list[str], neg_count: int) -> None:
        for nxt, pol in adj.get(current, []):
            if nxt == start and len(path) >= 2:
                total_neg = neg_count + (1 if pol == "-" else 0)
                loops.append((path[:] + [nxt], total_neg % 2 == 1))
                continue
            if nxt in path or len(path) > 10:
                continue
            new_neg = neg_count + (1 if pol == "-" else 0)
            dfs(start, nxt, path + [nxt], new_neg)

    for node in adj:
        dfs(node, node, [node], 0)

    unique: dict[tuple[str, ...], tuple[list[str], bool]] = {}
    for path, is_balancing in loops:
        key = tuple(sorted(path))
        if key not in unique:
            unique[key] = (path, is_balancing)
    return list(unique.values())

__all__ = [
    "render_ascii",
    "render_dot",
    "detect_loops",
]
