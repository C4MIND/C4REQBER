# SPDX-License-Identifier: AGPL-3.0
# Copyright (c) 2026 c4reqber Contributors
from __future__ import annotations

import logging
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any


logger = logging.getLogger(__name__)


def _find_ghc() -> str | None:
    for path in ["/opt/homebrew/bin/ghc", "/usr/local/bin/ghc"]:
        if os.path.exists(path):
            return path
    try:
        subprocess.run(["ghc", "--version"], capture_output=True, timeout=5)
        return "ghc"
    except Exception:
        return None


def verify_haskell_typecheck(code: str, module_name: str = "Verified") -> dict[str, Any]:
    """Run GHC type checker on generated Haskell code. Catches type errors, pattern match exhaustiveness, unused bindings."""
    ghc = _find_ghc()
    if not ghc:
        return {"status": "unavailable", "error": "GHC not found", "backend": "haskell-typecheck"}

    with tempfile.TemporaryDirectory() as td:
        src_path = Path(td) / f"{module_name}.hs"
        src_path.write_text(code)

        try:
            result = subprocess.run(
                [ghc, "-Wall", "-Werror", "-fno-code", str(src_path)],
                capture_output=True, text=True, timeout=30,
            )
            stdout = result.stdout.strip()[-500:] if result.stdout else ""
            stderr = result.stderr.strip()[-500:] if result.stderr else ""

            if result.returncode == 0:
                return {
                    "status": "passed",
                    "backend": "haskell-typecheck",
                    "message": "Type checking passed with -Wall -Werror",
                    "warnings": stdout if stdout else "",
                }
            else:
                errors = [line for line in (stderr + "\n" + stdout).splitlines() if "error:" in line.lower() or "warning:" in line.lower()]
                return {
                    "status": "failed",
                    "backend": "haskell-typecheck",
                    "error": errors[-3:] if errors else stderr[-300:],
                    "raw_output": stderr[:500],
                }
        except subprocess.TimeoutExpired:
            return {"status": "timeout", "backend": "haskell-typecheck", "error": "GHC type check timed out (30s)"}
        except Exception as e:
            return {"status": "error", "backend": "haskell-typecheck", "error": str(e)}


def verify_haskell_quickcheck(code: str, module_name: str = "Properties", prop_count: int = 100) -> dict[str, Any]:
    """Run QuickCheck on property definitions found in the code."""
    ghc = _find_ghc()
    if not ghc:
        return {"status": "unavailable", "error": "GHC not found", "backend": "haskell-quickcheck"}

    # Wrap code with QuickCheck main if it contains properties
    if "quickCheck" not in code and "prop_" not in code:
        return {"status": "skipped", "backend": "haskell-quickcheck", "message": "No QuickCheck properties found in code"}

    quickcheck_wrapper = f"""{{-# OPTIONS_GHC -Wno-unused-imports #-}}
import Test.QuickCheck

main :: IO ()
main = mapM_ quickCheck [ {', '.join(f'prop_{name}' for name in _extract_prop_names(code))} ]

{code}
"""

    # Try to compile and run
    with tempfile.TemporaryDirectory() as td:
        src_path = Path(td) / f"{module_name}.hs"
        exe_path = Path(td) / module_name
        src_path.write_text(quickcheck_wrapper)

        try:
            compile_result = subprocess.run(
                [ghc, "-o", str(exe_path), str(src_path)],
                capture_output=True, text=True, timeout=30,
            )
            if compile_result.returncode != 0:
                return {"status": "compile_failed", "backend": "haskell-quickcheck", "error": compile_result.stderr[-300:]}

            run_result = subprocess.run(
                [str(exe_path)],
                capture_output=True, text=True, timeout=30,
            )
            lines = run_result.stdout.strip().splitlines()
            passed = sum(1 for l in lines if "+++ OK" in l)
            failed = sum(1 for l in lines if "*** Failed!" in l)
            return {
                "status": "passed" if failed == 0 else "failed",
                "backend": "haskell-quickcheck",
                "passed": passed,
                "failed": failed,
                "output": lines[-5:] if lines else [],
            }
        except subprocess.TimeoutExpired:
            return {"status": "timeout", "backend": "haskell-quickcheck", "error": "QuickCheck timed out"}
        except Exception as e:
            return {"status": "error", "backend": "haskell-quickcheck", "error": str(e)}


def _extract_prop_names(code: str) -> list[str]:
    import re
    return re.findall(r"prop_(\w+)", code)


def verify_haskell_all(code: str, module_name: str = "Verified") -> dict[str, Any]:
    """Run all Haskell verification backends."""
    results = {
        "typecheck": verify_haskell_typecheck(code, module_name),
    }
    if "quickCheck" in code or "prop_" in code:
        results["quickcheck"] = verify_haskell_quickcheck(code, module_name)
    return results
