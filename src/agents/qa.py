"""c4reqber QA Controller — Automated Quality Assurance.

Runs lint, typecheck, tests, version sync, secret scan, and
circular-import detection. Produces a structured report that
can be consumed by the CLI (`blast qa`) or CI pipeline.
"""
from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class QACheck:
    """Result of a single QA check."""

    name: str
    passed: bool
    duration_ms: float
    stdout: str = ""
    stderr: str = ""
    errors: list[str] = field(default_factory=list)


@dataclass
class QAResult:
    """Complete QA report."""

    passed: int = 0
    failed: int = 0
    total: int = 0
    checks: dict[str, QACheck] = field(default_factory=dict)
    duration_sec: float = 0.0

    @property
    def success_rate(self) -> float:
        return self.passed / self.total if self.total > 0 else 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "failed": self.failed,
            "total": self.total,
            "success_rate": self.success_rate,
            "duration_sec": self.duration_sec,
            "checks": {
                name: {
                    "passed": c.passed,
                    "duration_ms": c.duration_ms,
                    "errors": c.errors,
                }
                for name, c in self.checks.items()
            },
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)


class QAController:
    """Automated quality assurance for the c4reqber codebase.

    Usage::

        qa = QAController(project_root=Path("/path/to/c4reqber"))
        result = qa.run_all()
        print(result.to_json())
    """

    def __init__(self, project_root: Path | None = None) -> None:
        self.root = project_root or Path(__file__).resolve().parents[2]
        self._venv_bin = self._find_venv_bin()

    def _find_venv_bin(self) -> Path:
        """Locate virtual environment bin directory."""
        candidates = [
            self.root / ".venv" / "bin",
            self.root / "venv" / "bin",
            Path.home() / ".local" / "bin",
        ]
        for c in candidates:
            if c.exists():
                return c
        return Path("/usr/local/bin")

    def _run_cmd(
        self,
        cmd: list[str],
        cwd: Path | None = None,
        timeout: int = 120,
    ) -> tuple[int, str, str, float]:
        """Run a shell command and return (rc, stdout, stderr, duration_ms)."""
        import time

        start = time.perf_counter()
        try:
            from src.utils.safe_subprocess import safe_subprocess_run
            result = safe_subprocess_run(
                cmd,
                cwd=cwd or self.root,
                timeout=timeout,
                capture_output=True,
                text=True,
            )
        except subprocess.TimeoutExpired:
            duration = (time.perf_counter() - start) * 1000
            return 1, "", "Timeout", duration
        except FileNotFoundError as e:
            duration = (time.perf_counter() - start) * 1000
            return 127, "", str(e), duration

        duration = (time.perf_counter() - start) * 1000
        return result.returncode, result.stdout, result.stderr, duration

    # ------------------------------------------------------------------
    # Individual checks
    # ------------------------------------------------------------------

    def check_ruff(self) -> QACheck:
        """Run ruff linter on src/."""
        ruff = self._venv_bin / "ruff"
        rc, stdout, stderr, duration = self._run_cmd([str(ruff), "check", "src/"])
        errors: list[str] = []
        if rc != 0:
            errors = [line for line in (stdout + stderr).splitlines() if line.strip()]
        return QACheck(
            name="ruff",
            passed=rc == 0,
            duration_ms=duration,
            stdout=stdout,
            stderr=stderr,
            errors=errors[:20],  # cap at 20
        )

    def check_mypy(self) -> QACheck:
        """Run mypy type checker."""
        mypy = self._venv_bin / "mypy"
        rc, stdout, stderr, duration = self._run_cmd([str(mypy), "src/"])
        errors: list[str] = []
        if rc != 0:
            errors = [line for line in (stdout + stderr).splitlines() if line.strip()]
        return QACheck(
            name="mypy",
            passed=rc == 0,
            duration_ms=duration,
            stdout=stdout,
            stderr=stderr,
            errors=errors[:20],
        )

    def check_pytest(self) -> QACheck:
        """Run pytest test suite."""
        pytest = self._venv_bin / "pytest"
        rc, stdout, stderr, duration = self._run_cmd(
            [str(pytest), "-xvs", "--tb=short", "-q"],
            timeout=300,
        )
        errors: list[str] = []
        if rc != 0:
            errors = [line for line in (stdout + stderr).splitlines() if line.strip()]
        return QACheck(
            name="pytest",
            passed=rc == 0,
            duration_ms=duration,
            stdout=stdout,
            stderr=stderr,
            errors=errors[:20],
        )

    def check_version_sync(self) -> QACheck:
        """Ensure version is consistent across files."""
        import time

        start = time.perf_counter()
        errors: list[str] = []

        # Read pyproject.toml version
        pyproject = self.root / "pyproject.toml"
        if pyproject.exists():
            content = pyproject.read_text()
            import re

            m = re.search(r'version\s*=\s*"([^"]+)"', content)
            pyproject_version = m.group(1) if m else None
        else:
            pyproject_version = None
            errors.append("pyproject.toml not found")

        # Check AGENTS.md
        agents_md = self.root / "AGENTS.md"
        if agents_md.exists():
            content = agents_md.read_text()
            m = re.search(r'Version:\s*([\d.]+)', content)
            agents_version = m.group(1) if m else None
            if pyproject_version and agents_version and pyproject_version != agents_version:
                errors.append(
                    f"Version mismatch: pyproject.toml={pyproject_version}, AGENTS.md={agents_version}"
                )

        # Check README.md
        readme = self.root / "README.md"
        if readme.exists():
            content = readme.read_text()
            versions = re.findall(r'version-([\d.]+)', content)
            if pyproject_version and versions:
                unique = set(versions)
                if len(unique) > 1 or (pyproject_version not in unique):
                    errors.append(
                        f"Version mismatch: pyproject.toml={pyproject_version}, README badges={unique}"
                    )

        duration = (time.perf_counter() - start) * 1000
        return QACheck(
            name="version_sync",
            passed=len(errors) == 0,
            duration_ms=duration,
            errors=errors,
        )

    def check_secrets(self) -> QACheck:
        """Scan for committed secrets."""
        import time

        start = time.perf_counter()
        errors: list[str] = []

        # Check for .env files in git index
        rc, stdout, _, _ = self._run_cmd(
            ["git", "ls-files"],
        )
        if rc == 0:
            tracked = stdout.splitlines()
            secret_patterns = [".env", ".env.development", ".env.production", "api_key", "secret"]
            for f in tracked:
                f_lower = f.lower()
                for pat in secret_patterns:
                    if pat in f_lower and not f_lower.endswith(".example"):
                        errors.append(f"Potential secret tracked: {f}")

        # Check for hardcoded API keys in src/
        key_patterns = [
            r'sk-or-[a-zA-Z0-9]{20,}',
            r'sk-[a-zA-Z0-9]{20,}',
            r'nvapi-[a-zA-Z0-9]{20,}',
            r'Bearer\s+[a-zA-Z0-9]{20,}',
        ]
        for pyfile in self.root.rglob("src/**/*.py"):
            content = pyfile.read_text(errors="ignore")
            for pat in key_patterns:
                import re

                if re.search(pat, content):
                    errors.append(f"Potential API key in {pyfile.relative_to(self.root)}")
                    break  # one error per file is enough

        duration = (time.perf_counter() - start) * 1000
        return QACheck(
            name="secrets",
            passed=len(errors) == 0,
            duration_ms=duration,
            errors=errors,
        )

    def check_circular_imports(self) -> QACheck:
        """Detect circular imports in src/."""
        import time

        start = time.perf_counter()
        errors: list[str] = []

        # Use python -m to attempt importing every top-level module
        src_dir = self.root / "src"
        if src_dir.exists():
            for pkg in src_dir.iterdir():
                if pkg.is_dir() and (pkg / "__init__.py").exists():
                    module_name = f"src.{pkg.name}"
                    rc, _, stderr, _ = self._run_cmd(
                        ["python3", "-c", f"import {module_name}"],
                        timeout=30,
                    )
                    if rc != 0 and "circular import" in stderr.lower():
                        errors.append(f"Circular import in {module_name}: {stderr[:200]}")

        duration = (time.perf_counter() - start) * 1000
        return QACheck(
            name="circular_imports",
            passed=len(errors) == 0,
            duration_ms=duration,
            errors=errors,
        )

    # ------------------------------------------------------------------
    # Orchestration
    # ------------------------------------------------------------------

    def run_all(self) -> QAResult:
        """Run all QA checks and return aggregated result."""
        import time

        start = time.perf_counter()
        result = QAResult()

        checks = [
            ("ruff", self.check_ruff),
            ("mypy", self.check_mypy),
            ("pytest", self.check_pytest),
            ("version_sync", self.check_version_sync),
            ("secrets", self.check_secrets),
            ("circular_imports", self.check_circular_imports),
        ]

        for name, check_fn in checks:
            try:
                check = check_fn()
            except Exception as e:
                check = QACheck(
                    name=name,
                    passed=False,
                    duration_ms=0.0,
                    errors=[str(e)],
                )
            result.checks[name] = check
            result.total += 1
            if check.passed:
                result.passed += 1
            else:
                result.failed += 1

        result.duration_sec = time.perf_counter() - start
        return result
