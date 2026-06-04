"""Validation utilities for C44TCDI.

Provides validation functions for hypotheses, proofs, and simulation configs
to be used in API endpoints and pipeline steps.
"""

from __future__ import annotations

import logging
import re
from typing import Any


logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Hypothesis validation
# ---------------------------------------------------------------------------

def validate_hypothesis(hypothesis: dict[str, Any]) -> dict[str, Any]:
    """Validate a hypothesis dictionary.

    Checks:
    - Has required fields (text or structured)
    - Text is non-empty and reasonable length
    - Is falsifiable (has testable claims)
    - Has valid source attribution

    Args:
        hypothesis: Hypothesis dictionary to validate

    Returns:
        Dict with 'valid' (bool), 'errors' (list), 'warnings' (list)
    """
    errors: list[str] = []
    warnings: list[str] = []


    # Check for text or structured format
    text = hypothesis.get("text", "")
    structured = hypothesis.get("structured", False)

    if not text and not structured:
        errors.append("Hypothesis must have 'text' or be 'structured'")
    elif text:
        # Validate text

            # Check for testable claims (basic heuristic)
            has_prediction = any(
                kw in text.lower()
                for kw in ["predict", "expect", "will", "should", "measurement", "measure"]
            )
            if not has_prediction:
                warnings.append("Hypothesis may not be falsifiable - no predictive language found")

            # Check for specificity
            if text.count(" ") < 5:
                warnings.append("Hypothesis may be too vague (less than 5 words)")

    # Validate source
    source = hypothesis.get("source", "")
    if source and not isinstance(source, str):
        errors.append("Hypothesis 'source' must be a string")

    # Validate confidence if present
    confidence = hypothesis.get("confidence")
    if confidence is not None:
        if isinstance(confidence, (int, float)):
            if not 0 <= confidence <= 1:
                warnings.append("Confidence should be between 0 and 1")
        else:
            errors.append("Hypothesis 'confidence' must be a number")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
    }


def validate_hypothesis_text(text: str) -> dict[str, Any]:
    """Validate hypothesis text directly.

    Args:
        text: Hypothesis text to validate

    Returns:
        Dict with 'valid' (bool), 'errors' (list), 'warnings' (list)
    """

    errors: list[str] = []
    warnings: list[str] = []

    if len(text.strip()) < 10:
        errors.append("Hypothesis text is too short (min 10 chars)")
    elif len(text) > 10000:
        warnings.append("Hypothesis text is very long (>10000 chars)")

    # Check for testable claims
    has_prediction = any(
        kw in text.lower()
        for kw in ["predict", "expect", "will", "should", "measurement", "measure"]
    )
    if not has_prediction:
        warnings.append("Hypothesis may not be falsifiable - no predictive language found")

    # Check for specificity
    if text.count(" ") < 5:
        warnings.append("Hypothesis may be too vague (less than 5 words)")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
    }


# ---------------------------------------------------------------------------
# Proof validation
# ---------------------------------------------------------------------------

def validate_proof(proof: dict[str, Any]) -> dict[str, Any]:
    """Validate a proof dictionary.

    Checks:
    - Has required fields (language, proof)
    - Proof code is non-empty
    - Language is supported
    - Generated flag is boolean

    Args:
        proof: Proof dictionary to validate

    Returns:
        Dict with 'valid' (bool), 'errors' (list), 'warnings' (list)
    """
    errors: list[str] = []
    warnings: list[str] = []


    # Check required fields
    language = proof.get("language", "")
    proof_code = proof.get("proof", "")

    if not language:
        errors.append("Proof must have 'language' field")
    elif language not in ("lean4", "coq", "dafny", "hoare", "unknown"):
        warnings.append(f"Unsupported proof language: {language}")

    if not proof_code:
        errors.append("Proof must have 'proof' field with code")

    # Check generated flag
    generated = proof.get("generated", None)
    if generated is not None and not isinstance(generated, bool):
        warnings.append("Proof 'generated' should be a boolean")

    # Validate proof syntax basics (if language is known)
    if isinstance(proof_code, str) and proof_code and language == "lean4":
        if not _validate_lean4_basic(proof_code):
            warnings.append("Proof may have Lean4 syntax issues")
    elif isinstance(proof_code, str) and proof_code and language == "coq":
        if not _validate_coq_basic(proof_code):
            warnings.append("Proof may have Coq syntax issues")
    elif isinstance(proof_code, str) and proof_code and language == "dafny":
        if not _validate_dafny_basic(proof_code):
            warnings.append("Proof may have Dafny syntax issues")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
    }


def _validate_lean4_basic(code: str) -> bool:
    """Basic Lean 4 syntax validation."""
    # Check for theorem/def keyword
    if not re.search(r"\b(theorem|lemma|def|example)\b", code):
        return False
    # Check for proof terminator
    if not re.search(r"\b(Qed\.|end\s+\w+|by\s+.+)$", code, re.MULTILINE):
        return False
    return True


def _validate_coq_basic(code: str) -> bool:
    """Basic Coq syntax validation."""
    if not re.search(r"\b(Theorem|Lemma|Definition|Goal)\b", code):
        return False
    if "Qed." not in code and "Defined." not in code:
        return False
    return True


def _validate_dafny_basic(code: str) -> bool:
    """Basic Dafny syntax validation."""
    if not re.search(r"\b(method|function|lemma)\b", code):
        return False
    if "{" not in code or "}" not in code:
        return False
    return True


# ---------------------------------------------------------------------------
# Simulation config validation
# ---------------------------------------------------------------------------

def validate_simulation_config(config: dict[str, Any]) -> dict[str, Any]:
    """Validate a simulation configuration dictionary.

    Checks:
    - Has required fields (domain, pattern_id or engine)
    - Duration and dt are valid
    - Domain is supported
    - Numeric parameters are valid

    Args:
        config: Simulation config dictionary to validate

    Returns:
        Dict with 'valid' (bool), 'errors' (list), 'warnings' (list)
    """
    errors: list[str] = []
    warnings: list[str] = []


    # Required fields
    domain = config.get("domain", "")
    if not domain:
        errors.append("Simulation config must have 'domain' field")

    # Optional but validated fields
    duration = config.get("duration")
    if duration is not None:
        if not isinstance(duration, (int, float)):
            errors.append("'duration' must be a number")
        elif duration <= 0:
            errors.append("'duration' must be positive")
        elif duration > 1000:
            warnings.append("'duration' is very large (>1000)")

    dt = config.get("dt")
    if dt is not None:
        if not isinstance(dt, (int, float)):
            errors.append("'dt' must be a number")
        elif dt <= 0:
            errors.append("'dt' must be positive")
        elif dt > 1:
            warnings.append("'dt' is large (>1), may cause instability")
        if duration and dt and dt >= duration:
            errors.append("'dt' must be less than 'duration'")

    # Pattern ID or engine
    pattern_id = config.get("pattern_id")
    engine = config.get("engine")
    if not pattern_id and not engine:
        warnings.append("No 'pattern_id' or 'engine' specified")

    # Hypothesis text
    hypothesis_text = config.get("hypothesis", "")
    if hypothesis_text and not isinstance(hypothesis_text, str):
        errors.append("'hypothesis' must be a string")

    # Supported domains
    supported_domains = [
        "physics", "chemistry", "biology", "engineering",
        "materials", "electronics", "energy", "medicine",
        "economics", "software", "general"
    ]
    if domain and domain not in supported_domains:
        warnings.append(f"Domain '{domain}' may not be supported")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
    }


def validate_simulation_result(result: dict[str, Any]) -> dict[str, Any]:
    """Validate a simulation result dictionary.

    Args:
        result: Simulation result to validate

    Returns:
        Dict with 'valid' (bool), 'errors' (list), 'warnings' (list)
    """
    errors: list[str] = []
    warnings: list[str] = []


    # Check status
    status = result.get("status", "")
    if status == "error":
        errors.append(f"Simulation failed: {result.get('error', 'Unknown error')}")
    elif status == "timeout":
        warnings.append("Simulation timed out")

    # Validate numeric fields if present
    time_steps = result.get("time_steps")
    if time_steps is not None:
        if not isinstance(time_steps, int):
            errors.append("'time_steps' must be an integer")
        elif time_steps < 0:
            errors.append("'time_steps' must be non-negative")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
    }


# ---------------------------------------------------------------------------
# Generic validation helper
# ---------------------------------------------------------------------------

def validate_required_fields(
    data: dict[str, Any],
    required_fields: list[str],
    field_types: dict[str, type] | None = None,
) -> list[str]:
    """Validate that required fields are present and of correct type.

    Args:
        data: Dictionary to validate
        required_fields: List of required field names
        field_types: Optional dict mapping field names to expected types

    Returns:
        List of error messages (empty if valid)
    """
    errors: list[str] = []

    for field in required_fields:
        if field not in data:
            errors.append(f"Missing required field: {field}")
        elif field_types and field in field_types:
            expected_type = field_types[field]
            if not isinstance(data[field], expected_type):
                errors.append(
                    f"Field '{field}' must be of type {expected_type.__name__}"
                )

    return errors
