"""Tests for BaseP6Client and ClientRegistry."""
from __future__ import annotations

import pytest

from src.knowledge.sources.base_p6 import BaseP6Client, ClientRegistry, client_registry


class DummyClient(BaseP6Client):
    BASE_URL = "https://example.com"


class TestClientRegistry:
    def test_add_remove_client(self) -> None:
        reg = ClientRegistry()
        client = DummyClient()
        reg.add(client)
        assert client in reg._clients
        reg.remove(client)
        assert client not in reg._clients

    @pytest.mark.anyio(backend="asyncio")
    async def test_close_all_closes_clients(self) -> None:
        reg = ClientRegistry()
        client = DummyClient()
        reg.add(client)
        assert client.available is True
        await reg.close_all()
        assert client.available is False
        assert len(reg._clients) == 0

    @pytest.mark.anyio(backend="asyncio")
    async def test_module_level_registry(self) -> None:
        client = DummyClient()
        assert client in client_registry._clients
        await client.close()
        assert client not in client_registry._clients


class TestBaseP6Client:
    @pytest.mark.anyio(backend="asyncio")
    async def test_context_manager(self) -> None:
        async with DummyClient() as client:
            assert client.available is True
        assert client.available is False

    @pytest.mark.anyio(backend="asyncio")
    async def test_close_idempotent(self) -> None:
        client = DummyClient()
        await client.close()
        await client.close()  # Should not raise
        assert client.available is False

    def test_available_without_httpx(self) -> None:
        import src.knowledge.sources.base_p6 as base_p6
        orig = base_p6.HAS_HTTPX
        try:
            base_p6.HAS_HTTPX = False
            client = DummyClient()
            assert client.available is False
        finally:
            base_p6.HAS_HTTPX = orig
