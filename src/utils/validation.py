"""
C4REQBER: Startup Validation
Validates configuration before starting services
"""
from __future__ import annotations

import os
import sys
from typing import Any


class StartupValidator:
    """Validates system configuration on startup."""

    @staticmethod
    def validate_api_keys() -> tuple[bool, list[str]]:
        """
        Validate required API keys.

        Returns:
            (is_valid, missing_keys)
        """
        # For CLI-only mode, OpenRouter is optional (mock works)
        # For API mode, these are recommended but not strictly required

        recommended = {
            "OPENROUTER_API_KEY": "LLM integration (OpenRouter)",
            "SEMANTIC_SCHOLAR_API_KEY": "Academic paper search (optional)",
        }

        missing = []
        warnings = []

        for key, description in recommended.items():
            if not os.getenv(key):
                if key == "OPENROUTER_API_KEY":
                    missing.append(f"{key} ({description})")
                else:
                    warnings.append(
                        f"{key} not set - {description} will have reduced functionality"
                    )

        # Critical for API mode
        critical_for_api = {
            "JWT_SECRET": "API authentication (generate with: openssl rand -hex 32)",
            "DATABASE_URL": "PostgreSQL connection string",
        }

        critical_missing = []
        for key, description in critical_for_api.items():
            if not os.getenv(key):
                critical_missing.append(f"{key}: {description}")

        is_valid = len(critical_missing) == 0

        return is_valid, critical_missing + missing, warnings  # type: ignore[return-value]

    @staticmethod
    def print_validation_report() -> Any:
        """Print validation report and exit if critical errors."""
        is_valid, errors, warnings = StartupValidator.validate_api_keys()  # type: ignore[misc]

        if warnings:
            print("⚠️  Warnings:")
            for w in warnings:
                print(f"   - {w}")
            print()

        if errors:
            print("🔴 Missing required configuration:")
            for e in errors:
                print(f"   - {e}")
            print()
            print("Set environment variables or create .env file")
            return False

        print("✅ Configuration valid")
        return True


def validate_on_startup() -> None:
    """Run validation on module import."""
    # Only validate in API mode
    if os.getenv("C4REQBER_MODE") == "api":
        if not StartupValidator.print_validation_report():
            sys.exit(1)
