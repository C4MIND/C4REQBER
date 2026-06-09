"""c4reqber Guardian — Safety and Security Scanner.

Scans prompts, code, and outputs for:
- Prompt injection attempts
- Credential / API key leaks
- Unsafe AST patterns
- Known attack signatures

Integrates with the PolicyEngine to block dangerous inputs
before they reach the pipeline.
"""
from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ScanResult:
    """Result of a security scan."""

    clean: bool
    threats: list[str] = field(default_factory=list)
    severity: str = "none"  # none, low, medium, high, critical


class Guardian:
    """Safety guardian for the c4reqber system.

    Usage::

        guardian = Guardian()
        result = guardian.scan_prompt(user_input)
        if not result.clean:
            print(f"Threats detected: {result.threats}")
    """

    # Prompt injection patterns
    PROMPT_INJECTION_PATTERNS: list[str] = [
        r"ignore previous instructions",
        r"ignore all (prior|previous) (instructions|rules)",
        r"disregard (the |your )?(system|developer|previous) (prompt|instructions|rules)",
        r"you are now .* instead",
        r"new instructions?:",
        r"system prompt leak",
        r"\{\{.*\}\}",  # Jinja/template injection
        r"<\|im_start\|>",  # ChatML injection
        r"\[INST\]",  # Llama instruction injection
        r"\n\nHuman:",  # Anthropic separator abuse
    ]

    # Credential leak patterns
    CREDENTIAL_PATTERNS: list[str] = [
        r'sk-or-[a-zA-Z0-9_-]{20,}',
        r'sk-[a-zA-Z0-9]{20,}',
        r'nvapi-[a-zA-Z0-9]{20,}',
        r'Bearer\s+[a-zA-Z0-9_-]{20,}',
        r'api[_-]?key\s*[:=]\s*["\'][a-zA-Z0-9_-]{10,}["\']',
        r'password\s*[:=]\s*["\'][^"\']{4,}["\']',
        r'secret\s*[:=]\s*["\'][^"\']{4,}["\']',
        r'AKIA[0-9A-Z]{16}',  # AWS access key
        r'ghp_[a-zA-Z0-9]{36}',  # GitHub PAT
    ]

    # Unsafe AST patterns (none in Python 3.8+ — kept for forward compat)
    UNSAFE_AST_NODES: tuple[type[Any], ...] = ()

    # Dangerous builtins
    DANGEROUS_BUILTINS: set[str] = {
        "eval",
        "exec",
        "compile",
        "__import__",
        "open",  # only dangerous in untrusted code
        "input",  # can be used for prompt injection
    }

    def __init__(self) -> None:
        self._injection_re = [re.compile(p, re.IGNORECASE) for p in self.PROMPT_INJECTION_PATTERNS]
        self._credential_re = [re.compile(p) for p in self.CREDENTIAL_PATTERNS]

    # ------------------------------------------------------------------
    # Prompt scanning
    # ------------------------------------------------------------------

    def scan_prompt(self, text: str) -> ScanResult:
        """Scan user prompt for injection attempts."""
        threats: list[str] = []

        for pattern in self._injection_re:
            if pattern.search(text):
                threats.append(f"Prompt injection pattern: {pattern.pattern[:50]}")

        severity = self._severity_from_count(len(threats))
        return ScanResult(clean=len(threats) == 0, threats=threats, severity=severity)

    # ------------------------------------------------------------------
    # Credential scanning
    # ------------------------------------------------------------------

    def scan_credentials(self, text: str) -> ScanResult:
        """Scan text for leaked credentials or API keys."""
        threats: list[str] = []

        for pattern in self._credential_re:
            matches = pattern.findall(text)
            for match in matches[:3]:  # cap at 3 per pattern
                masked = match[:4] + "***" + match[-4:] if len(match) > 12 else "***"
                threats.append(f"Credential leak: {masked}")

        severity = self._severity_from_count(len(threats))
        return ScanResult(clean=len(threats) == 0, threats=threats, severity=severity)

    # ------------------------------------------------------------------
    # AST validation
    # ------------------------------------------------------------------

    def validate_ast(self, code: str) -> ScanResult:
        """Validate Python code AST for unsafe patterns."""
        threats: list[str] = []

        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return ScanResult(clean=False, threats=[f"Syntax error: {e}"], severity="high")

        for node in ast.walk(tree):
            # Check for dangerous builtins
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id in self.DANGEROUS_BUILTINS:
                    threats.append(f"Dangerous builtin call: {node.func.id}()")
                elif isinstance(node.func, ast.Attribute) and node.func.attr in self.DANGEROUS_BUILTINS:
                    threats.append(f"Dangerous method call: .{node.func.attr}()")

            # Check for unsafe nodes
            if isinstance(node, self.UNSAFE_AST_NODES):
                threats.append(f"Unsafe AST node: {type(node).__name__}")

            # Check for __import__
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == "__import__":
                    threats.append("Dynamic import detected")

        severity = self._severity_from_count(len(threats))
        return ScanResult(clean=len(threats) == 0, threats=threats, severity=severity)

    # ------------------------------------------------------------------
    # Combined scan
    # ------------------------------------------------------------------

    def full_scan(self, text: str, code: str | None = None) -> ScanResult:
        """Run all scanners on input text and optional code."""
        all_threats: list[str] = []

        prompt_result = self.scan_prompt(text)
        all_threats.extend(prompt_result.threats)

        cred_result = self.scan_credentials(text)
        all_threats.extend(cred_result.threats)

        if code:
            ast_result = self.validate_ast(code)
            all_threats.extend(ast_result.threats)

        severities = [prompt_result.severity, cred_result.severity]
        if code:
            severities.append(ast_result.severity)

        max_severity = max(
            severities,
            key=lambda s: {"none": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}.get(s, 0),
        )

        return ScanResult(
            clean=len(all_threats) == 0,
            threats=all_threats,
            severity=max_severity,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _severity_from_count(count: int) -> str:
        if count == 0:
            return "none"
        if count == 1:
            return "low"
        if count <= 3:
            return "medium"
        if count <= 5:
            return "high"
        return "critical"
