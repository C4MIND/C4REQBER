from __future__ import annotations


"""Multi-Provider Reasoner Client — model routing for formal proofs.

Priority chain:
1. DeepSeek direct (deepseek-reasoner)
2. OpenRouter (google/gemini-2.5-pro, meta-llama/llama-4-maverick)
3. Local (lmstudio/qwq-32b, ollama/deepseek-r1:32b)

Uses zero temperature for deterministic proof generation.
"""

import logging
import os
from dataclasses import dataclass

import httpx


logger = logging.getLogger(__name__)


@dataclass
class ReasonerProvider:
    """Configuration for a reasoner model provider."""

    name: str
    base_url: str
    model: str
    api_key_env: str
    timeout: float = 60.0
    priority: int = 1  # Lower = tried first
    max_tokens: int = 4000


# Default provider chain — edit via config
DEFAULT_PROVIDERS = [
    ReasonerProvider(
        name="deepseek-direct",
        base_url="https://api.deepseek.com/v1/chat/completions",
        model="deepseek-reasoner",
        api_key_env="DEEPSEEK_API_KEY",
        priority=1,
    ),
    ReasonerProvider(
        name="openrouter-gemini",
        base_url="https://openrouter.ai/api/v1/chat/completions",
        model="google/gemini-2.5-pro-preview-03-25",
        api_key_env="OPENROUTER_API_KEY",
        priority=2,
    ),
    ReasonerProvider(
        name="openrouter-llama",
        base_url="https://openrouter.ai/api/v1/chat/completions",
        model="meta-llama/llama-4-maverick",
        api_key_env="OPENROUTER_API_KEY",
        priority=3,
    ),
    ReasonerProvider(
        name="local-lmstudio",
        base_url="http://localhost:1234/v1/chat/completions",
        model="qwq-32b",
        api_key_env="LMSTUDIO_API_KEY",
        timeout=120.0,
        priority=4,
    ),
    ReasonerProvider(
        name="local-ollama",
        base_url="http://localhost:11434/v1/chat/completions",
        model="deepseek-r1:32b",
        api_key_env="",  # Ollama needs no key
        timeout=120.0,
        priority=5,
    ),
]


class MultiProviderReasonerClient:
    """Reasoner client with provider routing."""

    def __init__(self, providers: list[ReasonerProvider] | None = None) -> None:
        self.providers = providers or self._load_providers()
        self._client = httpx.AsyncClient()

    def _load_providers(self) -> list[ReasonerProvider]:
        """Load providers from config, filter unavailable."""
        available = []
        for p in DEFAULT_PROVIDERS:
            key = os.environ.get(p.api_key_env, "")
            if p.api_key_env and not key:
                logger.debug("Skipping %s: no API key (%s)", p.name, p.api_key_env)
                continue
            # Check local endpoints
            if "localhost" in p.base_url and not self._check_local(p.base_url):
                logger.debug("Skipping %s: local endpoint not available", p.name)
                continue
            available.append(p)

        if not available:
            logger.warning("No reasoner providers available! Set DEEPSEEK_API_KEY or OPENROUTER_API_KEY")
        return sorted(available, key=lambda x: x.priority)

    def _check_local(self, url: str) -> bool:
        """Quick check if local endpoint is up."""
        try:
            httpx.get(url.replace("/chat/completions", "/models"), timeout=2.0)
            return True
        except (ConnectionError, TimeoutError, RuntimeError):
            return False

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.0,
        max_tokens: int | None = None,
    ) -> str:
        """Generate with provider routing.

        Tries each provider in priority order until one succeeds.
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        for provider in self.providers:
            try:
                logger.info("Trying provider: %s (%s)", provider.name, provider.model)
                result = await self._call_provider(provider, messages, temperature, max_tokens)
                if result and not result.startswith("[Error"):
                    return self._strip_code_blocks(result)
            except Exception as e:
                logger.warning("Provider %s failed: %s", provider.name, e)
                continue

        raise RuntimeError("All reasoner providers failed")

    async def _call_provider(
        self,
        provider: ReasonerProvider,
        messages: list[dict],
        temperature: float,
        max_tokens: int | None,
    ) -> str:
        """Call a single provider."""
        headers = {"Content-Type": "application/json"}
        key = os.environ.get(provider.api_key_env, "")
        if key:
            headers["Authorization"] = f"Bearer {key}"
        # OpenRouter needs extra header
        if "openrouter" in provider.base_url:
            headers["HTTP-Referer"] = "https://c4reqber.ai"
            headers["X-Title"] = "c4reqber"

        resp = await self._client.post(
            provider.base_url,
            headers=headers,
            json={
                "model": provider.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens or provider.max_tokens,
            },
            timeout=provider.timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]

    def _strip_code_blocks(self, text: str) -> str:
        """Remove markdown code block wrappers."""
        lines = text.split("\n")
        result = []
        in_block = False
        for line in lines:
            if line.strip().startswith("```"):
                in_block = not in_block
                continue
            result.append(line)
        return "\n".join(result).strip()

    async def generate_proof(
        self,
        claim: str,
        backend: str,
        domain: str = "general",
        example: str | None = None,
    ) -> str:
        """Generate formal proof with optimized prompt."""
        system = f"""You are an expert {backend} proof engineer.
Generate COMPLETE, COMPILABLE {backend} code.
NEVER use placeholders (sorry, admit, {{! !}}).
Use exact {backend} syntax."""

        prompt = self._build_proof_prompt(claim, backend, domain, example)
        return await self.generate(prompt, system, temperature=0.0, max_tokens=4000)

    async def fix_error(
        self,
        code: str,
        error: str,
        backend: str,
    ) -> str:
        """Fix compilation error with context."""
        prompt = f"""Fix this {backend} compilation error:

```{backend}
{code}
```

COMPILER ERROR:
{error}

Rules:
1. Identify the exact line causing the error
2. Fix ONLY the error, don't change working code
3. Return COMPLETE corrected code
4. NEVER add placeholders (sorry, admit)

Return corrected code ONLY:"""

        return await self.generate(prompt, temperature=0.0, max_tokens=4000)

    def _build_proof_prompt(
        self,
        claim: str,
        backend: str,
        domain: str,
        example: str | None,
    ) -> str:
        """Build token-efficient proof prompt."""
        backend_rules = {
            "lean4": """Lean 4 rules:
- Use "import Mathlib" for math, "import Std" for basic
- NEVER use "sorry" — provide actual tactics
- Use: intro, apply, rw, simp, linarith, exact, induction, cases
- Theorem format: theorem name : type := by tactics""",
            "coq": """Coq rules:
- Use: Theorem, Proof, Qed, induction, apply, auto, tauto
- NEVER use "Admitted"
- End with "Qed." """,
            "dafny": """Dafny rules:
- Use: method, ensures, requires, invariant, decreases
- Include pre/post conditions
- Use while loops with invariants""",
            "agda": """Agda rules:
- Use: data, record, open, module, where
- Use Unicode: ∀, →, ≡, Σ
- Provide pattern matching with cases""",
            "hoare": """Hoare logic rules:
- Use: precondition, postcondition, invariant
- Format: {P} C {Q}
- Include loop invariants""",
        }

        parts = [
            f"Generate a {backend} proof for this claim:",
            f'"{claim}"',
            f"\nDomain: {domain}",
            f"\n{backend_rules.get(backend, '')}",
        ]

        if example:
            parts.append(f"\nWORKING EXAMPLE:\n{example}")

        parts.append("\nReturn ONLY the complete code. No explanations.")
        return "\n".join(parts)


# Backward compatibility alias
DeepSeekReasonerClient = MultiProviderReasonerClient
