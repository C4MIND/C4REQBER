"""
Security Test: Zero eval() / exec() in production code.

CRITICAL GOAL: Zero eval() / exec() in production code.
"""

from __future__ import annotations

import ast
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent / "src"


def _find_python_files(root: Path) -> list[Path]:
    """Recursively find all Python files under root."""
    return list(root.rglob("*.py"))


# Known legitimate eval/exec uses in the codebase.
# These are vetted exceptions — do NOT add new entries without code review.
KNOWN_EXCEPTIONS = frozenset(
    {
        Path(__file__).resolve().parent.parent.parent / "src" / "skills" / "calculator.py",
        Path(__file__).resolve().parent.parent.parent / "src" / "simulations" / "boolnet_bridge.py",
    }
)


def _contains_eval_or_exec(file_path: Path) -> tuple[bool, list[str]]:
    """Check if a file contains eval() or exec() calls (not in comments/strings)."""
    if file_path.resolve() in KNOWN_EXCEPTIONS:
        return False, []

    try:
        with open(file_path, encoding="utf-8") as f:
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
                f"Found {len(all_issues)} eval()/exec() call(s) in src/:\n" + "\n".join(all_issues)
            )

    def test_grep_confirms_zero_eval_exec(self) -> None:
        """Use ripgrep to confirm no eval/exec in src/ (excluding comments/docstrings).

        This test requires ripgrep (rg) for accurate word-boundary matching.
        The AST-based test_zero_eval_exec_in_src is the primary security check;
        this test is a secondary confirmation and is skipped when rg is unavailable.
        """
        if not shutil.which("rg"):
            pytest.skip("ripgrep (rg) not available — relying on AST-based check above")
            return

        known_exception_paths = {str(exc_path) for exc_path in KNOWN_EXCEPTIONS}

        result = subprocess.run(
            ["rg", "-n", "\beval\b|\bexec\b", str(PROJECT_ROOT), "--type", "py"],
            capture_output=True,
            text=True,
        )

        lines = result.stdout.strip().split("\n") if result.stdout.strip() else []
        bad_lines = []
        for line in lines:
            if not line.strip():
                continue
            # Skip known exception files
            if any(exc_path in line for exc_path in known_exception_paths):
                continue
            # Skip PyTorch model.eval() patterns
            if ".eval()" in line:
                continue
            # Skip comments
            if line.strip().startswith("#"):
                continue
            bad_lines.append(line)

        assert len(bad_lines) == 0, "ripgrep found potential eval/exec usage:\n" + "\n".join(
            bad_lines
        )
