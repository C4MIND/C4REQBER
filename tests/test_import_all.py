"""Import guard: every module under src/ must import cleanly.

Why this exists: import-time crashes (a broken ``from x import y``, a
malformed dataclass, a duplicated decorator) slip past the rest of the
suite whenever the broken module happens to be untested — exactly how a
triple-@dataclass crash in the REPL and a dead-on-arrival import in
terminal.py survived thousands of passing tests. This test imports every
src module so CI fails loudly the moment one stops importing.

The sweep runs in a FRESH subprocess on purpose: importing everything in
the pytest process would inherit ``sys.modules`` pollution from earlier
tests (mocks, partial imports, sys.path shims that shadow ``src.agents``
etc.), producing false failures. A clean interpreter sees the real state.

Genuinely-optional third-party dependencies (torch, gensim, z3, ...) are
not installed in every environment, so a ModuleNotFoundError naming one
of them is skipped rather than failed. Anything else — a SyntaxError, a
TypeError at class-construction time, a missing first-party module, a
NameError — is a real breakage and fails the test.
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys

_REPO = pathlib.Path(__file__).resolve().parent.parent

# Sweep program, run in a clean interpreter. argv: <repo_root> <out_json>.
_SWEEP = r"""
import importlib, json, pathlib, sys

repo = pathlib.Path(sys.argv[1])
out = pathlib.Path(sys.argv[2])
# Self-contained path setup (don't rely on PYTHONPATH being set in CI).
sys.path.insert(0, str(repo / "src"))
sys.path.insert(0, str(repo))

OPTIONAL_DEPS = {
    "torch", "transformers", "sentence_transformers", "gensim", "numba",
    "z3", "pymc", "arviz", "dowhy", "wasmtime", "newton", "sklearn",
    "matplotlib", "plotly", "redis", "sqlalchemy", "asyncpg", "alembic",
    "psycopg2", "feedparser", "Bio", "sentry_sdk", "opentelemetry", "mcp",
}

def missing_optional(exc):
    if type(exc).__name__ != "ModuleNotFoundError":
        return False
    name = (getattr(exc, "name", "") or "").split(".")[0]
    return name in OPTIONAL_DEPS

src = repo / "src"
mods = set()
for p in src.rglob("*.py"):
    if "__pycache__" in p.parts:
        continue
    parts = list(p.with_suffix("").relative_to(src.parent).parts)
    if parts[-1] == "__init__":
        parts = parts[:-1]
    mods.add(".".join(parts))

failures = []
for m in sorted(mods):
    try:
        importlib.import_module(m)
    except BaseException as exc:  # classify everything
        if not missing_optional(exc):
            failures.append(f"{m}: {type(exc).__name__}: {exc}")

out.write_text(json.dumps(failures))
"""


def test_all_src_modules_import(tmp_path):
    out = tmp_path / "import_failures.json"
    proc = subprocess.run(
        [sys.executable, "-c", _SWEEP, str(_REPO), str(out)],
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert out.exists(), (
        "import sweep subprocess did not produce output "
        f"(rc={proc.returncode}):\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
    )
    failures = json.loads(out.read_text())
    assert not failures, (
        f"{len(failures)} src module(s) failed to import in a clean interpreter:\n  "
        + "\n  ".join(failures)
    )
