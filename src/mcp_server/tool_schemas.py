# SPDX-License-Identifier: AGPL-3.0
# Copyright (c) 2026 c4reqber Contributors
from __future__ import annotations


_OBJ = {"type": "object"}
_STR = {"type": "string"}
_INT = {"type": "integer"}
_BOOL = {"type": "boolean"}
_NUM = {"type": "number"}
_ARR_STR = {"type": "array", "items": {"type": "string"}}
_ARR_INT = {"type": "array", "items": {"type": "integer"}}
_ARR_OBJ = {"type": "array", "items": {"type": "object"}}
_ARR = {"type": "array"}

_OUT_COMMON = {
    "status": {
        "type": "string",
        "enum": ["success", "error", "partial", "unavailable", "not_applicable"],
    },
    "errors": _ARR_STR,
    "warnings": _ARR_STR,
    "metadata": _OBJ,
}


def _p(desc, typ=None, default=None, enum=None, items=None):  # type: ignore
    r = {"description": desc}
    if typ is not None:
        r["type"] = typ
    if default is not None:
        r["default"] = default
    if enum is not None:
        r["enum"] = enum
    if items is not None:
        r["items"] = items
    return r


def _ot(data, desc):
    return {"type": "object", "properties": {**_OUT_COMMON, "data": data}, "description": desc}


INPUT_SCHEMAS = {
    "c4_solve": {
        "type": "object",
        "properties": {
            "problem": _p(
                "Problem statement to solve via 7-phase HIL discovery pipeline (A→G)", typ="string"
            ),
            "domain": _p("Scientific domain (default: science)", typ="string", default="science"),
        },
        "required": ["problem"],
    },
    "c4_search": {
        "type": "object",
        "properties": {
            "query": _p("Search query across configured knowledge sources", typ="string"),
            "sources": _p("Optional list of source names", typ="array", items={"type": "string"}),
        },
        "required": ["query"],
        "additionalProperties": False,
    },
    "c4_triz": {
        "type": "object",
        "properties": {
            "improving": _p("TRIZ parameter to improve (1-39)", typ="integer", default=1),
            "worsening": _p("TRIZ parameter that worsens (1-39)", typ="integer", default=2),
            "mode": _p(
                "TRIZ mode: matrix, ariz, standard, sufield",
                typ="string",
                enum=["matrix", "ariz", "standard", "sufield"],
                default="matrix",
            ),
            "problem": _p("Problem description for ARIZ/sufield modes", typ="string", default=""),
        },
    },
    "c4_fingerprint": {
        "type": "object",
        "properties": {
            "problem": _p("Problem text to classify into C4 Z33 cognitive state", typ="string")
        },
        "required": ["problem"],
    },
    "c4_verify": {
        "type": "object",
        "properties": {
            "code": _p("Proof code to verify", typ="string"),
            "language": _p(
                "Proof language: lean4, coq, dafny, agda, z3, hoare, cvc5, tla, alloy, haskell-typecheck, haskell-quickcheck",
                typ="string",
            ),
        },
        "required": ["code"],
    },
    "c4_prove": {
        "type": "object",
        "properties": {
            "hypothesis": _p("Natural-language hypothesis to prove", typ="string"),
            "language": _p(
                "Target proof language: lean4, coq, dafny, agda, z3, hoare, cvc5, tla, alloy, haskell-typecheck, haskell-quickcheck",
                typ="string",
                default="lean4",
            ),
        },
        "required": ["hypothesis"],
    },
    "c4_transfer": {
        "type": "object",
        "properties": {
            "problem": _p("Problem to transfer across domains", typ="string"),
            "source_domain": _p("Source domain name", typ="string"),
            "target_domain": _p("Target domain name", typ="string"),
        },
        "required": ["problem", "source_domain", "target_domain"],
    },
    "c4_simulate": {
        "type": "object",
        "properties": {
            "pattern_id": _p("Simulation pattern ID", typ="string"),
            "hypothesis": _p("Hypothesis dict with parameters", typ="object"),
        },
        "required": ["pattern_id", "hypothesis"],
    },
    "c4_bayesian": {
        "type": "object",
        "properties": {
            "models": {
                "description": "BMA model objects (name, probability, prediction) or legacy name-to-prior mapping",
                "oneOf": [
                    {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["name", "probability", "prediction"],
                        },
                    },
                    {"type": "object", "additionalProperties": {"type": "number"}},
                ],
            },
            "samples": _p(
                "Compatibility metadata for requested sample count", typ="integer", default=1000
            ),
        },
        "required": ["models"],
        "additionalProperties": False,
    },
    "c4_causal": {
        "type": "object",
        "properties": {
            "nodes": _p(
                "SCM nodes with name, parents, and optional metadata",
                typ="array",
                items={"type": "object", "required": ["name"]},
            ),
            "treatment": _p("Treatment variable name", typ="string"),
            "outcome": _p("Outcome variable name", typ="string"),
        },
        "required": ["nodes", "treatment", "outcome"],
        "additionalProperties": False,
    },
    "c4_export": {
        "type": "object",
        "properties": {
            "discovery": _p("Discovery result dict to export", typ="object"),
            "format": _p(
                "Export format: markdown, json, latex, html",
                typ="string",
                enum=["markdown", "json", "latex", "html"],
                default="markdown",
            ),
        },
        "required": ["discovery"],
    },
    "c4_autoresearch": {
        "type": "object",
        "properties": {
            "file": _p("Path to Python training script", typ="string"),
            "metric": _p("Metric name (e.g. val_bpb)", typ="string", default="val_bpb"),
            "max_iter": _p("Max mutations", typ="integer", default=100),
        },
        "required": ["file"],
    },
    "c4_chain": {
        "type": "object",
        "properties": {
            "problem": _p("Problem text for discovery chain", typ="string"),
            "from_state": _p("Source C4 state [T,S,A]", typ="array", items={"type": "integer"}),
            "to_state": _p("Target C4 state [T,S,A]", typ="array", items={"type": "integer"}),
        },
        "required": ["problem"],
    },
    "c4_meta": {
        "type": "object",
        "properties": {
            "reasoning_trace": _p("Reasoning trace to analyze", typ="string"),
            "depth": _p("Reflection depth", typ="integer", default=2),
        },
        "required": ["reasoning_trace"],
    },
    "c4_social": {
        "type": "object",
        "properties": {
            "action": _p("Action: status, publish, preview, drafts, health, post", typ="string"),
            "draft_id": _p("Draft ID for publish/preview/post", typ="string", default=""),
            "platform": _p(
                "Platform for post: twitter, mastodon, reddit, discord, slack",
                typ="string",
                default="",
            ),
        },
        "required": ["action"],
    },
    "blast_solve": {
        "type": "object",
        "properties": {
            "problem": _p("Problem via UniversalSolvePipeline", typ="string"),
            "output_format": _p(
                "Output: auto, prd, code, plan, blueprint, protocol", typ="string", default="auto"
            ),
            "domain": _p("Domain hint", typ="string"),
        },
        "required": ["problem"],
    },
    "blast_turbo": {
        "type": "object",
        "properties": {
            "topic": _p("Research topic for paradigm-shifting proposal", typ="string"),
            "verify_backend": _p("Verification backend", typ="string", default="hybrid"),
            "functors": _p("Enable functor agents", typ="boolean", default=True),
        },
        "required": ["topic"],
    },
    "blast_flash": {
        "type": "object",
        "properties": {
            "question": _p("Question for quick answer", typ="string"),
            "with_sources": _p("Include source citations", typ="boolean", default=False),
            "deep": _p("Run USP cognitive components", typ="boolean", default=False),
        },
        "required": ["question"],
    },
    "blast_turbofactory": {
        "type": "object",
        "properties": {
            "domain": _p("Domain for paradigm factory", typ="string"),
            "scale": _p("Scale: mini, standard, mega, giga", typ="string", default="standard"),
            "max_concurrent": _p("Max concurrent pipelines", typ="integer", default=5),
            "pipeline_mode": _p("Pipeline: solve, turbo, mixed", typ="string", default="mixed"),
        },
        "required": ["domain"],
    },
    "blast_auto": {
        "type": "object",
        "properties": {"query": _p("Query to auto-route to best BLAST mode", typ="string")},
        "required": ["query"],
    },
    "c4_codegen": {
        "type": "object",
        "properties": {
            "specification": _p(
                "Natural language description of the code to generate", typ="string"
            ),
            "language": _p(
                "Target language: python, rust, cpp",
                typ="string",
                enum=["python", "rust", "cpp"],
                default="python",
            ),
            "verify": _p(
                "Whether to verify generated code with formal methods", typ="boolean", default=True
            ),
            "optimization_target": _p(
                "Optimization focus: speed, memory, readability",
                typ="string",
                enum=["speed", "memory", "readability"],
                default="readability",
            ),
        },
        "required": ["specification"],
    },
}

OUTPUT_SCHEMAS = {
    "c4_solve": _ot(
        {
            "type": "object",
            "properties": {
                "topic": _STR,
                "sources": _INT,
                "gaps": _INT,
                "hypotheses": _INT,
                "simulation": _STR,
                "verification": _STR,
                "quality_grade": _STR,
                "quality_score": _NUM,
                "dissertation_path": _STR,
                "warnings": _ARR_STR,
            },
        },
        "Discovery pipeline result with C4Result envelope",
    ),
    "c4_search": _ot(_ARR_OBJ, "Search results across 33 knowledge sources"),
    "c4_triz": _ot(
        {"type": "object", "properties": {"mode": _STR, "principles": _ARR_INT}},
        "TRIZ contradiction resolution result",
    ),
    "c4_fingerprint": _ot(
        {"type": "object", "properties": {"problem": _STR, "state": _ARR_INT, "fingerprint": _STR}},
        "C4 Z3 state fingerprint",
    ),
    "c4_verify": _ot(
        {
            "type": "object",
            "properties": {"valid": _BOOL, "proof": _STR, "language": _STR, "details": _OBJ},
        },
        "Formal proof verification result",
    ),
    "c4_prove": _ot(
        {
            "type": "object",
            "properties": {
                "valid": _BOOL,
                "proof": _STR,
                "language": _STR,
                "iterations": _INT,
                "details": _OBJ,
            },
        },
        "LLM-based formal proof generation result",
    ),
    "c4_transfer": _ot(_OBJ, "Cross-domain isomorphism transfer result"),
    "c4_simulate": _ot(
        {"type": "object", "properties": {"pattern": _STR, "result": _OBJ}},
        "Physics simulation result",
    ),
    "c4_bayesian": _ot(
        {
            "type": "object",
            "properties": {
                "method": _STR,
                "models": _ARR_OBJ,
                "samples": _INT,
                "best_model": _STR,
                "weighted_prediction": _NUM,
                "uncertainty": _NUM,
            },
        },
        "Bayesian model comparison result",
    ),
    "c4_causal": _ot(
        {
            "type": "object",
            "properties": {
                "treatment": _STR,
                "outcome": _STR,
                "identifiable": _BOOL,
                "formula": _STR,
                "adjustment_set": _ARR_STR,
                "reason": _STR,
            },
        },
        "Causal identification via do-calculus",
    ),
    "c4_export": _ot(
        {"type": "object", "properties": {"status": _STR, "format": _STR, "content": _STR}},
        "Exported discovery document",
    ),
    "c4_autoresearch": _ot(
        {
            "type": "object",
            "properties": {
                "status": _STR,
                "best_metric": _NUM,
                "best_iteration": _INT,
                "total_iterations": _INT,
                "total_duration_seconds": _NUM,
                "improvement_trace": _ARR_OBJ,
            },
        },
        "Autoresearch training loop result",
    ),
    "c4_chain": _ot(
        {
            "type": "object",
            "properties": {
                "from_state": _ARR,
                "to_state": _ARR,
                "path": _ARR,
                "step_count": _INT,
                "theorem": _STR,
            },
        },
        "C4 discovery chain (Theorem 11)",
    ),
    "c4_meta": _ot(
        {
            "type": "object",
            "properties": {
                "state": _STR,
                "target_meta_state": _STR,
                "hamming_distance": _INT,
                "operators": _ARR,
                "reflections": _ARR,
                "depth": _INT,
            },
        },
        "Meta-cognitive reflection result",
    ),
    "c4_social": _ot(
        {
            "type": "object",
            "properties": {
                "action": _STR,
                "draft_id": _STR,
                "platform": _STR,
                "status": _STR,
                "drafts": _ARR,
            },
        },
        "Social publishing result",
    ),
    "blast_solve": _ot(
        {
            "type": "object",
            "properties": {
                "mode": _STR,
                "problem": _STR,
                "final_solution": _STR,
                "confidence": _NUM,
                "sources": _INT,
                "gaps": _INT,
                "quality_report": _OBJ,
                "c4_path": _ARR,
                "plugin_selection": _ARR,
                "cost_usd": _NUM,
            },
        },
        "BLAST solve mode strategic artifact result",
    ),
    "blast_turbo": _ot(
        {
            "type": "object",
            "properties": {
                "mode": _STR,
                "topic": _STR,
                "sources": _INT,
                "gaps": _INT,
                "hypotheses": _INT,
                "simulation": _STR,
                "verification": _STR,
                "quality_grade": _STR,
                "quality_score": _NUM,
                "quality_gates": _ARR,
                "dissertation_path": _STR,
            },
        },
        "BLAST turbo mode paradigm-shifting result",
    ),
    "blast_flash": _ot(
        {
            "type": "object",
            "properties": {"mode": _STR, "answer": _STR, "sources": _ARR_OBJ, "usp_context": _OBJ},
        },
        "BLAST flash mode quick answer result",
    ),
    "blast_turbofactory": _ot(
        {
            "type": "object",
            "properties": {
                "mode": _STR,
                "domain": _STR,
                "scale": _STR,
                "pipeline_mode": _STR,
                "pipelines": _INT,
                "successful": _INT,
                "failed": _INT,
                "total_hypotheses": _INT,
                "avg_quality_score": _NUM,
                "results": _ARR,
            },
        },
        "BLAST turbofactory parallel pipeline result",
    ),
    "blast_auto": _ot(
        {
            "type": "object",
            "properties": {"auto_routed": _BOOL, "selected_mode": _STR, "mode_description": _STR},
        },
        "Auto-routed BLAST mode result",
    ),
    "c4_codegen": _ot(
        {
            "type": "object",
            "properties": {
                "code": _STR,
                "verified": _BOOL,
                "backend_used": _STR,
                "proof_code": _STR,
                "errors": _ARR_STR,
                "suggestions": _ARR_STR,
            },
        },
        "Code generation with optional formal verification",
    ),
}
