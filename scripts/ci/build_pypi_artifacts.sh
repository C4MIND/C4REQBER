#!/usr/bin/env bash
# Build PyPI artifacts with TUI binary intact in the wheel.
#
# `python -m build` (default) builds an sdist first, then builds the wheel
# FROM that sdist. Our sdist excludes src/tui/v9/bin/c4tui-v9* (see
# pyproject.toml), so the hatch force_include hook never sees the binary and
# the published wheel is Python-only. Build the wheel from the working tree
# first, then the sdist.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

python -m build --wheel
python -m build --sdist

if [[ "${C4REQBER_TUI_WHEEL_STRICT:-0}" == "1" ]]; then
  python3 - <<'PY'
from __future__ import annotations

import glob
import sys
import zipfile

wheels = sorted(glob.glob("dist/*.whl"))
if not wheels:
    sys.exit("ERROR: no wheel in dist/ after build")
path = wheels[-1]
with zipfile.ZipFile(path) as zf:
    hits = [
        n
        for n in zf.namelist()
        if n.endswith("c4tui-v9") or n.endswith("c4tui-v9.exe")
    ]
    if not hits:
        sys.exit(f"ERROR: {path} missing c4tui-v9 binary (wheel-from-sdist bug?)")
    for name in hits:
        size = zf.getinfo(name).file_size
        if size <= 0:
            sys.exit(f"ERROR: {name} in {path} has size {size}")
        print(f"OK wheel contains {name} ({size} bytes)")
PY
fi
