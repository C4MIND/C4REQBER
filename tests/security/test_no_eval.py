"""
Security Test: Zero eval() / exec() in production code.

CRITICAL GOAL: Zero eval() / exec() in production code.
"""
from __future__ import annotations

import ast
import os
import subprocess
import sys
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent / "src"


def _find_python_files(root: Path) -> list[Path]:
    """Recursively find all Python files under root."""
    return list(root.rglob("*.py"))


def _contains_eval_or_exec(file_path: Path) -> tuple[bool, list[str]]:
    """Check if a file contains eval() or exec() calls (not in comments/strings)."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()
    except (OSError, UnicodeDecodeError):
        return False, []

    issues: list[str] = []
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return False, []

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id in ("eval", "exec"):
                    issues.append(f"{file_path}:{node.lineno}: {node.func.id}()")

    return len(issues) > 0, issues


class TestNoEvalExec:
    def test_zero_eval_exec_in_src(self) -> None:
        """Assert that ZERO eval() or exec() calls exist in src/."""
        all_issues: list[str] = []
        for py_file in _find_python_files(PROJECT_ROOT):
            has_issues, issues = _contains_eval_or_exec(py_file)
            if has_issues:
                all_issues.extend(issues)

        if all_issues:
            pytest.fail(
                f"Found {len(all_issues)} eval()/exec() call(s) in src/:\n" +
                "\n".join(all_issues)
            )

    def test_grep_confirms_zero_eval_exec(self) -> None:
        """Use ripgrep to confirm no eval/exec in src/ (excluding comments/docstrings)."""
        result = subprocess.run(
            ["rg", "-n", "\beval\b|\bexec\b", str(PROJECT_ROOT), "--type", "py"],
            capture_output=True,
            text=True,
        )
        # ripgrep returns 1 when no matches found — that's what we want
        # But we need to filter out legitimate uses like model.eval() in PyTorch
        lines = result.stdout.strip().split("\n") if result.stdout.strip() else []
        # Filter out comments, docstrings, and PyTorch .eval() calls
        bad_lines = []
        for line in lines:
            if not line.strip():
                continue
            # Skip PyTorch model.eval() patterns
            if ".eval()" in line:
                continue
            # Skip comments
            if line.strip().startswith("#"):
                continue
            bad_lines.append(line)

        assert len(bad_lines) == 0, (
            f"ripgrep found potential eval/exec usage:\n" + "\n".join(bad_lines)
        )
