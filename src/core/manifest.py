from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any


class ModuleManifest:
    """Scans all src modules and reports import status."""

    def __init__(self) -> None:
        self._src_root = Path(__file__).resolve().parent.parent

    def scan(self) -> dict[str, Any]:
        """Scan all modules under src/ and return status map."""
        modules: dict[str, bool] = {}
        details: dict[str, str] = {}

        for entry in sorted(self._src_root.iterdir()):
            if not entry.is_dir():
                continue
            if entry.name.startswith("_") or entry.name == "__pycache__":
                continue

            init = entry / "__init__.py"
            module_name = f"src.{entry.name}"

            if not init.exists():
                modules[module_name] = False
                details[module_name] = "missing __init__.py"
                continue

            try:
                importlib.import_module(module_name)
                modules[module_name] = True
                details[module_name] = "ok"
            except ImportError as exc:
                modules[module_name] = False
                details[module_name] = f"ImportError: {exc}"

        total = len(modules)
        ok = sum(1 for v in modules.values() if v)
        failed = total - ok

        return {
            "total": total,
            "ok": ok,
            "failed": failed,
            "modules": modules,
            "details": details,
        }

    def report(self) -> str:
        """Return a human-readable status report."""
        status = self.scan()
        lines = [
            f"Module Manifest — {status['ok']}/{status['total']} passing",
            "─" * 50,
        ]
        for mod_name, mod_ok in sorted(status["modules"].items()):
            marker = "✓" if mod_ok else "✗"
            detail = status["details"][mod_name]
            lines.append(f"  {marker} {mod_name}  ({detail})")
        if status["failed"]:
            lines.append(f"\n{status['failed']} module(s) have import errors — review above.")
        return "\n".join(lines)
