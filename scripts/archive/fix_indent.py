#!/usr/bin/env python3
"""Repair all files corrupted by the bad indent fixer"""
import re
from pathlib import Path


PATTERNS_DIR = Path("/Users/figuramax/LocalProjects/TURBO-CDI/src/patterns")

def repair_file(fp: Path) -> bool:
    lines = []
    fixed = False
    content_lines = fp.read_text().split('\n')

    for line in content_lines:
        # Pattern 1: lines like "4    if hypothesis is None:" (digit prefix + code)
        # where the digit represents the indent level
        m = re.match(r'^(\d+)(\s+)(.+)$', line)
        if m:
            digit = int(m.group(1))
            rest = m.group(2) + m.group(3)
            # Reconstruct with proper spaces
            lines.append(' ' * digit + rest)
            fixed = True
        # Pattern 2: lines like "# type: ignore for continue" after a broken line continuation
        elif re.match(r'\s*# type: ignore', line):
            lines.append(line)
        else:
            lines.append(line)

    if fixed:
        fp.write_text('\n'.join(lines))
        print(f"  REPAIRED: {fp.relative_to(PATTERNS_DIR)}")
    return fixed


def main():
    count = 0
    for fp in sorted(PATTERNS_DIR.rglob("*.py")):
        if repair_file(fp):
            count += 1
    print(f"\nRepaired {count} files")


if __name__ == "__main__":
    main()
