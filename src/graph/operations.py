"""Graph mutation operations: add, remove, update nodes and edges.

DEPRECATED: This module has been split into submodules.
Import from graph.operations instead.
"""
from __future__ import annotations

# Thin wrapper — re-export from new submodules for backward compatibility
from graph.operations.core import (
    add_discovery,
    add_project,
    add_reference,
)
from graph.operations.mutations import (
    add_analogy,
    add_experiment_node,
    add_operator_node,
)
from graph.operations.utils import (
    add_citation,
    add_derivation,
    add_edge,
    add_transformation,
)


__all__ = [
    "add_discovery",
    "add_project",
    "add_reference",
    "add_analogy",
    "add_operator_node",
    "add_experiment_node",
    "add_edge",
    "add_citation",
    "add_derivation",
    "add_transformation",
]
