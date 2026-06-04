"""
Security Test: Subprocess Safety
Tests that path injection and command injection are blocked.
"""
from __future__ import annotations

import sys
from pathlib import Path


# Bypass src/__init__.py which has missing dependencies
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))


import pytest

from utils.safe_subprocess import (
    SubprocessSecurityError,
    safe_command_string,
    validate_command,
    validate_cwd,
    validate_temp_path,
)


class TestSubprocessSafety:
    def test_validate_command_rejects_empty(self) -> None:
        with pytest.raises(SubprocessSecurityError):
            validate_command([])

    def test_validate_command_rejects_shell_metacharacters(self) -> None:
        with pytest.raises(SubprocessSecurityError):
            validate_command(["python3", "-c", "import os; os.system('rm -rf /')"])

    def test_validate_command_rejects_pipe(self) -> None:
        with pytest.raises(SubprocessSecurityError):
            validate_command(["echo", "hello | cat /etc/passwd"])

    def test_validate_command_rejects_semicolon(self) -> None:
        with pytest.raises(SubprocessSecurityError):
            validate_command(["python3", "script.py; rm -rf /"])

    def test_validate_command_accepts_safe(self) -> None:
        result = validate_command(["python3", "script.py", "--flag", "value"])
        assert result == ["python3", "script.py", "--flag", "value"]

    def test_validate_cwd_rejects_outside_project(self) -> None:
        with pytest.raises(SubprocessSecurityError):
            validate_cwd("/etc")

    def test_validate_cwd_accepts_project_root(self) -> None:
        result = validate_cwd(None)
        assert isinstance(result, Path)

    def test_validate_temp_path_rejects_path_traversal(self) -> None:
        with pytest.raises(SubprocessSecurityError):
            validate_temp_path("/tmp/../../../etc/passwd")

    def test_validate_temp_path_accepts_system_temp(self) -> None:
        result = validate_temp_path("/tmp/test_file.txt")
        assert isinstance(result, Path)

    def test_safe_command_string_quotes_args(self) -> None:
        result = safe_command_string(["python3", "hello world", "a;b"])
        assert "'hello world'" in result or '"hello world"' in result
        assert result.startswith("python3 ")

    def test_safe_subprocess_run_blocks_path_injection(self) -> None:
        from utils.safe_subprocess import safe_subprocess_run

        with pytest.raises(SubprocessSecurityError):
            safe_subprocess_run(
                ["python3", "script.py"],
                cwd="/etc",
                timeout=1,
            )

    def test_safe_subprocess_run_blocks_command_injection(self) -> None:
        from utils.safe_subprocess import safe_subprocess_run

        with pytest.raises(SubprocessSecurityError):
            safe_subprocess_run(
                ["python3", "-c", "import os; os.system('id')"],
                timeout=1,
            )
