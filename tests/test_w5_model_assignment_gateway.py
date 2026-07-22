"""W5 regression: ModelAssignment honored on gateway / stage / depth paths."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.llm.depth_router import DepthBasedRouter
from src.llm.gateway import DefaultGateway
from src.llm.model_assignment import ModelAssignment
from src.llm.router import ProviderRouter


def test_provider_router_stage_uses_model_assignment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cfg = tmp_path / "models.json"
    ma = ModelAssignment.create_default("balanced")
    ma.phases["F"].model = "assigned/synthesis-from-json"
    ma.save(cfg)
    monkeypatch.setattr("src.llm.model_assignment.CONFIG_FILE", cfg)

    router = ProviderRouter()
    config = router.get_config_for_stage("synthesis")
    assert config.model == "assigned/synthesis-from-json"


def test_provider_router_proof_generation_maps_to_phase_g(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cfg = tmp_path / "models.json"
    ma = ModelAssignment.create_default("balanced")
    ma.phases["G"].model = "assigned/proof-qc-model"
    ma.save(cfg)
    monkeypatch.setattr("src.llm.model_assignment.CONFIG_FILE", cfg)

    router = ProviderRouter()
    config = router.get_config_for_stage("proof_generation")
    assert config.model == "assigned/proof-qc-model"


def test_depth_router_prefers_model_assignment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cfg = tmp_path / "models.json"
    ma = ModelAssignment.create_default("premium")
    ma.phases["B"].model = "assigned/knowledge-search"
    ma.save(cfg)
    monkeypatch.setattr("src.llm.model_assignment.CONFIG_FILE", cfg)

    model = DepthBasedRouter.route_for_pipeline_phase("B", "balanced")
    assert model == "assigned/knowledge-search"


@pytest.mark.asyncio
async def test_gateway_generate_passes_phase_to_async_client() -> None:
    mock_client = MagicMock()
    mock_client.generate = AsyncMock(return_value=MagicMock(content="ok", model="m", usage={}))

    gw = DefaultGateway(async_client=mock_client)
    await gw.generate("hello", phase="D")

    mock_client.generate.assert_awaited_once()
    _kwargs = mock_client.generate.call_args.kwargs
    assert _kwargs.get("phase") == "D"
