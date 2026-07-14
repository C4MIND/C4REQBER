"""Information Theory Plugin — Shannon entropy, mutual information, KL divergence.

Does NOT duplicate: Hash (fingerprinting), Text Distance (token Jaccard), C4 engine (state space).
UNIQUE: Information-theoretic metrics for cognitive state analysis and paradigm shift detection.
"""
from __future__ import annotations

import math
from collections import Counter
from typing import Any


def shannon_entropy(values: list[Any], base: float = 2.0) -> dict[str, Any]:
    """Shannon entropy H(X) = -Σ p(x) log p(x)."""
    n = len(values)
    if n == 0:
        return {"entropy": 0.0, "normalized": 0.0, "unique_values": 0, "n": 0}

    counts = Counter(values)
    total = sum(counts.values())
    entropy = 0.0
    for count in counts.values():
        if count > 0:
            p = count / total
            entropy -= p * math.log(p) / math.log(base)

    max_entropy = math.log(len(counts)) / math.log(base) if len(counts) > 1 else 1.0
    normalized = entropy / max_entropy if max_entropy > 0 else 0.0

    return {
        "entropy": round(entropy, 6),
        "normalized": round(normalized, 6),
        "unique_values": len(counts),
        "n": n,
        "base": base,
    }


def mutual_information(x_vals: list[Any], y_vals: list[Any], base: float = 2.0) -> dict[str, Any]:
    """Mutual information I(X;Y) = H(X) + H(Y) - H(X,Y)."""
    if len(x_vals) != len(y_vals) or len(x_vals) == 0:
        return {"error": "Vectors must be same length and non-empty"}

    joint = Counter(zip(x_vals, y_vals, strict=False))
    x_counts = Counter(x_vals)
    y_counts = Counter(y_vals)
    n = len(x_vals)

    mi = 0.0
    for (x, y), joint_count in joint.items():
        p_xy = joint_count / n
        p_x = x_counts[x] / n
        p_y = y_counts[y] / n
        if p_xy > 0 and p_x > 0 and p_y > 0:
            mi += p_xy * math.log(p_xy / (p_x * p_y)) / math.log(base)

    hx = shannon_entropy(x_vals, base)["entropy"]
    hy = shannon_entropy(y_vals, base)["entropy"]
    norm = mi / math.sqrt(hx * hy) if hx > 0 and hy > 0 else 0.0

    return {
        "mutual_information": round(mi, 6),
        "normalized": round(norm, 6),
        "hx": round(hx, 6),
        "hy": round(hy, 6),
        "n": n,
    }


def kl_divergence(p_dist: dict[Any, float], q_dist: dict[Any, float], base: float = 2.0) -> dict[str, Any]:
    """Kullback-Leibler divergence D_KL(P||Q)."""
    if not p_dist or not q_dist:
        return {"error": "Distributions required"}

    epsilon = 1e-10
    kl = 0.0
    all_keys = set(p_dist.keys()) | set(q_dist.keys())

    for k in all_keys:
        p = p_dist.get(k, epsilon)
        q = q_dist.get(k, epsilon)
        if p > epsilon and q > epsilon:
            kl += p * math.log(p / q) / math.log(base)

    return {"kl_divergence": round(kl, 6), "base": base}


def complexity_metric(text: str) -> dict[str, Any]:
    """Combined information-theoretic complexity of text.

    Metrics: entropy (character level), entropy (word level),
    compression ratio estimate, vocabulary richness.
    """
    if not text.strip():
        return {"error": "Empty text"}

    chars = list(text)
    words = text.split()
    char_entropy = shannon_entropy(chars)
    word_entropy = shannon_entropy(words)

    # Compression ratio estimate: entropy * length / (max theoretical)
    n = len(text)
    unique_chars = char_entropy["unique_values"]
    compression_ratio = char_entropy["entropy"] * n / (n * math.log(unique_chars, 2)) if unique_chars > 1 and n > 0 else 1.0

    # Vocabulary richness (type-token ratio)
    unique_words = word_entropy["unique_values"]
    ttr = unique_words / len(words) if words else 0.0

    complexity = char_entropy["normalized"] * 0.3 + (1 - compression_ratio) * 0.3 + word_entropy["normalized"] * 0.2 + ttr * 0.2

    return {
        "complexity_score": round(complexity, 4),
        "char_entropy": char_entropy["entropy"],
        "word_entropy": word_entropy["entropy"],
        "compression_ratio": round(compression_ratio, 4),
        "type_token_ratio": round(ttr, 4),
        "chars": n,
        "words": len(words),
    }


# ── Pipeline interface ─────────────────────────────────────────────────

def execute(problem: str = "", hypothesis_text: str = "", **kwargs: Any) -> dict[str, Any]:
    """Run information-theoretic analysis.

    Auto-selects analysis type based on available kwargs.
    If --depth flag is set, runs complexity_metric on hypothesis_text.
    """
    metric = kwargs.get("metric", "complexity")

    try:
        if metric == "entropy":
            return shannon_entropy(kwargs.get("values", list(hypothesis_text)))
        elif metric == "mutual_info":
            return mutual_information(kwargs.get("x", []), kwargs.get("y", []))
        elif metric == "kl":
            return kl_divergence(kwargs.get("p", {}), kwargs.get("q", {}))
        else:
            # Default: analyze hypothesis text complexity
            return complexity_metric(hypothesis_text or problem)
    except Exception as e:
        return {"error": str(e), "metric": metric}
