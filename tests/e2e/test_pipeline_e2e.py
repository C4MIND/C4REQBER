"""Test runner for UniversalSolvePipeline — all 10 steps including step 10"""
import asyncio
import os
import sys
import pytest
import time
from pathlib import Path


_project_root = Path(__file__).resolve().parent
_dotenv_path = _project_root / ".env"
if _dotenv_path.exists():
    with open(_dotenv_path) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _key, _, _val = _line.partition("=")
                _key = _key.strip()
                _val = _val.strip().strip('"').strip("'")
                if _key and _val and _key not in os.environ:
                    os.environ[_key] = _val

_missing = [k for k in ("OPENROUTER_API_KEY",) if not os.environ.get(k)]
if _missing:
    print(f"WARNING: Missing env vars: {_missing}. Set in .env or environment.")
    print("Run: cp .env.example .env && edit .env with your keys")
    pytest.skip(f"Missing env vars: {_missing}")

import src.llm.config as _llm_config


_llm_config._PROVIDER_DEFAULT_MODELS[_llm_config.LLMProvider.OPENROUTER] = "google/gemini-2.0-flash-001"

from src.agents.pipeline import UniversalSolvePipeline


async def main():
    problem = "How to reduce energy consumption in data centers"
    mode = "full"
    print(f"Problem: {problem}")
    print(f"Mode: {mode}")
    print("=" * 60)

    start = time.monotonic()
    pipeline = UniversalSolvePipeline()
    pipeline.set_pattern("thermal")

    step_events = []
    final_result = None
    try:
        async for event in pipeline.solve_streaming(problem, mode=mode):
            ev = {k: v for k, v in event.items()}
            if "result" in ev and hasattr(ev["result"], "to_dict"):
                ev["result"] = ev["result"].to_dict()
            print(f"EVENT: {ev.get('event'):12s} | stage={ev.get('stage')} | status={ev.get('status')} | err={ev.get('error')}")
            if ev.get("event") == "step_complete":
                step_events.append(ev)
            if ev.get("event") == "complete":
                final_result = ev.get("result", {})
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await pipeline.close()

    elapsed = time.monotonic() - start

    print("\n--- STEP SUMMARY ---")
    for i, ev in enumerate(step_events, 1):
        dur = ev.get('duration_ms', 0)
        print(f"Step {i:02d}: {ev.get('stage'):25s} | {ev.get('status'):10s} | {dur:.0f}ms | err={ev.get('error') or 'None'}")

    print(f"\n--- FINAL SOLUTION ---")
    sol = final_result.get("final_solution", "") if final_result else ""
    print(sol[:4000] if sol else "(empty)")
    if len(sol or "") > 4000:
        print(f"... ({len(sol)} chars total)")

    print(f"\n--- METRICS ---")
    if final_result:
        print(f"Confidence: {final_result.get('confidence')}")
        print(f"Isomorphism found: {final_result.get('isomorphism_found')}")
        print(f"C4 path: {final_result.get('c4_path')}")
        print(f"MP perspectives: {len(final_result.get('mp_perspectives', []))}")
        print(f"QZRF recommendations: {final_result.get('qzrf_recommendations', [])}")
    print(f"Total time: {elapsed:.2f}s")

if __name__ == "__main__":
    asyncio.run(main())
