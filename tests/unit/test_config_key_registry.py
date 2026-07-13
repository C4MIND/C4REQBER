"""Tests for key registry and secrets store."""

from __future__ import annotations

import os
from pathlib import Path

import pytest


def test_key_registry_parses_env_example():
    from src.config.key_registry import all_keys, categories

    keys = all_keys()
    assert len(keys) >= 50
    names = {k.env_name for k in keys}
    assert "OPENROUTER_API_KEY" in names
    assert "MASTODON_ACCESS_TOKEN" in names
    assert "llm" in categories()


def test_secrets_store_roundtrip(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from src.config import secrets_store

    monkeypatch.setattr(secrets_store, "SECRETS_ENV", tmp_path / "secrets.env")
    secrets_store.set_secret("OPENROUTER_API_KEY", "sk-or-test-secret")
    assert secrets_store.get_value("OPENROUTER_API_KEY") == "sk-or-test-secret"
    rows = secrets_store.list_key_status()
    test_row = next(r for r in rows if r["env_name"] == "OPENROUTER_API_KEY")
    assert test_row["configured"] is True
    assert str(test_row["masked"]).startswith("****")


def test_config_keys_json_output(capsys):
    from src.cli.config_keys import handle_keys_command

    handle_keys_command(json_out=True)
    captured = capsys.readouterr().out
    assert "OPENROUTER_API_KEY" in captured
    assert "categories" in captured


def test_config_keys_assign(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from src.cli.config_keys import handle_keys_command
    from src.config import secrets_store

    monkeypatch.setattr(secrets_store, "SECRETS_ENV", tmp_path / "secrets.env")
    handle_keys_command(assign="OPENROUTER_API_KEY=sk-or-test-assign")
    assert secrets_store.get_value("OPENROUTER_API_KEY") == "sk-or-test-assign"


def test_config_keys_rejects_unknown_assign(capsys):
    from src.cli.config_keys import handle_keys_command

    with pytest.raises(SystemExit) as exc:
        handle_keys_command(assign="NOT_A_REAL_KEY=abc")
    assert exc.value.code == 1
    assert "Unknown key" in capsys.readouterr().out


def test_secrets_store_rejects_newlines(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from src.config import secrets_store

    monkeypatch.setattr(secrets_store, "SECRETS_ENV", tmp_path / "secrets.env")
    with pytest.raises(ValueError, match="newlines"):
        secrets_store.set_secret("OPENROUTER_API_KEY", "line1\ninjected")


def test_secrets_store_file_mode(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    import stat

    from src.config import secrets_store

    path = tmp_path / "secrets.env"
    monkeypatch.setattr(secrets_store, "SECRETS_ENV", path)
    secrets_store.set_secret("OPENROUTER_API_KEY", "sk-test-mode")
    assert path.exists()
    assert oct(path.stat().st_mode & 0o777) == oct(stat.S_IRUSR | stat.S_IWUSR)
