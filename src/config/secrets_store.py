"""Persistent user secrets at ~/.c4reqber/secrets.env."""

from __future__ import annotations

import logging
import os
import re
import stat
from pathlib import Path

from src.config.key_registry import KeyDef, all_keys
from src.config.paths import CONFIG_DIR, ensure_config_dir


logger = logging.getLogger(__name__)

SECRETS_ENV = CONFIG_DIR / "secrets.env"
_ENV_LINE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)=(.*)$")
_ENV_NAME = re.compile(r"^[A-Z][A-Z0-9_]*$")
_REGISTERED = {k.env_name for k in all_keys()}


def is_registered_env_name(env_name: str) -> bool:
    return env_name in _REGISTERED


def load_secrets_env(*, override: bool = False) -> None:
    """Load ~/.c4reqber/secrets.env into os.environ."""
    if not SECRETS_ENV.is_file():
        return
    try:
        from dotenv import load_dotenv

        load_dotenv(SECRETS_ENV, override=override)
        return
    except ImportError:
        logger.debug("python-dotenv unavailable; using inline secrets.env parser")
    for key, val in _parse_secrets_file().items():
        if override or not os.environ.get(key):
            os.environ[key] = val


def _parse_secrets_file() -> dict[str, str]:
    if not SECRETS_ENV.is_file():
        return {}
    out: dict[str, str] = {}
    for line in SECRETS_ENV.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        m = _ENV_LINE.match(stripped)
        if m:
            out[m.group(1)] = m.group(2).strip().strip('"').strip("'")
    return out


def get_value(env_name: str) -> str:
    """Return effective value: process env wins, then secrets.env."""
    return os.environ.get(env_name, "") or _parse_secrets_file().get(env_name, "")


def mask_value(value: str, secret: bool = True) -> str:
    if not value:
        return ""
    if not secret:
        return value
    if len(value) <= 4:
        return "****"
    return "****" + value[-4:]


def list_key_status(keys: list[KeyDef] | None = None) -> list[dict[str, str | bool]]:
    """Return status for each registered key."""
    registry = keys or all_keys()
    file_vals = _parse_secrets_file()
    result: list[dict[str, str | bool]] = []
    for key in registry:
        env_val = os.environ.get(key.env_name, "")
        file_val = file_vals.get(key.env_name, "")
        effective = env_val or file_val
        result.append(
            {
                **key.to_dict(),
                "configured": bool(effective),
                "source": "env" if env_val else ("file" if file_val else ""),
                "masked": mask_value(effective, key.secret),
            }
        )
    return result


def set_secret(env_name: str, value: str) -> Path:
    """Write or update one key in secrets.env."""
    if not _ENV_NAME.match(env_name):
        raise ValueError(f"Invalid env name: {env_name}")
    if not is_registered_env_name(env_name):
        raise ValueError(f"Unknown env name (not in registry): {env_name}")
    if any(ch in value for ch in "\n\r"):
        raise ValueError("Secret value must not contain newlines")

    ensure_config_dir()
    try:
        CONFIG_DIR.chmod(stat.S_IRWXU)
    except OSError:
        pass

    lines: list[str] = []
    if SECRETS_ENV.is_file():
        lines = SECRETS_ENV.read_text(encoding="utf-8").splitlines()
    updated = False
    new_lines: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#") or "=" not in stripped:
            new_lines.append(line)
            continue
        name = stripped.split("=", 1)[0].strip()
        if name == env_name:
            new_lines.append(f"{env_name}={value}")
            updated = True
        else:
            new_lines.append(line)
    if not updated:
        if new_lines and new_lines[-1].strip():
            new_lines.append("")
        new_lines.append(f"{env_name}={value}")
    header = "# c4reqber secrets — managed by blast config keys / TUI Setup Hub\n"
    if not new_lines or not new_lines[0].startswith("# c4reqber secrets"):
        new_lines = [header.rstrip(), *new_lines]
    SECRETS_ENV.write_text("\n".join(new_lines).rstrip() + "\n", encoding="utf-8")
    try:
        SECRETS_ENV.chmod(stat.S_IRUSR | stat.S_IWUSR)
    except OSError:
        logger.warning("Could not chmod 600 on %s", SECRETS_ENV)
    os.environ[env_name] = value
    return SECRETS_ENV


def category_summary() -> dict[str, dict[str, int]]:
    """Configured/total counts per category."""
    summary: dict[str, dict[str, int]] = {}
    for row in list_key_status():
        cat = str(row["category"])
        summary.setdefault(cat, {"total": 0, "configured": 0})
        summary[cat]["total"] += 1
        if row["configured"]:
            summary[cat]["configured"] += 1
    return summary
