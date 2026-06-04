"""Tests for src/adapters/ollama_adapter.py"""
from __future__ import annotations
from pathlib import Path

import json
import sys
from io import BytesIO
from typing import Any
from unittest.mock import MagicMock, patch


_root = Path(__file__).resolve().parent.parent
project_root = _root.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pytest

from src.adapters.ollama_adapter import (
    LLMProvider,
    OllamaAdapter,
    OllamaModel,
)


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════


@pytest.fixture
def adapter():
    return OllamaAdapter(base_url="http://localhost:11434")


@pytest.fixture
def mock_response():
    def make_response(data: dict, status: int = 200):
        response = MagicMock()
        response.status = status
        response.__enter__ = MagicMock(return_value=response)
        response.__exit__ = MagicMock(return_value=False)
        response.read = MagicMock(return_value=json.dumps(data).encode())
        return response
    return make_response


# ═══════════════════════════════════════════════════════════════════
# OllamaModel
# ═══════════════════════════════════════════════════════════════════


class TestOllamaModel:
    def test_init(self):
        model = OllamaModel(
            name="test-model",
            size="5 GB",
            parameter_size="7B",
            quantization="q4_0",
            format="gguf",
            family="llama",
        )
        assert model.name == "test-model"
        assert model.size == "5 GB"
        assert model.parameter_size == "7B"
        assert model.quantization == "q4_0"
        assert model.format == "gguf"
        assert model.family == "llama"


# ═══════════════════════════════════════════════════════════════════
# OllamaAdapter initialization
# ═══════════════════════════════════════════════════════════════════


class TestOllamaAdapterInit:
    def test_default_url(self):
        a = OllamaAdapter()
        assert a.base_url == "http://localhost:11434"

    def test_custom_url(self, adapter):
        assert adapter.base_url == "http://localhost:11434"

    def test_url_trailing_slash_removed(self):
        a = OllamaAdapter(base_url="http://localhost:11434/")
        assert a.base_url == "http://localhost:11434"

    def test_recommended_models(self):
        assert "reasoning" in OllamaAdapter.RECOMMENDED_MODELS
        assert "fast" in OllamaAdapter.RECOMMENDED_MODELS
        assert "powerful" in OllamaAdapter.RECOMMENDED_MODELS
        assert "code" in OllamaAdapter.RECOMMENDED_MODELS
        assert "small" in OllamaAdapter.RECOMMENDED_MODELS


# ═══════════════════════════════════════════════════════════════════
# is_available
# ═══════════════════════════════════════════════════════════════════


class TestIsAvailable:
    def test_available(self, adapter, mock_response):
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.return_value = mock_response({"models": []})
            assert adapter.is_available() is True

    def test_not_available_connection_error(self, adapter):
        with patch("urllib.request.urlopen", side_effect=ConnectionRefusedError()):
            assert adapter.is_available() is False

    def test_not_available_bad_status(self, adapter, mock_response):
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.return_value = mock_response({}, status=500)
            assert adapter.is_available() is False


# ═══════════════════════════════════════════════════════════════════
# list_models
# ═══════════════════════════════════════════════════════════════════


class TestListModels:
    def test_basic(self, adapter, mock_response):
        data = {
            "models": [
                {
                    "name": "model1",
                    "size": 5000000000,
                    "details": {
                        "parameter_size": "7B",
                        "quantization_level": "q4_0",
                        "format": "gguf",
                        "family": "llama",
                    }
                }
            ]
        }
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.return_value = mock_response(data)
            models = adapter.list_models()

        assert len(models) == 1
        assert models[0].name == "model1"
        assert models[0].parameter_size == "7B"
        assert models[0].family == "llama"

    def test_multiple_models(self, adapter, mock_response):
        data = {
            "models": [
                {"name": "m1", "size": 1000, "details": {}},
                {"name": "m2", "size": 2000, "details": {}},
            ]
        }
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.return_value = mock_response(data)
            models = adapter.list_models()

        assert len(models) == 2
        assert models[0].name == "m1"
        assert models[1].name == "m2"

    def test_empty_models(self, adapter, mock_response):
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.return_value = mock_response({"models": []})
            models = adapter.list_models()
        assert models == []

    def test_json_decode_error(self, adapter):
        with patch("urllib.request.urlopen") as mock_urlopen:
            response = MagicMock()
            response.__enter__ = MagicMock(return_value=response)
            response.__exit__ = MagicMock(return_value=False)
            response.read = MagicMock(return_value=b"invalid json")
            mock_urlopen.return_value = response
            models = adapter.list_models()
        assert models == []

    def test_missing_details(self, adapter, mock_response):
        data = {"models": [{"name": "m1", "size": 1000}]}
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.return_value = mock_response(data)
            models = adapter.list_models()
        assert models[0].parameter_size == "?"
        assert models[0].family == "?"


# ═══════════════════════════════════════════════════════════════════
# generate
# ═══════════════════════════════════════════════════════════════════


class TestGenerate:
    def test_basic(self, adapter, mock_response):
        data = {"response": "Hello, world!"}
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.return_value = mock_response(data)
            result = adapter.generate("Say hello")

        assert result == "Hello, world!"

    def test_with_system_prompt(self, adapter, mock_response):
        data = {"response": "System response"}
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.return_value = mock_response(data)
            result = adapter.generate("test", system="You are a test")

        assert result == "System response"
            # Verify system was included in request
        call_args = mock_urlopen.call_args
        request = call_args[0][0]
        body = json.loads(request.data)
        assert body["system"] == "You are a test"

    def test_with_temperature(self, adapter, mock_response):
        data = {"response": "test"}
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.return_value = mock_response(data)
            adapter.generate("test", temperature=0.5)

        call_args = mock_urlopen.call_args
        request = call_args[0][0]
        body = json.loads(request.data)
        assert body["options"]["temperature"] == 0.5

    def test_with_max_tokens(self, adapter, mock_response):
        data = {"response": "test"}
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.return_value = mock_response(data)
            adapter.generate("test", max_tokens=100)

        call_args = mock_urlopen.call_args
        request = call_args[0][0]
        body = json.loads(request.data)
        assert body["options"]["num_predict"] == 100

    def test_default_model(self, adapter, mock_response):
        data = {"response": "test"}
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.return_value = mock_response(data)
            adapter.generate("test")

        call_args = mock_urlopen.call_args
        request = call_args[0][0]
        body = json.loads(request.data)
        assert body["model"] == "qwen2.5:14b"

    def test_custom_model(self, adapter, mock_response):
        data = {"response": "test"}
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.return_value = mock_response(data)
            adapter.generate("test", model="llama3.1:70b")

        call_args = mock_urlopen.call_args
        request = call_args[0][0]
        body = json.loads(request.data)
        assert body["model"] == "llama3.1:70b"

    def test_json_decode_error(self, adapter):
        with patch("urllib.request.urlopen") as mock_urlopen:
            response = MagicMock()
            response.__enter__ = MagicMock(return_value=response)
            response.__exit__ = MagicMock(return_value=False)
            response.read = MagicMock(return_value=b"invalid")
            mock_urlopen.return_value = response
            result = adapter.generate("test")

        assert "Error:" in result
        assert "Ollama" in result

    def test_empty_response(self, adapter, mock_response):
        data = {"response": ""}
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.return_value = mock_response(data)
            result = adapter.generate("test")

        assert result == ""


# ═══════════════════════════════════════════════════════════════════
# generate_structured
# ═══════════════════════════════════════════════════════════════════


class TestGenerateStructured:
    def test_basic(self, adapter, mock_response):
        data = {"response": '{"name": "test", "value": 42}'}
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.return_value = mock_response(data)
            schema = {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "value": {"type": "integer"},
                }
            }
            result = adapter.generate_structured("test", schema)

        assert result["name"] == "test"
        assert result["value"] == 42

    def test_json_in_markdown(self, adapter, mock_response):
        data = {"response": '```json\n{"name": "test"}\n```'}
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.return_value = mock_response(data)
            schema = {"type": "object", "properties": {"name": {"type": "string"}}}
            result = adapter.generate_structured("test", schema)

        assert result["name"] == "test"

    def test_json_in_generic_code_block(self, adapter, mock_response):
        data = {"response": '```\n{"name": "test"}\n```'}
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.return_value = mock_response(data)
            schema = {"type": "object", "properties": {"name": {"type": "string"}}}
            result = adapter.generate_structured("test", schema)

        assert result["name"] == "test"

    def test_invalid_json_fallback(self, adapter, mock_response):
        data = {"response": "not valid json"}
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.return_value = mock_response(data)
            schema = {
                "type": "object",
                "properties": {
                    "items": {"type": "array"},
                    "name": {"type": "string"},
                }
            }
            result = adapter.generate_structured("test", schema)

        assert result == {"items": [], "name": ""}

    def test_temperature_override(self, adapter, mock_response):
        data = {"response": '{"x": 1}'}
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.return_value = mock_response(data)
            schema = {"type": "object", "properties": {"x": {"type": "integer"}}}
            adapter.generate_structured("test", schema)

        call_args = mock_urlopen.call_args
        request = call_args[0][0]
        body = json.loads(request.data)
        assert body["options"]["temperature"] == 0.3


# ═══════════════════════════════════════════════════════════════════
# pull_model
# ═══════════════════════════════════════════════════════════════════


class TestPullModel:
    def test_success(self, adapter, mock_response):
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.return_value = mock_response({"status": "success"})
            result = adapter.pull_model("test-model")

        assert result is True

    def test_failure(self, adapter, mock_response):
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.return_value = mock_response({"status": "error"})
            result = adapter.pull_model("test-model")

        assert result is False

    def test_json_error(self, adapter):
        with patch("urllib.request.urlopen") as mock_urlopen:
            response = MagicMock()
            response.__enter__ = MagicMock(return_value=response)
            response.__exit__ = MagicMock(return_value=False)
            response.read = MagicMock(return_value=b"invalid")
            mock_urlopen.return_value = response
            result = adapter.pull_model("test-model")

        assert result is False

    def test_prints_message(self, adapter, mock_response):
        with patch("builtins.print") as mock_print:
            with patch("urllib.request.urlopen") as mock_urlopen:
                mock_urlopen.return_value = mock_response({"status": "success"})
                adapter.pull_model("test-model")

            mock_print.assert_called_once()
            assert "Pulling model" in mock_print.call_args[0][0]


# ═══════════════════════════════════════════════════════════════════
# _format_size
# ═══════════════════════════════════════════════════════════════════


class TestFormatSize:
    def test_bytes(self, adapter):
        assert adapter._format_size(512) == "512.0 B"

    def test_kilobytes(self, adapter):
        assert adapter._format_size(1536) == "1.5 KB"

    def test_megabytes(self, adapter):
        assert adapter._format_size(5 * 1024 * 1024) == "5.0 MB"

    def test_gigabytes(self, adapter):
        assert adapter._format_size(2 * 1024**3) == "2.0 GB"

    def test_terabytes(self, adapter):
        assert adapter._format_size(2 * 1024**4) == "2.0 TB"


# ═══════════════════════════════════════════════════════════════════
# recommend_model
# ═══════════════════════════════════════════════════════════════════


class TestRecommendModel:
    def test_80gb(self):
        assert OllamaAdapter.recommend_model(80) == "llama3.1:70b"

    def test_40gb(self):
        assert OllamaAdapter.recommend_model(40) == "llama3.1:70b-q4_0"

    def test_24gb(self):
        assert OllamaAdapter.recommend_model(24) == "qwen2.5:14b"

    def test_16gb(self):
        assert OllamaAdapter.recommend_model(16) == "qwen2.5:14b-q4_0"

    def test_8gb(self):
        assert OllamaAdapter.recommend_model(8) == "qwen2.5:7b"

    def test_4gb(self):
        assert OllamaAdapter.recommend_model(4) == "phi3:medium"


# ═══════════════════════════════════════════════════════════════════
# LLMProvider
# ═══════════════════════════════════════════════════════════════════


class TestLLMProvider:
    def test_init_no_providers(self):
        with patch.object(OllamaAdapter, "is_available", return_value=False):
            provider = LLMProvider()
            assert provider.active == "none"

    def test_init_ollama_available(self):
        with patch.object(OllamaAdapter, "is_available", return_value=True):
            provider = LLMProvider()
            assert provider.active == "ollama"

    def test_init_prefer_local(self):
        with patch.object(OllamaAdapter, "is_available", return_value=True):
            provider = LLMProvider(prefer_local=True)
            assert provider.active == "ollama"

    def test_init_openrouter_only(self):
        with patch.object(OllamaAdapter, "is_available", return_value=False):
            mock_client = MagicMock()
            fake_module = MagicMock()
            fake_module.LLMClient = mock_client
            with patch.dict(sys.modules, {"src.llm.client": fake_module, "llm.client": fake_module}):
                provider = LLMProvider(openrouter_key="test-key")
                assert provider.active == "openrouter"
                assert provider.openrouter is not None

    def test_get_status_no_providers(self):
        with patch.object(OllamaAdapter, "is_available", return_value=False):
            provider = LLMProvider()
            status = provider.get_status()
            assert status["active_provider"] == "none"
            assert status["ollama_available"] is False
            assert status["openrouter_available"] is False

    def test_get_status_ollama(self):
        with patch.object(OllamaAdapter, "is_available", return_value=True):
            provider = LLMProvider()
            status = provider.get_status()
            assert status["active_provider"] == "ollama"
            assert status["ollama_available"] is True
            assert status["prefer_local"] is False

    def test_generate_ollama(self):
        with patch.object(OllamaAdapter, "is_available", return_value=True):
            provider = LLMProvider()
            with patch.object(provider.ollama, "generate", return_value="hello") as mock_gen:
                result = provider.generate("test")
                assert result == "hello"
                mock_gen.assert_called_once()

    def test_generate_no_provider_raises(self):
        with patch.object(OllamaAdapter, "is_available", return_value=False):
            provider = LLMProvider()
            with pytest.raises(RuntimeError, match="No LLM provider available"):
                provider.generate("test")

    def test_generate_structured_ollama(self):
        with patch.object(OllamaAdapter, "is_available", return_value=True):
            provider = LLMProvider()
            schema = {"type": "object", "properties": {"x": {"type": "string"}}}
            with patch.object(provider.ollama, "generate_structured", return_value={"x": "test"}) as mock_gen:
                result = provider.generate_structured("test", schema)
                assert result == {"x": "test"}

    def test_generate_structured_no_provider_raises(self):
        with patch.object(OllamaAdapter, "is_available", return_value=False):
            provider = LLMProvider()
            with pytest.raises(RuntimeError, match="No LLM provider available"):
                provider.generate_structured("test", {})

    def test_openrouter_generate(self):
        with patch.object(OllamaAdapter, "is_available", return_value=False):
            provider = LLMProvider()
            mock_client = MagicMock()
            mock_client.generate = MagicMock(return_value="openrouter response")
            provider.openrouter = mock_client
            provider.active = "openrouter"
            result = provider.generate("test")
            assert result == "openrouter response"

    def test_openrouter_generate_structured(self):
        with patch.object(OllamaAdapter, "is_available", return_value=False):
            provider = LLMProvider()
            mock_client = MagicMock()
            mock_client.generate_structured = MagicMock(return_value={"x": 1})
            provider.openrouter = mock_client
            provider.active = "openrouter"
            schema = {"type": "object", "properties": {"x": {"type": "integer"}}}
            result = provider.generate_structured("test", schema)
            assert result == {"x": 1}

    def test_openrouter_import_fallback(self):
        with patch.object(OllamaAdapter, "is_available", return_value=False):
            mock_client = MagicMock()
            fake_module = MagicMock()
            fake_module.LLMClient = MagicMock(return_value=mock_client)
            with patch.dict(sys.modules, {"src.llm.client": fake_module, "llm.client": fake_module}):
                provider = LLMProvider(openrouter_key="test-key")
                assert provider.openrouter is not None

    def test_generate_with_model_param(self):
        with patch.object(OllamaAdapter, "is_available", return_value=True):
            provider = LLMProvider()
            with patch.object(provider.ollama, "generate", return_value="test") as mock_gen:
                provider.generate("test", model="custom-model")
                _, kwargs = mock_gen.call_args
                assert kwargs["model"] == "custom-model"

    def test_generate_structured_with_model_param(self):
        with patch.object(OllamaAdapter, "is_available", return_value=True):
            provider = LLMProvider()
            with patch.object(provider.ollama, "generate_structured", return_value={}) as mock_gen:
                schema = {"type": "object", "properties": {}}
                provider.generate_structured("test", schema, model="custom-model")
                _, kwargs = mock_gen.call_args
                assert kwargs["model"] == "custom-model"


# ═══════════════════════════════════════════════════════════════════
# Edge Cases
# ═══════════════════════════════════════════════════════════════════


class TestEdgeCases:
    def test_adapter_custom_url(self):
        a = OllamaAdapter(base_url="http://other:8080")
        assert a.base_url == "http://other:8080"

    def test_generate_empty_prompt(self, adapter, mock_response):
        data = {"response": ""}
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.return_value = mock_response(data)
            result = adapter.generate("")
            assert result == ""

    def test_list_models_no_models_key(self, adapter, mock_response):
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.return_value = mock_response({})
            models = adapter.list_models()
        assert models == []

    def test_recommend_model_exact_thresholds(self):
        assert OllamaAdapter.recommend_model(80) == "llama3.1:70b"
        assert OllamaAdapter.recommend_model(79) == "llama3.1:70b-q4_0"
        assert OllamaAdapter.recommend_model(40) == "llama3.1:70b-q4_0"
        assert OllamaAdapter.recommend_model(39) == "qwen2.5:14b"
        assert OllamaAdapter.recommend_model(24) == "qwen2.5:14b"
        assert OllamaAdapter.recommend_model(23) == "qwen2.5:14b-q4_0"
        assert OllamaAdapter.recommend_model(16) == "qwen2.5:14b-q4_0"
        assert OllamaAdapter.recommend_model(15) == "qwen2.5:7b"
        assert OllamaAdapter.recommend_model(8) == "qwen2.5:7b"
        assert OllamaAdapter.recommend_model(7) == "phi3:medium"

    def test_llm_provider_both_available_prefers_openrouter(self):
        with patch.object(OllamaAdapter, "is_available", return_value=True):
            mock_client = MagicMock()
            fake_module = MagicMock()
            fake_module.LLMClient = MagicMock(return_value=mock_client)
            with patch.dict(sys.modules, {"src.llm.client": fake_module, "llm.client": fake_module}):
                provider = LLMProvider(openrouter_key="key")
                assert provider.active == "openrouter"

    def test_llm_provider_both_available_prefers_local(self):
        with patch.object(OllamaAdapter, "is_available", return_value=True):
            mock_client = MagicMock()
            fake_module = MagicMock()
            fake_module.LLMClient = MagicMock(return_value=mock_client)
            with patch.dict(sys.modules, {"src.llm.client": fake_module, "llm.client": fake_module}):
                provider = LLMProvider(openrouter_key="key", prefer_local=True)
                assert provider.active == "ollama"

    def test_generate_response_missing_key(self, adapter, mock_response):
        data = {}  # No "response" key
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.return_value = mock_response(data)
            result = adapter.generate("test")
            assert result == ""

    def test_generate_structured_empty_schema(self, adapter, mock_response):
        data = {"response": "{ }"}
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.return_value = mock_response(data)
            schema = {"type": "object", "properties": {}}
            result = adapter.generate_structured("test", schema)
            assert result == {}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
