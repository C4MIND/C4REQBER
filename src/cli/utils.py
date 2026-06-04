#!/usr/bin/env python3
"""C4REQBER CLI — Utility command implementations."""
from __future__ import annotations

from typing import Any

from src.cli.core import get_llm_client, print_banner


def cmd_operators(args: Any) -> Any:
    """List all 27 operators."""
    from src.core.operators import Operators

    ops = Operators()

    print("\n" + "=" * 60)
    print("C4REQBER OPERATORS (27 total)")
    print("=" * 60)

    print("\n--- Base Operators (9) ---")
    for name, op in ops.base.items():
        print(f"  {op.symbol:8} | {name:20} | {op.description}")

    print("\n--- Composed Operators (18) ---")
    for name, op in ops.composed.items():
        print(f"  {op.symbol:8} | {name:25} | {op.description}")

    print("\n" + "=" * 60 + "\n")

    return 0


def cmd_test_llm(args: Any) -> None:
    """Test LLM connection."""
    print_banner()

    print("Testing LLM connection...")

    try:
        llm = get_llm_client()
    except RuntimeError as e:
        print("✗ No LLM provider available.\n")
        print(f"    {e}")
        return 1  # type: ignore[return-value]

    if llm.test_connection():
        print("✓ LLM connection successful!")
        print(f"  Default model: {llm.DEFAULT_MODEL}\n")
        return 0  # type: ignore[return-value]
    else:
        print("✗ LLM connection failed. Check your API key.\n")
        return 1  # type: ignore[return-value]
