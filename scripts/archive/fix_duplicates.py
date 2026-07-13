#!/usr/bin/env python3
"""Remove duplicate exception types from later except blocks."""

import re
from pathlib import Path


PROJECT_DIR = Path("/Users/figuramax/LocalProjects/TURBO-CDI")
SRC_DIR = PROJECT_DIR / "src"


def fix_duplicate_exceptions(filepath: Path) -> int:
    """Fix duplicate exceptions in a file. Returns count of fixes."""
    content = filepath.read_text()
    lines = content.split("\n")
    fixes = 0

    # Track exceptions caught in previous except blocks at same indent level
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if stripped.startswith("except "):
            indent = len(line) - len(line.lstrip())

            # Extract exceptions from this line
            match = re.match(r"\s*except\s+\(?([^:]+)\)?\s*(?:as\s+\w+)?\s*:", line)
            if not match:
                i += 1
                continue

            exc_str = match.group(1).strip()
            if exc_str == "Exception":
                i += 1
                continue

            # Parse exceptions - could be tuple or single
            if exc_str.startswith("(") and exc_str.endswith(")"):
                exc_str = exc_str[1:-1]
            current_exceptions = [e.strip() for e in exc_str.split(",")]

            # Look backward for previous except blocks at same indent
            prev_exceptions = set()
            for j in range(i - 1, -1, -1):
                prev_line = lines[j]
                if not prev_line.strip():
                    continue
                prev_indent = len(prev_line) - len(prev_line.lstrip())
                prev_stripped = prev_line.strip()

                if prev_indent < indent and (
                    prev_stripped.startswith("try:")
                    or prev_stripped.startswith("def ")
                    or prev_stripped.startswith("async def ")
                    or prev_stripped.startswith("class ")
                ):
                    break

                if prev_indent == indent and prev_stripped.startswith("except "):
                    prev_match = re.match(
                        r"\s*except\s+\(?([^:]+)\)?\s*(?:as\s+\w+)?\s*:", prev_line
                    )
                    if prev_match:
                        prev_exc_str = prev_match.group(1).strip()
                        if prev_exc_str.startswith("(") and prev_exc_str.endswith(")"):
                            prev_exc_str = prev_exc_str[1:-1]
                        for e in prev_exc_str.split(","):
                            prev_exceptions.add(e.strip())
                elif prev_indent == indent and not prev_stripped.startswith("except "):
                    break

            # Remove duplicates
            new_exceptions = [e for e in current_exceptions if e not in prev_exceptions]

            if len(new_exceptions) < len(current_exceptions):
                alias_match = re.search(r"as\s+(\w+)", line)
                alias = f" as {alias_match.group(1)}" if alias_match else " as e"

                if len(new_exceptions) == 0:
                    new_line = f"{' ' * indent}except Exception{alias}:"
                elif len(new_exceptions) == 1:
                    new_line = f"{' ' * indent}except {new_exceptions[0]}{alias}:"
                else:
                    new_line = f"{' ' * indent}except ({', '.join(new_exceptions)}){alias}:"

                lines[i] = new_line
                fixes += 1

        i += 1

    if fixes > 0:
        filepath.write_text("\n".join(lines))

    return fixes


def main():
    total_fixes = 0
    modified_files = []

    for filepath in sorted(SRC_DIR.rglob("*.py")):
        rel_path = filepath.relative_to(PROJECT_DIR)
        path_str = str(rel_path)

        if "/test" in path_str or "__pycache__" in path_str or path_str.startswith("tests/"):
            continue

        fixes = fix_duplicate_exceptions(filepath)
        if fixes > 0:
            print(f"Fixed {fixes} in {rel_path}")
            total_fixes += fixes
            modified_files.append(filepath)

    print(f"\nTotal duplicate fixes: {total_fixes}")

    # Verify syntax
    print("\nVerifying syntax...")
    errors = []
    for filepath in modified_files:
        rel = filepath.relative_to(PROJECT_DIR)
        result = os.system(f"cd {PROJECT_DIR} && python3 -m py_compile {rel} > /dev/null 2>&1")
        if result != 0:
            errors.append(str(rel))

    if errors:
        print(f"Syntax errors in: {', '.join(errors)}")
    else:
        print("All modified files compile successfully.")


if __name__ == "__main__":
    import os

    main()
