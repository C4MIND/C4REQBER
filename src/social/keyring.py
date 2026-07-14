"""c4reqber: Secure Key Storage — Fernet encryption for agent.json secrets."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from cryptography.fernet import Fernet


KEYRING_DIR = Path.home() / ".c4reqber"
KEYRING_FILE = KEYRING_DIR / ".keyring"

SENSITIVE_FIELDS = (
    "orcid.client_secret",
    "twitter.api_key",
    "twitter.api_secret",
    "twitter.access_token",
    "twitter.access_secret",
    "telegram.bot_token",
    "reddit.client_id",
    "reddit.client_secret",
    "reddit.password",
    "zenodo.access_token",
    "discord.webhook_url",
    "discord.bot_token",
    "slack.webhook_url",
    "slack.bot_token",
)


def _get_or_create_key() -> bytes:
    """Get encryption key from env or keychain, or create new one."""
    # 1. Env var
    key_b64 = os.getenv("C4REQBER_KEYRING_TOKEN")
    if key_b64:
        return key_b64.encode()

    # 2. macOS Keychain
    try:
        import subprocess
        result = subprocess.run(
            ["security", "find-generic-password", "-s", "c4reqber-keyring", "-w"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip().encode()
    except Exception:
        pass

    # 3. Linux libsecret
    try:
        import subprocess
        result = subprocess.run(
            ["secret-tool", "lookup", "application", "c4reqber-keyring"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip().encode()
    except Exception:
        pass

    # 4. Cached file
    if KEYRING_FILE.exists():
        return KEYRING_FILE.read_bytes()

    # 5. Generate new
    key = Fernet.generate_key()
    KEYRING_DIR.mkdir(parents=True, exist_ok=True)
    KEYRING_FILE.write_bytes(key)
    KEYRING_FILE.chmod(0o600)
    return key


def _get_fernet() -> Fernet:
    key = _get_or_create_key()
    return Fernet(key)


def encrypt_value(value: str) -> str:
    if not value:
        return ""
    f = _get_fernet()
    return f.encrypt(value.encode()).decode()


def decrypt_value(encrypted: str) -> str:
    if not encrypted:
        return ""
    try:
        f = _get_fernet()
        return f.decrypt(encrypted.encode()).decode()
    except Exception:
        return encrypted  # not encrypted — plaintext fallback


def encrypt_config_sensitive(config_dict: dict[str, Any]) -> dict[str, Any]:
    """Encrypt sensitive fields in a config dict (mutates in place)."""
    for field in SENSITIVE_FIELDS:
        keys = field.split(".")
        d = config_dict
        for k in keys[:-1]:
            d = d.setdefault(k, {})
        last = keys[-1]
        if last in d and d[last]:
            d[last] = encrypt_value(str(d[last]))
    return config_dict


def decrypt_config_sensitive(config_dict: dict[str, Any]) -> dict[str, Any]:
    """Decrypt sensitive fields in a config dict (mutates in place)."""
    for field in SENSITIVE_FIELDS:
        keys = field.split(".")
        d = config_dict
        found = True
        for k in keys[:-1]:
            if k not in d:
                found = False
                break
            d = d[k]
        if not found:
            continue
        last = keys[-1]
        if last in d and d[last]:
            d[last] = decrypt_value(str(d[last]))
    return config_dict
