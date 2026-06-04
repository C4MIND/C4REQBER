"""Tests for safe_subprocess in src/utils/safe_subprocess.py

Pure-logic unit tests: NO MOCKS, NO NETWORK, NO LLM.
Uses real subprocess calls with safe system commands.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from utils.safe_subprocess import (
    SubprocessSecurityError,
    get_project_root,
    safe_command_string,
    safe_subprocess_run,
    validate_command,
    validate_cwd,
    validate_temp_path,
)


# ═══════════════════════════════════════════════════════════════════
# safe_subprocess_run
# ═══════════════════════════════════════════════════════════════════


class TestSafeSubprocessRun:
    def test_simple_echo_command(self):
        """Running a simple echo should return stdout with the echoed text."""
        result = safe_subprocess_run(["echo", "hello_test_42"])
        assert result.returncode == 0
        assert "hello_test_42" in result.stdout

    def test_echo_with_quotes(self):
        """Echo with spaces should preserve the text."""
        result = safe_subprocess_run(["echo", "hello world test"])
        assert result.returncode == 0
        assert "hello world test" in result.stdout

    def test_returncode_zero_on_success(self):
        """Successful commands should return code 0."""
        result = safe_subprocess_run(["true"])
        assert result.returncode == 0

    def test_capture_output_enabled(self):
        """capture_output=True by default should return stdout and stderr."""
        result = safe_subprocess_run(["echo", "captured"])
        assert hasattr(result, "stdout")
        assert hasattr(result, "stderr")
        assert "captured" in result.stdout

    def test_custom_cwd(self):
        """Should accept a custom working directory within project root."""
        root = get_project_root()
        result = safe_subprocess_run(["pwd"], cwd=str(root / "src"))
        assert result.returncode == 0
        assert (root / "src").as_posix() in result.stdout.strip()


class TestTimeoutHandling:
    def test_timeout_on_slow_command(self):
        """A slow command should raise TimeoutExpired when timeout is set."""
        with pytest.raises(subprocess.TimeoutExpired):
            safe_subprocess_run(["sleep", "5"], timeout=0.1)

    def test_timeout_does_not_trigger_for_fast_command(self):
        """A fast command with generous timeout should not raise."""
        result = safe_subprocess_run(["echo", "fast"], timeout=5.0)
        assert result.returncode == 0

    def test_none_timeout_runs_indefinitely(self):
        """timeout=None should allow the command to complete."""
        result = safe_subprocess_run(["echo", "no_timeout"], timeout=None)
        assert result.returncode == 0
        assert "no_timeout" in result.stdout


class TestErrorHandling:
    def test_missing_binary_raises_filenotfound(self):
        """A nonexistent binary should raise FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            safe_subprocess_run(["nonexistent_binary_xyz_42"])

    def test_command_returning_nonzero(self):
        """A command that returns non-zero should still complete without exception."""
        result = safe_subprocess_run(["false"])
        assert result.returncode != 0

    def test_security_blocks_shell_metacharacter(self):
        """Commands with shell metacharacters should raise SubprocessSecurityError."""
        with pytest.raises(SubprocessSecurityError):
            safe_subprocess_run(["echo", "hello; rm -rf /"])


# ═══════════════════════════════════════════════════════════════════
# validate_command
# ═══════════════════════════════════════════════════════════════════


class TestValidateCommand:
    def test_valid_command_passes(self):
        """A normal command list should pass validation."""
        result = validate_command(["echo", "hello"])
        assert result == ["echo", "hello"]

    def test_empty_command_raises(self):
        """Empty command list should raise SubprocessSecurityError."""
        with pytest.raises(SubprocessSecurityError, match="cannot be empty"):
            validate_command([])

    def test_non_list_raises(self):
        """Non-list command should raise SubprocessSecurityError."""
        with pytest.raises(SubprocessSecurityError, match="must be a list"):
            validate_command("echo hello")  # type: ignore[arg-type]

    def test_semicolon_detected(self):
        """Semicolon in argument should raise SubprocessSecurityError."""
        with pytest.raises(SubprocessSecurityError, match="Dangerous"):
            validate_command(["echo", "hello; rm"])

    def test_pipe_detected(self):
        """Pipe character in argument should raise SubprocessSecurityError."""
        with pytest.raises(SubprocessSecurityError, match="Dangerous"):
            validate_command(["echo", "cat | rm"])

    def test_ampersand_detected(self):
        """Ampersand in argument should raise SubprocessSecurityError."""
        with pytest.raises(SubprocessSecurityError, match="Dangerous"):
            validate_command(["echo", "sleep &"])

    def test_backtick_detected(self):
        """Backtick in argument should raise SubprocessSecurityError."""
        with pytest.raises(SubprocessSecurityError, match="Dangerous"):
            validate_command(["echo", "`whoami`"])

    def test_non_string_part_raises(self):
        """Non-string parts should raise SubprocessSecurityError."""
        with pytest.raises(SubprocessSecurityError, match="must be string"):
            validate_command(["echo", 42])  # type: ignore[list-item]


# ═══════════════════════════════════════════════════════════════════
# validate_cwd
# ═══════════════════════════════════════════════════════════════════


class TestValidateCwd:
    def test_none_returns_project_root(self):
        """None cwd should return the project root."""
        cwd = validate_cwd(None)
        expected = get_project_root()
        assert cwd == expected

    def test_project_subdir_passes(self):
        """A directory inside the project root should pass."""
        root = get_project_root()
        subdir = root / "src"
        result = validate_cwd(str(subdir))
        assert result == subdir.resolve()

    def test_outside_project_raises(self):
        """A directory outside the project root should raise."""
        with pytest.raises(SubprocessSecurityError, match="outside project root"):
            validate_cwd("/etc")

    def test_relative_to_root_passes(self):
        """A relative path under project root should resolve correctly."""
        root = get_project_root()
        result = validate_cwd(root / "tests" / "utils")
        assert result == (root / "tests" / "utils").resolve()


# ═══════════════════════════════════════════════════════════════════
# validate_temp_path
# ═══════════════════════════════════════════════════════════════════


class TestValidateTempPath:
    def test_temp_dir_path_passes(self):
        """A path under /tmp should pass validation."""
        result = validate_temp_path("/tmp/test_file.txt")
        assert result == Path("/tmp/test_file.txt").resolve()

    def test_path_outside_allowed_dirs_raises(self):
        """A resolved path outside allowed temp dirs should raise."""
        path = Path("/Users/shared/test_file.txt")
        with pytest.raises(SubprocessSecurityError, match="not within allowed temp"):
            validate_temp_path(path)

    def test_outside_allowed_dirs_raises(self):
        """A path outside allowed temp dirs should raise."""
        with pytest.raises(SubprocessSecurityError, match="not within allowed temp"):
            validate_temp_path("/Users/shared/something")


# ═══════════════════════════════════════════════════════════════════
# safe_command_string
# ═══════════════════════════════════════════════════════════════════


class TestSafeCommandString:
    def test_simple_command_formatting(self):
        """Should join and quote command parts."""
        result = safe_command_string(["echo", "hello world"])
        assert "echo" in result
        assert "hello world" in result

    def test_handles_special_chars(self):
        """Special characters should be shell-quoted."""
        result = safe_command_string(["echo", "file with spaces.txt"])
        assert "'" in result or '"' in result

    def test_empty_list(self):
        """Empty command list should produce empty string."""
        result = safe_command_string([])
        assert result == ""


# ═══════════════════════════════════════════════════════════════════
# get_project_root
# ═══════════════════════════════════════════════════════════════════


class TestGetProjectRoot:
    def test_returns_valid_path(self):
        """get_project_root should return an existing directory."""
        root = get_project_root()
        assert root.exists()
        assert root.is_dir()

    def test_contains_expected_dirs(self):
        """Project root should contain known subdirectories."""
        root = get_project_root()
        assert (root / "src").is_dir()
        assert (root / "tests").is_dir()

    def test_contains_pyproject(self):
        """Project root should contain pyproject.toml."""
        root = get_project_root()
        assert (root / "pyproject.toml").is_file()
