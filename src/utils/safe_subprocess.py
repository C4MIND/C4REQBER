"""
C44TCDI: Safe Subprocess Helpers
Validates and sanitizes subprocess calls to prevent injection attacks.
"""
from __future__ import annotations

import logging
import os
import shlex
import subprocess
from pathlib import Path
from typing import Any


logger = logging.getLogger(__name__)


class SubprocessSecurityError(ValueError):
    """Raised when a subprocess call fails security validation."""

    pass


def get_project_root() -> Path:
    """Return the project root directory."""
    # Resolve from this file: src/utils/safe_subprocess.py -> project root
    return Path(__file__).resolve().parent.parent.parent


def validate_cwd(cwd: str | Path | None) -> Path:
    """Validate that cwd is within the project root.

    Raises SubprocessSecurityError if cwd is outside the project tree.
    """
    project_root = get_project_root()
    if cwd is None:
        return project_root

    cwd_path = Path(cwd).resolve()
    try:
        cwd_path.relative_to(project_root)
    except ValueError as e:
        raise SubprocessSecurityError(
            f"Working directory '{cwd_path}' is outside project root '{project_root}'"
        ) from e
    return cwd_path


def validate_command(cmd: list[str]) -> list[str]:
    """Validate a command list for safety.

    - Rejects shell metacharacters in arguments.
    - Rejects empty commands.
    - Returns the sanitized command list.
    """
    if not cmd:
        raise SubprocessSecurityError("Command cannot be empty")

    if not isinstance(cmd, list):
        raise SubprocessSecurityError("Command must be a list of strings")

    sanitized = []
    for part in cmd:
        if not isinstance(part, str):
            raise SubprocessSecurityError(f"Command part must be string, got {type(part).__name__}")
        # Check for dangerous shell metacharacters
        dangerous = (";", "&", "|", "$>", "<", "`", "$()", "\n", "$", "\\", "*", "?", "~", "{}", "!", "#", "%", "^")
        for char in dangerous:
            if char in part:
                raise SubprocessSecurityError(
                    f"Dangerous character '{char}' detected in command argument: {part}"
                )
        sanitized.append(part)

    return sanitized


def safe_subprocess_run(
    cmd: list[str],
    cwd: str | Path | None = None,
    timeout: float | None = None,
    capture_output: bool = True,
    text: bool = True,
    **kwargs: Any,
) -> subprocess.CompletedProcess[str]:
    """Run a subprocess with security validations.

    Args:
        cmd: Command as list of strings.
        cwd: Working directory (must be within project root).
        timeout: Timeout in seconds.
        capture_output: Whether to capture stdout/stderr.
        text: Whether to return text output.
        **kwargs: Additional args passed to subprocess.run.

    Returns:
        CompletedProcess result.

    Raises:
        SubprocessSecurityError: If validation fails.
    """
    validated_cmd = validate_command(cmd)
    validated_cwd = validate_cwd(cwd)

    kwargs.pop("shell", None)
    kwargs.pop("preexec_fn", None)
    kwargs.pop("start_new_session", None)

    # Symlink / TOCTOU guard: ensure cwd is not a symlink outside project
    project_root = get_project_root()
    real_cwd = os.path.realpath(str(validated_cwd))
    if not real_cwd.startswith(str(project_root)):
        raise SubprocessSecurityError(f"Resolved cwd '{real_cwd}' escapes project root")

    # Sanitize environment to prevent LD_PRELOAD / PATH injection
    safe_env = {
        k: v for k, v in (os.environ if kwargs.get("env") is None else kwargs["env"]).items()
        if k not in ("LD_PRELOAD", "LD_LIBRARY_PATH", "DYLD_INSERT_LIBRARIES")
    }
    if "env" not in kwargs or kwargs.get("env") is None:
        kwargs["env"] = safe_env

    logger.debug("Safe subprocess: cmd=%s cwd=%s", validated_cmd, validated_cwd)
    return subprocess.run(
        validated_cmd,
        cwd=str(validated_cwd),
        capture_output=capture_output,
        text=text,
        timeout=timeout,
        shell=False,
        **kwargs,
    )


def validate_temp_path(path: str | Path) -> Path:
    """Validate that a temporary file path is safe.

    - Must be within the system temp directory or project root.
    - Must not contain path traversal sequences.
    """
    path_obj = Path(path).resolve()
    temp_dirs = {
        Path(os.getenv("TMPDIR", "/tmp")).resolve(),
        Path(os.getenv("TEMP", "/tmp")).resolve(),
        Path(os.getenv("TMP", "/tmp")).resolve(),
        get_project_root() / ".tmp",
        get_project_root() / "tmp",
    }

    # Check for path traversal
    parts = path_obj.parts
    for part in parts:
        if part == "..":
            raise SubprocessSecurityError(f"Path traversal detected in: {path}")

    # Must be under an allowed temp directory
    for temp_dir in temp_dirs:
        try:
            path_obj.relative_to(temp_dir)
            return path_obj
        except ValueError:
            continue

    raise SubprocessSecurityError(
        f"Temporary path '{path_obj}' is not within allowed temp directories"
    )


def safe_command_string(cmd_parts: list[str]) -> str:
    """Convert command list to safely quoted shell string for logging."""
    return " ".join(shlex.quote(part) for part in cmd_parts)
