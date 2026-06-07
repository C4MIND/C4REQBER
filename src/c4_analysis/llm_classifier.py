"""
C4 LLM Classifier
LLM-powered C4 cognitive state classification.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from src.c4.state import C4State


logger = logging.getLogger(__name__)


C4_CLASSIFICATION_PROMPT = """You are a C4 cognitive classifier. Analyze the following problem statement and classify it into three dimensions of cognitive space.

C4 Framework:
- Time (T): 0=Past, 1=Present, 2=Future
- Scale (S): 0=Concrete, 1=Abstract, 2=Meta
- Agency (A): 0=Self, 1=Group, 2=System

Problem: {problem}

Return ONLY a JSON object in this exact format:
{{
  "time": 0-2,
  "scale": 0-2,
  "agency": 0-2,
  "confidence": 0.0-1.0,
  "reasoning": "brief explanation"
}}

Rules:
- Time: Is the problem about history/review (0), current operations (1), or planning/prediction (2)?
- Scale: Is it about physical implementation (0), conceptual design (1), or framework/methodology (2)?
- Agency: Is it personal (0), team/organization (1), or societal/system-level (2)?"""


class C4LLMClassifier:
    """LLM-powered C4 state classifier."""

    def __init__(self, llm_client: Any=None) -> None:
        self.llm_client = llm_client

    async def classify(self, problem: str) -> tuple[C4State, float, str]:
        """
        Classify problem into C4 state using LLM.

        Returns:
            (C4State, confidence, reasoning)
        """
        if self.llm_client is None:
            raise RuntimeError("LLM client required for C4 classification")

        prompt = C4_CLASSIFICATION_PROMPT.format(problem=problem)

        try:
            response = await self.llm_client.generate(
                prompt=prompt,
                system_prompt="You are a precise cognitive classifier. Respond ONLY with valid JSON.",
                temperature=0.1,
                max_tokens=200,
            )

            # Parse JSON from response
            content = response.content.strip()
            # Extract JSON if wrapped in markdown
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            data = json.loads(content.strip())

            t = max(0, min(2, int(data.get("time", 1))))
            s = max(0, min(2, int(data.get("scale", 1))))
            a = max(0, min(2, int(data.get("agency", 1))))
            confidence = float(data.get("confidence", 0.7))
            reasoning = data.get("reasoning", "LLM classification")

            return C4State(t, s, a), confidence, reasoning

        except Exception as e:
            logger.error("LLM C4 classification failed: %s", e)
            raise


def get_c4_classifier(llm_client: Any = None) -> C4LLMClassifier:
    """Get singleton C4 classifier (backed by DI container)."""
    from src.di.container import get_container
    container = get_container()
    if not container.has("c4_classifier"):
        container.register("c4_classifier", C4LLMClassifier(llm_client))
    classifier = container.resolve("c4_classifier")
    # Lazy-init LLM client if not provided
    if classifier.llm_client is None:
        from src.llm.providers import DeepSeekClient
        classifier.llm_client = DeepSeekClient()
    return classifier
