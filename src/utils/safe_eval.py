"""
C44TCDI: Safe Expression Evaluator
AST-based safe expression evaluator with strict whitelisting.
Zero eval() / exec() in production code.
"""
from __future__ import annotations

import ast
import math
import operator
from typing import Any


class SafeExpressionEvaluator:
    """AST-based safe expression evaluator.

    Whitelist approach: only explicitly allowed node types and operations
    are permitted. Any disallowed node raises ValueError immediately.
    """

    # Allowed AST node types
    ALLOWED_NODES: frozenset[type[ast.AST]] = frozenset({
        ast.Expression,
        ast.BinOp,
        ast.UnaryOp,
        ast.Constant,
        ast.Name,
        ast.Load,
        ast.Add,
        ast.Sub,
        ast.Mult,
        ast.Div,
        ast.Pow,
        ast.USub,
        ast.UAdd,
        ast.Call,
        ast.keyword,
        ast.Compare,
        ast.Eq,
        ast.NotEq,
        ast.Lt,
        ast.LtE,
        ast.Gt,
        ast.GtE,
        ast.BoolOp,
        ast.And,
        ast.Or,
        ast.Not,
    })

    # Allowed binary operators
    BINARY_OPS: dict[type[ast.operator], Any] = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
    }

    # Allowed unary operators
    UNARY_OPS: dict[type[ast.unaryop], Any] = {
        ast.UAdd: operator.pos,
        ast.USub: operator.neg,
    }

    # Allowed functions
    ALLOWED_FUNCTIONS: dict[str, Any] = {
        "abs": abs,
        "min": min,
        "max": max,
        "sin": math.sin,
        "cos": math.cos,
        "exp": math.exp,
        "log": math.log,
        "sqrt": math.sqrt,
    }

    # Allowed variables
    ALLOWED_NAMES: frozenset[str] = frozenset({
        "t", "x", "y", "z", "pi", "e",
    })

    # Constant values
    CONSTANTS: dict[str, float] = {
        "pi": math.pi,
        "e": math.e,
    }

    def __init__(
        self,
        extra_names: dict[str, Any] | None = None,
        extra_functions: dict[str, Any] | None = None,
    ) -> None:
        self.names: dict[str, Any] = dict(self.CONSTANTS)
        self.functions: dict[str, Any] = dict(self.ALLOWED_FUNCTIONS)
        if extra_names:
            self.names.update(extra_names)
        if extra_functions:
            self.functions.update(extra_functions)

    def evaluate(self, expression: str, variables: dict[str, Any] | None = None) -> Any:
        """Safely evaluate a mathematical expression.

        Args:
            expression: The expression string to evaluate.
            variables: Optional dict of variable values to inject.

        Returns:
            The result of the evaluated expression.

        Raises:
            ValueError: If the expression contains disallowed nodes or syntax.
        """
        if not expression or not expression.strip():
            raise ValueError("Expression cannot be empty")

        tree = ast.parse(expression.strip(), mode="eval")

        self._validate_nodes(tree)

        ctx: dict[str, Any] = dict(self.names)
        if variables:
            ctx.update(variables)

        return self._eval_node(tree.body, ctx)

    def _validate_nodes(self, tree: ast.AST) -> None:
        """Recursively validate that all AST nodes are in the allowlist."""
        for node in ast.walk(tree):
            if type(node) not in self.ALLOWED_NODES:
                raise ValueError(
                    f"Disallowed expression element: {type(node).__name__}"
                )

    def _eval_node(self, node: ast.AST, ctx: dict[str, Any]) -> Any:
        """Recursively evaluate an AST node."""
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError(f"Disallowed constant type: {type(node.value).__name__}")

        if isinstance(node, ast.Name):
            if node.id in ctx:
                return ctx[node.id]
            raise NameError(f"name '{node.id}' is not defined")

        if isinstance(node, ast.BinOp):
            op_type = type(node.op)
            if op_type not in self.BINARY_OPS:
                raise ValueError(f"Disallowed binary operator: {op_type.__name__}")
            left = self._eval_node(node.left, ctx)
            right = self._eval_node(node.right, ctx)
            return self.BINARY_OPS[op_type](left, right)

        if isinstance(node, ast.UnaryOp):
            uop_type = type(node.op)
            if uop_type not in self.UNARY_OPS:
                raise ValueError(f"Disallowed unary operator: {uop_type.__name__}")
            operand = self._eval_node(node.operand, ctx)
            return self.UNARY_OPS[uop_type](operand)

        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                raise NameError("only simple function names are allowed")
            func_name = node.func.id
            if func_name not in self.functions:
                raise NameError(f"name '{func_name}' is not defined")
            args = [self._eval_node(arg, ctx) for arg in node.args]
            kwargs = {str(kw.arg): self._eval_node(kw.value, ctx) for kw in node.keywords if kw.arg is not None}
            return self.functions[func_name](*args, **kwargs)

        if isinstance(node, ast.Compare):
            left = self._eval_node(node.left, ctx)
            if len(node.ops) != 1 or len(node.comparators) != 1:
                raise ValueError("Only simple comparisons are allowed")
            right = self._eval_node(node.comparators[0], ctx)
            cmp_type = type(node.ops[0])
            ops = {
                ast.Eq: operator.eq,
                ast.NotEq: operator.ne,
                ast.Lt: operator.lt,
                ast.LtE: operator.le,
                ast.Gt: operator.gt,
                ast.GtE: operator.ge,
            }
            if cmp_type not in ops:
                raise ValueError(f"Disallowed comparison: {cmp_type.__name__}")
            return ops[cmp_type](left, right)

        if isinstance(node, ast.BoolOp):
            values = [self._eval_node(v, ctx) for v in node.values]
            if isinstance(node.op, ast.And):
                return all(values)
            if isinstance(node.op, ast.Or):
                return any(values)
            raise ValueError(f"Disallowed bool op: {type(node.op).__name__}")

        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
            return not self._eval_node(node.operand, ctx)

        raise ValueError(f"Unsupported node type: {type(node).__name__}")


def safe_eval(expression: str, variables: dict[str, Any] | None = None) -> Any:
    """Convenience function: safely evaluate a mathematical expression."""
    return SafeExpressionEvaluator().evaluate(expression, variables)
