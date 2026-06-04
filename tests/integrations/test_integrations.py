"""Tests for integration modules — validate imports, init, auto-detection."""
from __future__ import annotations

import pytest


class TestPackageManager:
    def test_import(self):
        from src.cli.package_manager import PACKAGES, detect_all
        assert len(PACKAGES) == 15

    def test_detect_all(self):
        from src.cli.package_manager import detect_all, PackageStatus
        statuses = detect_all()
        assert len(statuses) == 15
        assert all(isinstance(v, PackageStatus) for v in statuses.values())

    def test_known_packages(self):
        from src.cli.package_manager import PACKAGES
        ids = {p.id for p in PACKAGES}
        assert "mlx-lm" in ids
        assert "chromadb" in ids
        assert "fastmcp" in ids
        assert "qiskit" in ids
        assert "nashpy" in ids


class TestMLXProvider:
    def test_import(self):
        from src.llm.providers.mlx_provider import MLXProvider
        assert MLXProvider is not None

    def test_is_apple_silicon(self):
        from src.llm.providers.mlx_provider import MLXProvider
        result = MLXProvider.is_apple_silicon()
        assert isinstance(result, bool)

    def test_init(self):
        from src.llm.providers.mlx_provider import MLXProvider
        mlx = MLXProvider()
        assert "Qwen" in mlx.model_name or "mlx" in mlx.model_name


class TestChromaVectorStore:
    def test_import(self):
        from src.knowledge.chroma_store import ChromaVectorStore
        assert ChromaVectorStore is not None

    def test_init(self):
        from src.knowledge.chroma_store import ChromaVectorStore
        store = ChromaVectorStore()
        assert store.available is not None
        assert store.persist_dir.endswith("chromadb")


class TestFastMCPBridge:
    def test_import(self):
        from src.mcp_server.fastmcp_bridge import FastMCPBridge
        assert FastMCPBridge is not None

    def test_init(self):
        from src.mcp_server.fastmcp_bridge import FastMCPBridge
        bridge = FastMCPBridge()
        assert not bridge.connected


class TestScientificBridges:
    def test_import_all(self):
        from src.integrations.scientific_bridges import (
            LangGraphBridge, SmitheryBridge, PyMCBridge,
            OpenMMBridge, DeepChemBridge, UnslothBridge, VLLMBridge,
        )
        assert LangGraphBridge is not None
        assert SmitheryBridge is not None
        assert PyMCBridge is not None
        assert OpenMMBridge is not None
        assert DeepChemBridge is not None
        assert UnslothBridge is not None
        assert VLLMBridge is not None

    @pytest.mark.parametrize("bridge_cls", [
        "LangGraphBridge", "SmitheryBridge", "PyMCBridge",
        "OpenMMBridge", "DeepChemBridge", "UnslothBridge", "VLLMBridge",
    ])
    def test_available_property(self, bridge_cls):
        from src.integrations import scientific_bridges as sb
        obj = getattr(sb, bridge_cls)()
        assert isinstance(obj.available, bool)


class TestLLMMLXProvider:
    def test_mlx_in_provider_enum(self):
        from src.llm.config import LLMProvider
        assert LLMProvider.MLX.value == "mlx"

    def test_mlx_in_provider_order(self):
        from src.llm.retry_pkg.policies import ProviderRetryManager
        order = [p.value for p in ProviderRetryManager.PROVIDER_ORDER]
        assert "mlx" in order
