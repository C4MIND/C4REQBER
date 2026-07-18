#!/usr/bin/env python3
"""Check API keys before running tests. Warns which tests will be skipped."""

from __future__ import annotations

import os
import sys


def check_key(name: str, env_var: str, required_for: list[str]) -> bool:
    value = os.environ.get(env_var, "")
    has_key = bool(value) and not value.startswith("YOUR_")
    status = "✅" if has_key else "❌"
    tests = ", ".join(required_for)
    print(f"  {status} {name:<20} {env_var:<30} → {tests}")
    return has_key


def main() -> int:
    print("═" * 70)
    print("  API KEY CHECK — c4reqber Test Suite")
    print("═" * 70)
    print()

    # Load keys: repo .env, then maintainer .env.dontredact (knowledge SSOT)
    for env_file in (".env", ".env.development", ".env.dontredact"):
        if os.path.exists(env_file):
            with open(env_file) as f:
                for line in f:
                    if "=" in line and not line.startswith("#"):
                        key, val = line.strip().split("=", 1)
                        os.environ[key] = val.strip().strip('"').strip("'")

    all_ok = True

    print("LLM Providers:")
    all_ok &= check_key("OpenRouter", "OPENROUTER_API_KEY", ["LLM routing", "multi-provider tests"])
    all_ok &= check_key("DeepSeek", "DEEPSEEK_API_KEY", ["cheap inference"])
    all_ok &= check_key("NVIDIA", "NVIDIA_API_KEY", ["free models (40 rpm)"])
    all_ok &= check_key("Liquid", "LIQUID_API_KEY", ["inference"])
    print()

    print("Search Engines:")
    all_ok &= check_key("Brave", "BRAVE_API_KEY", ["web search", "WebSearchPlugin"])
    check_key("Tavily", "TAVILY_API_KEY", ["AI search"])
    check_key("Exa", "EXA_API_KEY", ["neural search"])
    print()

    print("Knowledge Bases (.env.dontredact):")
    check_key("OpenAlex", "OPENALEX_API_KEY", ["paper search", "Phase B"])
    check_key("CORE", "CORE_API_KEY", ["open access papers"])
    check_key("NCBI", "NCBI_API_KEY", ["PubMed", "gene search"])
    check_key("NCBI email", "NCBI_EMAIL", ["PubMed rate limits"])
    check_key("Unpaywall", "UNPAYWALL_EMAIL", ["OA PDF links"])
    check_key("OpenFDA", "OPENFDA_API_KEY", ["drug/clinical data"])
    check_key("Materials Project", "MATERIALS_PROJECT_API_KEY", ["materials science"])
    check_key("NOAA", "NOAA_API_KEY", ["climate/ocean data"])
    check_key("NASA Earthdata", "NASA_EARTHDATA_TOKEN", ["satellite data"])
    check_key("Kaggle", "KAGGLE_KEY", ["datasets"])
    check_key("BibSonomy", "BIBSONOMY_API_KEY", ["social bibliography"])
    check_key("Datacite", "DATACITE_API_KEY", ["DOI metadata"])
    print()

    print("Social Media (fill before testing posting):")
    check_key("X/Twitter", "X_BEARER_TOKEN", ["auto-posting"])
    check_key("Mastodon", "MASTODON_ACCESS_TOKEN", ["auto-posting"])
    check_key("Telegram", "TELEGRAM_BOT_TOKEN", ["bot delivery"])
    check_key("Bluesky", "BLUESKY_APP_PASSWORD", ["auto-posting"])
    print()

    print("Formal Verification:")
    has_lean = check_key("Lean4", "LEAN4_PATH", ["theorem proving"])
    has_coq = check_key("Coq", "COQ_PATH", ["proof assistant"])
    has_dafny = check_key("Dafny", "DAFNY_PATH", ["program verification"])
    has_agda = check_key("Agda", "AGDA_PATH", ["type theory"])
    has_z3 = check_key("Z3", "Z3_PATH", ["Hoare logic"])
    print()

    print("═" * 70)
    if all_ok:
        print("  ✅ All critical keys present. Ready for full test suite.")
    else:
        print("  ⚠️  Some keys missing. Tests using those APIs will be skipped.")
        print("     To run skipped tests, add keys to .env.development")
    print("═" * 70)

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
