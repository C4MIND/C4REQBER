#!/usr/bin/env python3
"""Add minimal docstrings to public functions/classes in src/ that are missing them."""

from __future__ import annotations

import ast
import os
from collections.abc import Iterator
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parent.parent / "src"

EXCLUDE_DIRS = {"tests", "archive", "wasm", "patterns/v6_legacy"}

PREFIX_MAP: dict[str, str] = {
    "get_": "Get",
    "set_": "Set",
    "create_": "Create",
    "delete_": "Delete",
    "update_": "Update",
    "check_": "Check",
    "validate_": "Validate",
    "compute_": "Compute",
    "calculate_": "Calculate",
    "run_": "Run",
    "make_": "Make",
    "build_": "Build",
    "load_": "Load",
    "save_": "Save",
    "parse_": "Parse",
    "find_": "Find",
    "fetch_": "Fetch",
    "init_": "Initialize",
    "apply_": "Apply",
    "register_": "Register",
    "render_": "Render",
    "generate_": "Generate",
    "search_": "Search",
    "scan_": "Scan",
    "match_": "Match",
    "estimate_": "Estimate",
    "export_": "Export",
    "import_": "Import",
    "extract_": "Extract",
    "verify_": "Verify",
    "resolve_": "Resolve",
    "format_": "Format",
    "convert_": "Convert",
    "read_": "Read",
    "write_": "Write",
    "start_": "Start",
    "stop_": "Stop",
    "has_": "Check if has",
    "is_": "Check if",
    "can_": "Check if can",
    "should_": "Determine if should",
}


def snake_to_title(name: str) -> str:
    """Convert snake_case name to Title Case docstring."""
    normalized = name.rstrip("_")

    for prefix, replacement in PREFIX_MAP.items():
        if normalized.startswith(prefix) and len(normalized) > len(prefix):
            rest = normalized[len(prefix) :].replace("_", " ")
            return f"{replacement} {rest}."

    title = normalized.replace("_", " ")
    if not title:
        return "Placeholder."
    return title[0].upper() + title[1:] + "."


def has_docstring(node: ast.AST) -> bool:
    """Check if an AST node has a docstring."""
    body = getattr(node, "body", None)
    if not body or not isinstance(body, list) or len(body) == 0:
        return False
    first = body[0]
    if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant):
        return isinstance(first.value.value, str)
    return False


def count_body_lines(node: ast.AST) -> int:
    """Count statement lines in a function/class body (excluding docstring)."""
    body = getattr(node, "body", [])
    if not body:
        return 0
    if has_docstring(node):
        return len(body) - 1
    return len(body)


def get_first_real_body_lineno(node: ast.AST) -> int:
    """Get the 1-indexed line of the first real body content.

    Handles decorated functions/classes by returning the decorator's line
    instead of the definition line.
    """
    body = getattr(node, "body", [])
    if not body:
        return node.lineno

    first = body[0]
    decorator_list = getattr(first, "decorator_list", None)
    if decorator_list and len(decorator_list) > 0:
        # Return the line of the first decorator
        return decorator_list[0].lineno

    return first.lineno


def find_missing_docstrings(tree: ast.AST) -> list[tuple[ast.AST, str]]:
    """Find functions/classes in AST that need docstrings. Returns (node, kind)."""
    results: list[tuple[ast.AST, str]] = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith("_"):
                continue
            if has_docstring(node):
                continue
            if count_body_lines(node) <= 1:
                continue
            results.append((node, "function"))

        elif isinstance(node, ast.ClassDef):
            if node.name.startswith("_"):
                continue
            if has_docstring(node):
                continue
            if count_body_lines(node) == 0:
                continue
            results.append((node, "class"))

    return results


def iter_py_files(root: Path) -> Iterator[Path]:
    """Yield all .py files under root, excluding EXCLUDE_DIRS."""
    for dirpath, dirnames, filenames in os.walk(root):
        rel = Path(dirpath).relative_to(root)
        rel_str = str(rel)
        excluded = False
        for excl in EXCLUDE_DIRS:
            if rel_str == excl or rel_str.startswith(excl + os.sep):
                excluded = True
                break
        if excluded:
            dirnames.clear()
            continue

        for fname in sorted(filenames):
            if fname.endswith(".py"):
                yield Path(dirpath) / fname


def insert_docstring(filepath: Path, nodes: list[tuple[ast.AST, str]]) -> int:
    """Insert docstrings into a file. Returns number of docstrings added."""
    with open(filepath) as f:
        lines = f.readlines()

    edits: list[tuple[int, str]] = []
    for node, _kind in nodes:
        body = getattr(node, "body", [])
        if not body:
            continue

        # Insert BEFORE the first real body line
        insert_at = get_first_real_body_lineno(node) - 1  # 0-indexed

        # Determine indentation: node.col_offset + 4
        indent_level = node.col_offset + 4

        name = node.name
        docstring_text = snake_to_title(name)
        doc_line = f'{" " * indent_level}"""{docstring_text}"""\n'

        edits.append((insert_at, doc_line))

    if not edits:
        return 0

    # Sort by insertion position descending to avoid shifting
    edits.sort(key=lambda x: x[0], reverse=True)

    result_lines = list(lines)
    added = 0
    for insert_at, doc_line in edits:
        result_lines.insert(insert_at, doc_line)
        added += 1

    with open(filepath, "w") as f:
        f.writelines(result_lines)

    return added


def main() -> None:
    total_processed = 0
    total_added = 0
    files_modified = 0

    for py_file in iter_py_files(SRC_DIR):
        try:
            source = py_file.read_text()
        except Exception:
            continue

        try:
            tree = ast.parse(source, filename=str(py_file))
        except SyntaxError:
            print(f"  SKIP (syntax error): {py_file.relative_to(SRC_DIR.parent)}")
            continue

        missing = find_missing_docstrings(tree)
        if not missing:
            continue

        added = insert_docstring(py_file, missing)
        total_processed += len(missing)
        total_added += added
        if added > 0:
            files_modified += 1
            rel = py_file.relative_to(SRC_DIR.parent)
            print(f"  {rel}: +{added} docstring(s)")

    print()
    print(f"Total functions/classes processed: {total_processed}")
    print(f"Total docstrings added: {total_added}")
    print(f"Total files modified: {files_modified}")


if __name__ == "__main__":
    main()
