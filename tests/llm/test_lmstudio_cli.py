from __future__ import annotations

from src.llm.providers.lmstudio_cli import LMStudioCLI


def test_available_uses_path_lookup_without_shell(monkeypatch) -> None:
    checked: list[str] = []

    def fake_which(command: str) -> str | None:
        checked.append(command)
        return None

    client = LMStudioCLI()
    client.lms = "lms; touch /tmp/should-not-run"
    monkeypatch.setattr("src.llm.providers.lmstudio_cli.os.path.exists", lambda _: False)
    monkeypatch.setattr("src.llm.providers.lmstudio_cli.shutil.which", fake_which)

    assert client.available is False
    assert checked == ["lms; touch /tmp/should-not-run"]
