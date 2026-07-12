#!/usr/bin/env python3
"""Smoke-test all verification backends (CVC5, TLA+, Alloy + core). Exit 0 only if all available backends pass."""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from src.config.paths import load_verifiers_env  # noqa: E402

load_verifiers_env()

BOUNDED_TLA = """---- MODULE Counter ----
EXTENDS Naturals
VARIABLE x
Init == x = 0
Next == /\\ x < 5 /\\ x' = x + 1
====
"""

ALLOY_MODEL = "sig Node {}\nrun {} for 3\n"

CVC5_SMT = "(set-logic QF_LIA)\n(declare-const x Int)\n(assert (> x 0))\n(check-sat)\n"


def _check(name: str, available: bool, valid: bool | None, detail: str) -> bool:
    if not available:
        print(f"SKIP {name}: not installed ({detail})")
        return True
    if valid:
        print(f"PASS {name}")
        return True
    print(f"FAIL {name}: {detail}")
    return False


def main() -> int:
    from src.verification.alloy_client import AlloyClient
    from src.verification.cvc5_client import CVC5Client
    from src.verification.tla_client import TLAClient

    ok = True

    cvc5 = CVC5Client()
    if cvc5.test_connection():
        r = cvc5.verify(CVC5_SMT)
        ok &= _check("cvc5", True, r.get("valid", False), r.get("error", r.get("output", "")))
    else:
        _check("cvc5", False, None, "install: bash tools/install-verifiers.sh")

    tla = TLAClient()
    if tla.test_connection():
        r = tla.verify(BOUNDED_TLA)
        ok &= _check("tla", True, r.get("valid", False), r.get("error", r.get("output", "")))
    else:
        _check("tla", False, None, "set TLA_TOOLS_JAR or run install-verifiers.sh")

    alloy = AlloyClient()
    if alloy.test_connection():
        r = alloy.verify(ALLOY_MODEL)
        ok &= _check("alloy", True, r.get("valid", False), r.get("error", r.get("output", "")))
    else:
        _check("alloy", False, None, "brew install alloy-analyzer or set ALLOY_JAR")

    print("")
    if ok:
        print("OK: verifier smoke test passed")
        return 0
    print("ERROR: one or more verifiers failed")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
