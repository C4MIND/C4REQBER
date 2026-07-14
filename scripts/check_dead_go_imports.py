#!/usr/bin/env python3
"""Check for dead Go imports (var _ = X to keep import alive).

For each .go file with such a hack, verify the import is actually unused
in the file body and recommend removal.
"""

import re
import sys
from pathlib import Path


REPO = Path("/Users/figuramax/LocalProjects/C4REQBER/src/tui/v9")


def check_file(path: Path) -> list[tuple[str, str]]:
    """Return list of (import_line, marker_line) that look like dead-import hacks."""
    src = path.read_text()
    if "var _ =" not in src:
        return []
    m = re.search(r"^import \((.*?)\n\)", src, re.MULTILINE | re.DOTALL)
    if not m:
        return []
    import_block = m.group(1)
    body = src[m.end() :]
    findings = []
    for line in import_block.split("\n"):
        s = line.strip()
        if not s or s.startswith("//"):
            continue
        if not s.startswith('"'):
            continue
        pkg = s.strip('"').split("/")[-1].split(" ")[0]
        identifier = pkg.split(".")[-1].split('"')[0]
        # Check if identifier appears in body outside the var _ = hack itself
        body_no_hack = re.sub(
            r"var _ = [a-zA-Z_]+\.[A-Za-z_]+\s*(//.*)?$", "", body, flags=re.MULTILINE
        )
        if identifier not in body_no_hack:
            # Find the marker line
            marker_match = re.search(rf"var _ = {identifier}\.[A-Za-z_]+", body)
            marker = marker_match.group(0) if marker_match else "?"
            findings.append((pkg, marker))
    return findings


def main():
    total = 0
    for f in REPO.rglob("*.go"):
        findings = check_file(f)
        if findings:
            total += len(findings)
            print(f"{f.relative_to(REPO.parent.parent)}")
            for pkg, marker in findings:
                print(f"  {pkg}: '{marker}' — import is dead, remove the var _ and the import line")
    print(f"\nTotal dead-import hacks: {total}")


if __name__ == "__main__":
    main()
