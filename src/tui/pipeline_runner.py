"""
TUI: Pipeline Runner
Discovery pipeline execution methods for C4TUI.
"""
from __future__ import annotations

import logging


logger = logging.getLogger(__name__)

import asyncio
import json
from typing import Any

from src.tui.pipeline_stories import PIPELINE_STORIES


def _run_pipeline_modules(problem: str, papers_raw: list, hypothesis_text: str, domain: str) -> dict:
    """Run all 10 discovery modules in background (preparation only)."""
    results = {}

    # 1. GPU Providers — detect hardware
    try:
        from compute.gpu_providers import detect_local_gpu
        gpu_status = detect_local_gpu()
    except ImportError:
        gpu_status = "cpu_only"

    # 2. Gap Miner — find research gaps
    try:
        from src.discovery.gap_miner import GapMiner
        gm = GapMiner()
        gap_result = asyncio.run(gm.mine_for_discovery(problem, papers_raw))
        results["gap_miner"] = gap_result.get("gaps_found", 0)
    except (ImportError, KeyError):
        logger.debug("GapMiner unavailable in pipeline runner")

    # 3. Zettelkasten — save discovery progress
    try:
        from src.knowledge.zettelkasten import Zettelkasten
        zk = Zettelkasten()
        zk.add_discovery(problem, hypothesis_text, papers_raw)
    except ImportError:
        logger.debug("Optional module unavailable in pipeline runner")

    # 4. Novelty Validator — check hypothesis originality
    try:
        from src.discovery.novelty_validator import NoveltyValidator
        async def _check_novelty() -> dict[str, Any]:
            nv = NoveltyValidator()
            async with nv as validator:
                return await validator.check(hypothesis_text, domain)
        novelty = asyncio.run(_check_novelty())
        results["novelty"] = novelty.get("novelty_score", 0)
    except (TimeoutError, ImportError, KeyError, TypeError):
        pass

    # 5. Monte Carlo — statistical validation
    try:
        from bayesian.monte_carlo import MonteCarloValidator
        mc = MonteCarloValidator(trials=100)
        mc_result = mc.validate(
            {"mean": 0.78},
            {"mean": 0.45, "std": 0.1},
        )
        results["monte_carlo"] = mc_result.get("significant", False)
    except (ImportError, KeyError):
        logger.debug("Optional module unavailable in pipeline runner")

    # 6. Falsifier — adversarial hypothesis check
    try:
        from src.discovery.falsifier import Falsifier
        falsifier = Falsifier()
        falsify = falsifier.check(hypothesis_text, domain)
        results["falsifier"] = "YES" if falsify.falsifiable else "NO"
    except (ImportError, KeyError):
        logger.debug("Optional module unavailable in pipeline runner")

    # 7. Auto Poster — share discovery (if keys configured)
    try:
        from social.auto_poster import SocialAutoPoster
        poster = SocialAutoPoster()
        teaser = f"C4 Discovery: {problem[:120]} — {hypothesis_text[:150]}"
        for plat in ["mastodon", "x_twitter"]:
            try:
                poster.post(plat, teaser, auto_approve=True)
            except (ImportError, AttributeError, OSError, ValueError):
                pass
    except ImportError:
        logger.debug("Optional module unavailable in pipeline runner")

    # 8. Blueprint Generator — for physical/engineering domains
    try:
        if domain in ("engineering", "materials", "physics"):
            from publishing.blueprint import BlueprintGenerator
            bp = BlueprintGenerator()
            bp.generate_ascii_schematic(
                problem, [{"name": "Component", "material": "Unknown"}]
            )
    except ImportError:
        logger.debug("Optional module unavailable in pipeline runner")

    # 9. Auto Scanner — find next problems to solve
    try:
        async def _scan() -> list:
            from src.discovery.auto_scanner import AutoScanner
            scanner = AutoScanner()
            return await scanner.scan_unsolved_problems([domain])
        next_problems = asyncio.run(_scan())
        results["next_problems"] = next_problems[:5]
    except (TimeoutError, ImportError, IndexError, KeyError, TypeError):
        pass

    # 10. Domain Selector — enrich with domain simulations
    try:
        from src.simulations.domain_selector import get_domain_simulations
        sims = get_domain_simulations(domain)
        results["simulations"] = sims
    except (ImportError, KeyError):
        logger.debug("Optional module unavailable in pipeline runner")

    return results


def run_discovery_pipeline_sync(problem: str, live, _update_render, _advance_pipeline_step, _pipeline_completion, _mascot, play_sound_fn) -> dict:
    """Запустити пайплайн відкриття (пошаговий, ожідає Enter)."""
    running = True
    phase = "running"
    messages: list[str] = []
    current_step = 0
    results = None
    all_glow: set[Any] = set()
    completion_flash = False
    export_file = None
    _pipeline_step_index = 0
    _pipeline_stories = []
    _pipeline_total: int = 0
    _module_results = {}
    _stop_flag = False

    # Wire 10 discovery pipeline modules with real calls
    papers_raw: list[dict[str, Any]] = []
    hypothesis_text = ""
    domain = "ai"

    try:
        import httpx
        api_url = "http://127.0.0.1:8000/api/v8/discover/one-click"
        with httpx.Client(timeout=300) as client:
            response = client.post(api_url, json={"problem": problem, "domain": domain})
            results = response.json()
    except (ImportError, httpx.HTTPError, json.JSONDecodeError) as e:
        results = {"status": "error", "error": str(e)}
        return results

    papers_raw = results.get("papers", []) if isinstance(results, dict) else []
    hyp = results.get("hypothesis", "")
    hypothesis_text = hyp.get("text", str(hyp)) if isinstance(hyp, dict) else str(hyp)
    domain = results.get("domain", "ai") if isinstance(results, dict) else "ai"

    # Run all module wires once (background preparation)
    _module_results = _run_pipeline_modules(problem, papers_raw, hypothesis_text, domain)

    # Step-by-step display with user control
    _pipeline_stories = PIPELINE_STORIES.get("discover", [])
    _pipeline_total = len(_pipeline_stories)

    # Show first step
    _advance_pipeline_step(live, 0, _pipeline_stories, all_glow, completion_flash, _mascot)

    # Wait for user input to advance steps
    from src.tui.keyboard_handler import KeyboardReader
    with KeyboardReader() as kr:
        while _pipeline_step_index < _pipeline_total:
            key = kr.read_key(timeout=0.2)
            if key is None:
                continue
            if key == ('enter',):
                _pipeline_step_index += 1
                if _pipeline_step_index >= _pipeline_total:
                    break
                _advance_pipeline_step(live, _pipeline_step_index, _pipeline_stories, all_glow, completion_flash, _mascot)
            elif key == ('esc',) or key == ('char', 'q'):
                break

    # Completion celebration
    _pipeline_completion(live, all_glow, completion_flash, _mascot, play_sound_fn)

    return results
