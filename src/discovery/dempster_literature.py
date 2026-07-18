"""Literature Dempster-Shafer fusion with optional NLI stance scoring."""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any, Callable


logger = logging.getLogger(__name__)

_SUPPORT_KW = (
    "support",
    "supports",
    "confirm",
    "consistent",
    "agree",
    "demonstrate",
    "show that",
    "evidence for",
    "improve",
    "outperform",
    "significant",
    "validate",
)
_REFUTE_KW = (
    "refute",
    "contradict",
    "inconsistent",
    "fail",
    "cannot",
    "impossible",
    "against",
    "challenge",
    "disprove",
    "invalid",
    "not supported",
)


def _tokens(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-zA-Z]{4,}", text.lower()) if t}


def _count_hits(text: str, keywords: tuple[str, ...]) -> int:
    lower = text.lower()
    return sum(1 for kw in keywords if kw in lower)


def paper_stance_keywords(paper: dict[str, Any], hypothesis_tokens: set[str]) -> dict[str, Any]:
    """Keyword/overlap stance (heuristic)."""
    title = str(paper.get("title", "") or "")
    abstract = str(paper.get("abstract", "") or paper.get("description", "") or "")
    blob = f"{title}. {abstract}"
    paper_toks = _tokens(blob)
    overlap = len(hypothesis_tokens & paper_toks)
    support = float(_count_hits(blob, _SUPPORT_KW))
    refute = float(_count_hits(blob, _REFUTE_KW))

    if overlap == 0 and support == 0 and refute == 0:
        return {
            "supported": 0.0,
            "refuted": 0.0,
            "untested": 1.0,
            "overlap": 0.0,
            "irrelevant": True,
            "method": "keywords",
        }

    rel = 1.0 + min(3.0, overlap / 5.0)
    if support == 0 and refute == 0:
        return {
            "supported": 0.5 * rel,
            "refuted": 0.5 * rel,
            "untested": 1.0,
            "overlap": float(overlap),
            "method": "keywords",
        }
    return {
        "supported": (support + 0.1) * rel,
        "refuted": (refute + 0.1) * rel,
        "untested": 0.5,
        "overlap": float(overlap),
        "method": "keywords",
    }


# Back-compat alias
paper_stance = paper_stance_keywords


def _parse_stance_json(text: str) -> dict[str, Any] | None:
    text = text.strip()
    if not text:
        return None
    # Extract first JSON object
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        obj = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None
    label = str(obj.get("label", obj.get("stance", ""))).lower()
    conf = float(obj.get("confidence", obj.get("score", 0.6)))
    conf = max(0.05, min(0.95, conf))
    if label in {"support", "supported", "entailment", "entails"}:
        return {
            "supported": conf * 2.0,
            "refuted": (1.0 - conf) * 0.5,
            "untested": 0.3,
            "overlap": 1.0,
            "method": "nli",
        }
    if label in {"refute", "refuted", "contradiction", "contradicts"}:
        return {
            "supported": (1.0 - conf) * 0.5,
            "refuted": conf * 2.0,
            "untested": 0.3,
            "overlap": 1.0,
            "method": "nli",
        }
    if label in {"neutral", "untested", "unknown"}:
        return {
            "supported": 0.4,
            "refuted": 0.4,
            "untested": 1.2,
            "overlap": 0.5,
            "method": "nli",
        }
    return None


_MNLI_PIPE: Any = None


def _load_hf_token() -> str | None:
    """Load HF token from env or standard cache file (never log the value)."""
    tok = (
        os.environ.get("HF_TOKEN")
        or os.environ.get("HUGGINGFACE_HUB_TOKEN")
        or os.environ.get("HUGGING_FACE_HUB_TOKEN")
    )
    if tok:
        return tok.strip()
    for path in (
        os.path.expanduser("~/.cache/huggingface/token"),
        os.path.expanduser("~/.huggingface/token"),
    ):
        try:
            if os.path.isfile(path):
                with open(path, encoding="utf-8") as f:
                    val = f.read().strip()
                if val:
                    os.environ.setdefault("HF_TOKEN", val)
                    return val
        except OSError:
            continue
    return None


def _get_mnli_pipeline() -> Any | None:
    """Cached zero-shot MNLI pipeline (facebook/bart-large-mnli)."""
    global _MNLI_PIPE
    if _MNLI_PIPE is not None:
        return _MNLI_PIPE
    try:
        from transformers import pipeline  # type: ignore
    except ImportError:
        return None

    _load_hf_token()
    # Prefer project-local HF cache if present
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    local_hf = os.path.join(root, ".cache", "huggingface")
    if os.path.isdir(local_hf):
        os.environ.setdefault("HF_HOME", local_hf)

    try:
        _MNLI_PIPE = pipeline(
            "zero-shot-classification",
            model="facebook/bart-large-mnli",
            device=-1,
        )
        return _MNLI_PIPE
    except Exception as exc:
        logger.info("MNLI pipeline init failed: %s", exc)
        return None


def paper_stance_mnli(paper: dict[str, Any], hypothesis: str) -> dict[str, Any] | None:
    """Local zero-shot MNLI if transformers + bart-large-mnli available."""
    clf = _get_mnli_pipeline()
    if clf is None:
        return None

    title = str(paper.get("title", "") or "")
    abstract = str(paper.get("abstract", "") or paper.get("description", "") or "")
    premise = f"{title}. {abstract}".strip()[:2000]
    if len(premise) < 20:
        return None

    hyp = (hypothesis or "").strip()[:400]
    if not hyp:
        return None

    try:
        # Labels encode the claim so MNLI compares paper vs hypothesis content.
        labels = [
            f"supports the claim that {hyp}",
            f"refutes the claim that {hyp}",
            f"is unrelated to the claim that {hyp}",
        ]
        out = clf(premise, candidate_labels=labels)
        best = str(out["labels"][0]).lower()
        conf = float(out["scores"][0])
        if best.startswith("supports"):
            label = "supported"
        elif best.startswith("refutes"):
            label = "refuted"
        else:
            label = "neutral"
        parsed = _parse_stance_json(json.dumps({"label": label, "confidence": conf}))
        if parsed:
            parsed["method"] = "nli_mnli"
        return parsed
    except Exception as exc:
        logger.info("MNLI stance unavailable: %s", exc)
        return None


def paper_stance_llm(
    paper: dict[str, Any],
    hypothesis: str,
    *,
    llm_generate: Callable[..., str] | None = None,
) -> dict[str, Any] | None:
    """LLM JSON stance (supports/refutes/neutral)."""
    title = str(paper.get("title", "") or "")
    abstract = str(paper.get("abstract", "") or paper.get("description", "") or "")
    prompt = (
        "Classify how the paper relates to the hypothesis.\n"
        'Return ONLY JSON: {"label":"supported|refuted|neutral","confidence":0.0-1.0}\n'
        f"Hypothesis: {hypothesis[:500]}\n"
        f"Paper title: {title}\n"
        f"Abstract: {abstract[:1200]}\n"
    )

    text = ""
    if llm_generate is not None:
        try:
            text = llm_generate(prompt)
        except Exception as exc:
            logger.info("Injected LLM stance failed: %s", exc)
            return None
    else:
        try:
            api_key = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("C4_LLM_API_KEY")
            if not api_key:
                return None
            import asyncio

            from src.llm.multi_provider import OpenRouterClient

            client = OpenRouterClient()

            async def _go() -> str:
                resp = await client.generate(prompt, temperature=0.0, max_tokens=80)
                return getattr(resp, "text", None) or getattr(resp, "content", None) or str(resp)

            try:
                text = asyncio.run(_go())
            except RuntimeError:
                return None
        except Exception as exc:
            logger.info("LLM stance unavailable: %s", exc)
            return None

    parsed = _parse_stance_json(str(text))
    if parsed:
        parsed["method"] = "nli_llm"
    return parsed


def resolve_paper_stance(
    paper: dict[str, Any],
    hypothesis: str,
    hyp_toks: set[str],
    *,
    prefer_nli: bool = True,
    llm_generate: Callable[..., str] | None = None,
) -> dict[str, Any]:
    """Prefer MNLI → LLM → keywords."""
    if prefer_nli:
        mnli = paper_stance_mnli(paper, hypothesis)
        if mnli and not mnli.get("irrelevant"):
            return mnli
        llm = paper_stance_llm(paper, hypothesis, llm_generate=llm_generate)
        if llm and not llm.get("irrelevant"):
            return llm
    return paper_stance_keywords(paper, hyp_toks)


def fuse_dempster_from_papers(
    hypothesis: dict[str, Any],
    papers: list[dict[str, Any]],
    *,
    prefer_nli: bool = True,
    llm_generate: Callable[..., str] | None = None,
) -> dict[str, Any]:
    """Combine paper BBAs with Dempster-Shafer (real Bel/Pl math).

    ``prefer_nli=True`` tries MNLI/LLM first. Set ``C4_DEMPSTER_NLI=0`` to skip
    network LLM attempts in CI (keywords only).
    """
    if os.environ.get("C4_DEMPSTER_NLI", "1") in {"0", "false", "False"}:
        prefer_nli = False
    if llm_generate is not None:
        prefer_nli = True
    from src.bayesian.dempster_shafer import (
        EvidenceSensor,
        FrameOfDiscernment,
        combine_multiple,
    )

    frame = FrameOfDiscernment(["supported", "refuted", "untested"])
    sensor = EvidenceSensor(frame)
    h_text = str(hypothesis.get("text", "") or "")
    hyp_toks = _tokens(h_text)

    if not papers:
        support = float(_count_hits(h_text, _SUPPORT_KW)) + 1.0
        refute = float(_count_hits(h_text, _REFUTE_KW)) or 0.1
        bba = sensor.from_likelihoods(
            {"supported": support, "refuted": refute, "untested": 1.0},
            uncertainty=0.3,
        )
        return {
            "belief_supported": round(bba.belief({"supported"}), 4),
            "plausibility_supported": round(bba.plausibility({"supported"}), 4),
            "focal_elements": len(bba.focal_elements()),
            "papers_used": 0,
            "heuristic": True,
            "method": "hypothesis_keywords",
            "note": "No papers — hypothesis-keyword Dempster fallback",
        }

    bbas = []
    used = 0
    methods: list[str] = []
    for paper in papers[:40]:
        stance = resolve_paper_stance(
            paper,
            h_text,
            hyp_toks,
            prefer_nli=prefer_nli,
            llm_generate=llm_generate,
        )
        if stance.get("irrelevant"):
            continue
        likelihoods = {
            "supported": stance["supported"],
            "refuted": stance["refuted"],
            "untested": stance["untested"],
        }
        bbas.append(sensor.from_likelihoods(likelihoods, uncertainty=0.15))
        used += 1
        methods.append(str(stance.get("method", "keywords")))

    if not bbas:
        return fuse_dempster_from_papers(hypothesis, [], prefer_nli=False)

    combined = combine_multiple(*bbas) if len(bbas) > 1 else bbas[0]
    nli_used = any(m.startswith("nli") for m in methods)
    return {
        "belief_supported": round(combined.belief({"supported"}), 4),
        "plausibility_supported": round(combined.plausibility({"supported"}), 4),
        "focal_elements": len(combined.focal_elements()),
        "papers_used": used,
        "heuristic": not nli_used,
        "method": "nli_dempster" if nli_used else "keyword_overlap_dempster",
        "stance_methods": methods[:20],
        "note": (
            "Dempster-Shafer fused from NLI/LLM paper stance"
            if nli_used
            else "Dempster-Shafer fused from paper keyword stance (NLI unavailable)"
        ),
    }
