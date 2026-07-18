from __future__ import annotations

import asyncio
import logging
from typing import Any

from src.mcp_server.tool_dependencies import C4State


logger = logging.getLogger(__name__)


async def c4_autoresearch(
    file: str,
    metric: str = "val_bpb",
    max_iter: int = 100,
) -> dict[str, Any]:
    """Run Karpathy-style iterative autoresearch loop on a Python training file.

    Implements: propose → execute → evaluate → keep/revert loop with C4-guided mutations.
    Multi-agent parallel execution is enabled via the orchestrator.

    Args:
        file: Path to the Python training script to optimize.
        metric: Metric name to extract from stdout/logs (e.g. val_bpb, val_loss).
        max_iter: Maximum number of mutations to try.

    Returns:
        Report with best_metric, best_iteration, total_iterations, and trace.
    """
    try:
        from src.operators.autoresearch import run_autoresearch

        report = await asyncio.to_thread(
            run_autoresearch,
            file=file,
            metric=metric,
            max_iter=max_iter,
        )
        status = "success"
        warnings: list[str] = []
        if getattr(report, "total_iterations", 0) <= 0:
            status = "partial"
            warnings.append("no iterations completed")
        elif getattr(report, "best_iteration", None) in (None, -1, 0) and not getattr(
            report, "improvement_trace", None
        ):
            status = "partial"
            warnings.append("no improvement recorded")
        out: dict[str, Any] = {
            "status": status,
            "data": {
                "best_metric": report.best_metric,
                "best_iteration": report.best_iteration,
                "total_iterations": report.total_iterations,
                "total_duration_seconds": report.total_duration_seconds,
                "improvement_trace": report.improvement_trace,
            },
        }
        if warnings:
            out["warnings"] = warnings
        return out
    except Exception as e:
        logger.exception("MCP tool failed")
        return {"error": str(e), "status": "error"}


async def c4_chain(
    problem: str,
    from_state: list[int] | None = None,
    to_state: list[int] | None = None,
) -> dict[str, Any]:
    """Compute C4 discovery chain (Theorem 11: ≤6 steps between any two states).

    If both states are provided, returns the canonical path between them.
    If only `problem` is provided, loads discovery history and returns
    the nearest past discovery with chaining path.
    """
    try:
        from src.discovery.chainer import DiscoveryChainer
    except ImportError:
        try:
            from src.discovery.chainer import DiscoveryChainer
        except ImportError as e:
            return {"error": f"DiscoveryChainer not available: {e}"}

    chainer = DiscoveryChainer()

    if from_state is not None and to_state is not None:
        s1 = C4State(T=from_state[0], S=from_state[1], A=from_state[2])
        s2 = C4State(T=to_state[0], S=to_state[1], A=to_state[2])
        path = chainer.compute_path(s1, s2)
        return {
            "from_state": from_state,
            "to_state": to_state,
            "path": path,
            "step_count": len(path),
            "theorem": "Theorem 11: diameter of C4Space = 6",
        }

    suggestion = chainer.chain_from_history(problem, [])
    if suggestion is None:
        return {
            "problem": problem,
            "path": [],
            "step_count": 0,
            "note": "No prior discoveries found for this problem.",
        }
    return suggestion.to_dict()


async def c4_meta(reasoning_trace: str, depth: int = 2) -> dict[str, Any]:
    """Meta-cognitive reflection on reasoning quality and path optimization.

    Analyzes a reasoning trace through C4 state space, identifies
    meta-cognitive gaps, and suggests alternative operator sequences.
    """
    try:
        from src.c4.engine import C4Space, C4State
        from src.c4.routing import FRARouter, QualityPreset
    except ImportError as e:
        return {"error": f"C4 engine not available: {e}"}

    router = FRARouter()
    space = C4Space()

    # Fingerprint current reasoning state
    state = router.classify_c4_state(reasoning_trace)

    # Find optimal meta-cognitive states (high A dimension)
    meta_states = [s for s in space.all_states() if s.A >= 1]
    if not meta_states:
        meta_states = space.all_states()

    # Route to nearest meta-cognitive state
    target = min(meta_states, key=lambda s: space.hamming_distance(state, s))
    route = router.find_route(state, target, preset=QualityPreset.SYNTHESIS)

    # Generate reflection
    reflections = [
        f"Current reasoning maps to C4 state {state} (T={state.T}, S={state.S}, A={state.A})",
        f"Recommended meta-cognitive shift: {' → '.join(route.operators[:depth])}",
        f"Hamming distance to optimal meta-state: {route.hamming_distance}",
    ]

    if route.hamming_distance >= 3:
        reflections.append(
            "⚠️ Reasoning is far from meta-cognitive zone. Consider explicit reflection."
        )
    elif route.hamming_distance <= 1:
        reflections.append("✓ Reasoning is already in meta-cognitive zone.")

    return {
        "state": str(state),
        "target_meta_state": str(target),
        "hamming_distance": route.hamming_distance,
        "operators": route.operators[:depth],
        "reflections": reflections,
        "depth": depth,
    }


async def c4_social(action: str, draft_id: str = "", platform: str = "") -> dict[str, Any]:
    """Social publishing — preprint upload, post to platforms, health check.

    Actions: status, publish, preview, drafts, health, post.

    Args:
        action: status | publish | preview | drafts | health | post
        draft_id: Draft ID for publish/preview/post actions
        platform: Target platform for post action (twitter, mastodon, reddit, discord, slack)
    """
    from pathlib import Path

    if action == "status":
        from src.social.profile_manager import UserProfile

        p = UserProfile.load()
        drafts_dir = Path.home() / ".c4reqber" / "drafts"
        draft_count = (
            len([d for d in drafts_dir.iterdir() if d.is_dir()]) if drafts_dir.exists() else 0
        )
        return {"author": p.primary_author.name, "orcid": p.orcid_ids, "drafts": draft_count}

    if action == "health":
        from src.social.health_checker import check_all

        return await check_all()

    if action == "drafts":
        drafts_dir = Path.home() / ".c4reqber" / "drafts"
        if not drafts_dir.exists():
            return {"drafts": []}
        import json

        result = []
        for d in sorted(drafts_dir.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True)[:20]:
            if d.is_dir():
                state = (
                    json.loads((d / "draft_state.json").read_text())
                    if (d / "draft_state.json").exists()
                    else {}
                )
                result.append({"id": d.name, "status": state.get("status", "?")})
        return {"drafts": result}

    if action == "preview" and draft_id:
        draft_dir = Path.home() / ".c4reqber" / "drafts" / draft_id
        md = draft_dir / "dissertation.md"
        if md.exists():
            return {"draft_id": draft_id, "content": md.read_text(encoding="utf-8")[:5000]}
        return {"error": f"Draft {draft_id} not found"}

    if action == "publish" and draft_id:
        from src.social.publisher import Publisher

        pub = Publisher()
        result = await pub.publish(draft_id)
        return result.get("steps", result)

    if action == "post" and draft_id and platform:
        from src.social.post_dispatcher import post_draft

        try:
            result = await post_draft(draft_id, platform=platform, dry_run=False)
        except (FileNotFoundError, ValueError) as exc:
            return {"error": str(exc)}
        return result

    return {
        "error": f"Unknown action: {action}. Use: status, publish, preview, drafts, health, post"
    }
