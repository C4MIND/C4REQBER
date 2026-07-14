"""sync_provider_chain must raise on total failure, not return placeholder text."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.llm.sync_provider_chain import _ProviderSpec, generate_with_fallback


def test_generate_with_fallback_raises_when_all_providers_fail() -> None:
    spec = _ProviderSpec(
        name="test",
        url="http://localhost:9999/v1/chat/completions",
        model="test-model",
        api_key="",
        extra_headers={},
    )
    mock_client = MagicMock()
    mock_client.post.side_effect = RuntimeError("connection refused")

    with patch("src.llm.sync_provider_chain._build_chain", return_value=[spec]):
        with patch("httpx.Client") as client_cls:
            client_cls.return_value.__enter__.return_value = mock_client
            with pytest.raises(RuntimeError, match="All LLM providers failed"):
                generate_with_fallback("hello", system_prompt="sys")
