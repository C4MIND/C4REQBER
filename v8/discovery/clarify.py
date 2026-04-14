"""
Clarification Engine for Discovery Lab V2
Generates clarifying questions based on initial research query
"""

import json
import random
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from enum import Enum


class QuestionType(str, Enum):
    SINGLE_CHOICE = "single_choice"
    MULTI_CHOICE = "multi_choice"
    TEXT = "text"


class ClarificationOption(BaseModel):
    value: str
    ru: str
    en: str


class ClarificationQuestion(BaseModel):
    id: str
    question: Dict[str, str]  # {ru: "...", en: "..."}
    type: QuestionType
    options: Optional[List[ClarificationOption]] = None
    required: bool = True


class ClarificationAnswer(BaseModel):
    question_id: str
    answer: Any  # str for text/single, List[str] for multi


class RefinedQuery(BaseModel):
    original_query: str
    refined_query: str
    focus_areas: List[str]
    scope: str  # "broad", "moderate", "narrow"
    depth: str  # "shallow", "medium", "deep"
    domains: List[str]


class ClarificationEngine:
    """
    Generates clarifying questions to better understand user research intent.
    Uses LLM for dynamic generation with fallback to templates.
    """

    # Default question templates as fallback
    DEFAULT_QUESTIONS = [
        {
            "id": "scope",
            "question": {
                "ru": "Какой масштаб исследования вас интересует?",
                "en": "What scope of research are you interested in?",
            },
            "type": "single_choice",
            "options": [
                {
                    "value": "broad",
                    "ru": "Широкий обзор области (birds-eye view)",
                    "en": "Broad overview (birds-eye view)",
                },
                {
                    "value": "moderate",
                    "ru": "Умеренная глубина с ключевыми аспектами",
                    "en": "Moderate depth with key aspects",
                },
                {
                    "value": "narrow",
                    "ru": "Глубокое погружение в конкретный аспект",
                    "en": "Deep dive into specific aspect",
                },
            ],
            "required": True,
        },
        {
            "id": "focus",
            "question": {
                "ru": "Какой аспект темы наиболее важен для вас?",
                "en": "Which aspect of the topic is most important to you?",
            },
            "type": "multi_choice",
            "options": [
                {
                    "value": "theoretical",
                    "ru": "Теоретические основы",
                    "en": "Theoretical foundations",
                },
                {
                    "value": "practical",
                    "ru": "Практическое применение",
                    "en": "Practical applications",
                },
                {
                    "value": "history",
                    "ru": "Историческое развитие",
                    "en": "Historical development",
                },
                {
                    "value": "future",
                    "ru": "Будущие перспективы",
                    "en": "Future perspectives",
                },
                {
                    "value": "controversies",
                    "ru": "Контроверсии и дебаты",
                    "en": "Controversies and debates",
                },
            ],
            "required": False,
        },
        {
            "id": "domains",
            "question": {
                "ru": "Какие смежные области могут быть релевантны?",
                "en": "Which related domains might be relevant?",
            },
            "type": "multi_choice",
            "options": [
                {"value": "physics", "ru": "Физика", "en": "Physics"},
                {"value": "biology", "ru": "Биология", "en": "Biology"},
                {"value": "psychology", "ru": "Психология", "en": "Psychology"},
                {"value": "economics", "ru": "Экономика", "en": "Economics"},
                {
                    "value": "computer_science",
                    "ru": "Computer Science",
                    "en": "Computer Science",
                },
                {"value": "philosophy", "ru": "Философия", "en": "Philosophy"},
                {"value": "mathematics", "ru": "Математика", "en": "Mathematics"},
                {"value": "neuroscience", "ru": "Нейронаука", "en": "Neuroscience"},
            ],
            "required": False,
        },
        {
            "id": "goal",
            "question": {
                "ru": "Какова ваша конечная цель?",
                "en": "What is your ultimate goal?",
            },
            "type": "single_choice",
            "options": [
                {
                    "value": "novel_insight",
                    "ru": "Найти новое понимание / инсайт",
                    "en": "Find novel insight / understanding",
                },
                {
                    "value": "problem_solving",
                    "ru": "Решить конкретную проблему",
                    "en": "Solve specific problem",
                },
                {
                    "value": "knowledge_gap",
                    "ru": "Найти пробелы в знаниях",
                    "en": "Identify knowledge gaps",
                },
                {
                    "value": "cross_domain",
                    "ru": "Найти связи между областями",
                    "en": "Find cross-domain connections",
                },
                {
                    "value": "education",
                    "ru": "Образовательные цели",
                    "en": "Educational purposes",
                },
            ],
            "required": True,
        },
        {
            "id": "constraints",
            "question": {
                "ru": "Есть ли что-то, что следует исключить из рассмотрения?",
                "en": "Is there anything that should be excluded from consideration?",
            },
            "type": "text",
            "required": False,
        },
    ]

    def __init__(self, llm_client=None):
        self.llm_client = llm_client

    async def generate_questions(
        self, query: str, locale: str = "ru", num_questions: int = 5
    ) -> List[ClarificationQuestion]:
        """
        Generate clarifying questions based on the initial query.

        Args:
            query: User's initial research query
            locale: 'ru' or 'en'
            num_questions: Number of questions to generate (3-5)

        Returns:
            List of ClarificationQuestion objects
        """
        num_questions = max(1, min(20, num_questions))
        if self.llm_client:
            try:
                return await self._generate_with_llm(query, locale, num_questions)
            except Exception as e:
                print(f"LLM generation failed, using fallback: {e}")
                return self._generate_fallback(query, locale, num_questions)
        else:
            return self._generate_fallback(query, locale, num_questions)

    async def _generate_with_llm(
        self, query: str, locale: str, num_questions: int
    ) -> List[ClarificationQuestion]:
        """Use LLM to generate contextual questions"""

        prompt = f"""You are a research assistant helping to clarify the user's research intent.

User query: "{query}"
Target language: {locale}

Generate {num_questions} clarifying questions that will help conduct a precise research.

Requirements:
1. Questions should be relevant to the specific query
2. Mix of question types: single_choice, multi_choice, and text
3. At least one question about scope (broad/moderate/narrow)
4. At least one question about focus areas
5. Include domain selection if cross-domain research makes sense

Response format (JSON):
{{
  "questions": [
    {{
      "id": "unique_id",
      "question": {{"ru": "...", "en": "..."}},
      "type": "single_choice|multi_choice|text",
      "options": [{{"value": "...", "ru": "...", "en": "..."}}],  // for choice types
      "required": true/false
    }}
  ]
}}

Make questions specific to the topic. For "{query}", what would you need to know?"""

        response = await self.llm_client.generate(prompt)

        try:
            data = json.loads(response)
            questions = []
            for q_data in data.get("questions", []):
                question = ClarificationQuestion(
                    id=q_data["id"],
                    question=q_data["question"],
                    type=QuestionType(q_data["type"]),
                    options=[
                        ClarificationOption(**opt) for opt in q_data.get("options", [])
                    ]
                    if q_data.get("options")
                    else None,
                    required=q_data.get("required", True),
                )
                questions.append(question)
            return questions[:num_questions]
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"Failed to parse LLM response: {e}")
            raise

    def _generate_fallback(
        self, query: str, locale: str, num_questions: int
    ) -> List[ClarificationQuestion]:
        """Use template-based fallback questions"""

        # Select relevant subset of default questions
        # Prioritize: scope (always), goal (always), then focus/domains/constraints

        selected = []

        # Always include scope and goal
        scope_q = next(q for q in self.DEFAULT_QUESTIONS if q["id"] == "scope")
        goal_q = next(q for q in self.DEFAULT_QUESTIONS if q["id"] == "goal")

        selected.append(ClarificationQuestion(**scope_q))
        selected.append(ClarificationQuestion(**goal_q))

        # Add 1-3 more based on query analysis
        remaining = [
            q for q in self.DEFAULT_QUESTIONS if q["id"] not in ["scope", "goal"]
        ]

        # Analyze query for keywords to prioritize questions
        query_lower = query.lower()

        if any(
            word in query_lower
            for word in ["cross", "intersection", "between", "styk", "стык"]
        ):
            # Prioritize domains question for cross-domain queries
            domains_q = next(q for q in remaining if q["id"] == "domains")
            selected.append(ClarificationQuestion(**domains_q))
        elif any(
            word in query_lower
            for word in ["theory", "theoretical", "теория", "теоретический"]
        ):
            # Prioritize focus question for theoretical queries
            focus_q = next(q for q in remaining if q["id"] == "focus")
            selected.append(ClarificationQuestion(**focus_q))
        else:
            # Randomly choose between focus and domains
            random.shuffle(remaining)
            selected.append(ClarificationQuestion(**remaining[0]))

        # Always add constraints as optional
        constraints_q = next(
            q for q in self.DEFAULT_QUESTIONS if q["id"] == "constraints"
        )
        selected.append(ClarificationQuestion(**constraints_q))

        return selected[:num_questions]

    def refine_query(
        self,
        original_query: str,
        answers: List[ClarificationAnswer],
        locale: str = "ru",
    ) -> RefinedQuery:
        """
        Create a refined query based on original query and clarification answers.

        Args:
            original_query: Initial user query
            answers: List of answers to clarification questions
            locale: Language

        Returns:
            RefinedQuery object
        """
        # Parse answers into structured data
        answer_map = {a.question_id: a.answer for a in answers}

        # Determine scope
        scope = answer_map.get("scope", "moderate")
        if isinstance(scope, list):
            scope = scope[0] if scope else "moderate"

        # Determine depth based on scope
        depth_map = {"broad": "shallow", "moderate": "medium", "narrow": "deep"}
        depth = depth_map.get(scope, "medium")

        # Extract focus areas
        focus = answer_map.get("focus", [])
        if isinstance(focus, str):
            focus = [focus]

        # Extract domains
        domains = answer_map.get("domains", [])
        if isinstance(domains, str):
            domains = [domains]

        # Build refined query
        focus_str = ", ".join(focus) if focus else "general"
        domains_str = ", ".join(domains) if domains else "relevant domains"

        if locale == "ru":
            refined = (
                f"{original_query} "
                f"[Масштаб: {scope}, Фокус: {focus_str}, "
                f"Области: {domains_str}]"
            )
        else:
            refined = (
                f"{original_query} "
                f"[Scope: {scope}, Focus: {focus_str}, "
                f"Domains: {domains_str}]"
            )

        return RefinedQuery(
            original_query=original_query,
            refined_query=refined,
            focus_areas=focus,
            scope=scope,
            depth=depth,
            domains=domains,
        )


# Singleton instance
_clarification_engine: Optional[ClarificationEngine] = None


def get_clarification_engine(llm_client=None) -> ClarificationEngine:
    """Get or create singleton ClarificationEngine instance"""
    global _clarification_engine
    if _clarification_engine is None:
        _clarification_engine = ClarificationEngine(llm_client)
    return _clarification_engine
