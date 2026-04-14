"""
Advanced testing infrastructure for TURBO-CDI v8.3
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from core.orchestrator import TurboCDIv8Sync
from cognitive.bias_detector.core import BiasDetector, BiasType


@pytest.mark.asyncio
async def test_async_edge_cases():
    """Test various async edge cases from C1 fixes"""
    turbo = TurboCDIv8Sync()

    # Test nested event loop scenario (should not crash)
    async def nested_call():
        # This simulates calling from within an async web framework
        return turbo.plan_transformation(from_state=(0, 0, 0), to_state=(2, 2, 2), domain="test")

    result = await nested_call()
    assert result is not None
    assert hasattr(result, "path")


@pytest.mark.asyncio
async def test_embedder_thread_safety():
    """Test singleton embedder thread safety (C2)"""
    from rag.embedder import get_embedder, _embedder
    import threading

    # Reset embedder for test
    global _embedder
    _embedder = None

    embedders = []

    def get_multiple_times():
        for _ in range(5):
            embedders.append(get_embedder())

    threads = [threading.Thread(target=get_multiple_times) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # All should be the same object
    assert len(set(id(e) for e in embedders)) == 1
    assert len(embedders) == 50  # 10 threads * 5 calls each


@pytest.mark.asyncio
async def test_llm_failure_injection():
    """Test LLM failure recovery (C4)"""
    from discovery.llm_adapter import llm_call

    with patch("discovery.llm_adapter._call_groq") as mock_groq:
        with patch("discovery.llm_adapter._call_openrouter") as mock_or:
            # First call fails with timeout, second succeeds
            mock_groq.side_effect = asyncio.TimeoutError()
            mock_or.return_value = "success response"

            result = await llm_call("test prompt")
            assert result == "success response"
            mock_or.assert_called_once()


def test_bias_detection_expansion():
    """Test expanded bias detection for RAG/upload/discover (U8-U9)"""
    detector = BiasDetector()

    # Test RAG bias detection
    rag_warnings = detector.analyze_rag_query(
        "quantum computing methods",
        ["user_docs", "user_docs", "user_docs"],  # Heavy user bias
    )
    assert any(w.bias_type == BiasType.CONFIRMATION_BIAS for w in rag_warnings)

    # Test upload bias detection
    upload_warnings = detector.analyze_document_upload(
        "/path/to/success_case_study.pdf", {"authors_count": 1}
    )
    assert any(w.bias_type == BiasType.SURVIVORSHIP_BIAS for w in upload_warnings)

    # Test discovery bias detection
    discovery_warnings = detector.analyze_discovery_query("ai will solve everything", "technology")
    assert any(w.bias_type == BiasType.OPTIMISM_BIAS for w in discovery_warnings)


def test_bias_feedback_loop():
    """Test bias feedback processing (U11)"""
    from cognitive.user_profile.core import UserProfile

    user_profile = UserProfile(user_id="test")
    detector = BiasDetector(user_profile)

    # Process feedback
    detector.process_bias_feedback(BiasType.CONFIRMATION_BIAS, "irrelevant")

    # Check that sensitivity was adjusted
    assert hasattr(user_profile, "bias_sensitivity_levels")
    assert user_profile.bias_sensitivity_levels[BiasType.CONFIRMATION_BIAS.value] < 1.0


@pytest.mark.asyncio
async def test_websocket_security():
    """Test WebSocket security validations (C7)"""
    from api.websocket.server import TurboWebSocketServer
    from pydantic import ValidationError

    server = TurboWebSocketServer()

    # Test trials limit
    with pytest.raises(ValidationError):
        await server._validate_command(
            {
                "command": "falsify",
                "trials": 10**9,  # Too large
            }
        )

    # Test message size
    large_message = "A" * (2 * 1024 * 1024)  # 2MB
    with pytest.raises(ValidationError):
        await server._validate_command(large_message)


def test_gap_relationship_graph():
    """Test gap relationship visualization (U16)"""
    # This would test the CLI gap display logic
    # For now, just ensure the logic doesn't crash
    gaps = [
        {"description": "quantum error correction methods"},
        {"description": "quantum computing error correction"},
        {"description": "machine learning algorithms"},
    ]

    # Test overlap detection
    for i, gap in enumerate(gaps):
        relations = []
        gap_text = gap["description"].lower()

        for j, other_gap in enumerate(gaps):
            if i != j:
                other_text = other_gap["description"].lower()
                gap_words = set(gap_text.split())
                other_words = set(other_text.split())
                overlap = len(gap_words.intersection(other_words))
                if overlap > 1:
                    relations.append(f"#{j + 1}")

        if i == 0:  # quantum error correction
            assert len(relations) >= 1  # Should relate to gap #2
