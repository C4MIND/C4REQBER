"""Tests for FormalFrameworkExtender."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from src.exploration.formal_extender import ExtensionProposal, FormalFrameworkExtender


class TestExtensionProposal:
    def test_to_dict_truncates_code(self) -> None:
        proposal = ExtensionProposal(
            language="lean4",
            code="x" * 1000,
            description="test",
            compiles=True,
        )
        d = proposal.to_dict()
        assert len(d["code"]) == 500
        assert d["language"] == "lean4"
        assert d["compiles"] is True


class TestFormalFrameworkExtender:
    def test_extract_code_from_markdown(self) -> None:
        extender = FormalFrameworkExtender()
        text = "```lean4\nimport Mathlib\n```"
        code = extender._extract_code(text, "lean4")
        assert code == "import Mathlib"

    def test_extract_code_any_fence(self) -> None:
        extender = FormalFrameworkExtender()
        text = "```\nimport Mathlib\n```"
        code = extender._extract_code(text, "lean4")
        assert code == "import Mathlib"

    def test_extract_code_no_fence(self) -> None:
        extender = FormalFrameworkExtender()
        text = "import Mathlib"
        code = extender._extract_code(text, "lean4")
        assert code == "import Mathlib"

    @pytest.mark.anyio(backend="asyncio")
    async def test_propose_with_mock(self) -> None:
        extender = FormalFrameworkExtender()
        with patch.object(extender._router, "generate", new_callable=AsyncMock, return_value=AsyncMock(content="```lean4\nimport Mathlib\n```")):
            result = await extender.propose("mathlib4", "test gap")
        assert result is not None
        assert result.language == "lean4"
        assert "test gap" in result.description

    def test_propose_alias_callable(self) -> None:
        extender = FormalFrameworkExtender()
        assert callable(extender.propose)
