"""
C4 Classifier - классификация текста в когнитивные координаты
=============================================================

Поддерживаемые бэкенды:
- local: Ollama/LM Studio (бесплатно, локально)
- groq: Groq API (бесплатно, 14K req/day)
- mistral: Mistral API (бесплатно, 1B tokens/month)
- cerebras: Cerebras API (бесплатно, быстрый инференс)
- deepseek: DeepSeek API (дёшево, $0.14/M tokens)
- openai: OpenAI API (платно)
"""

import logging
import os
import re
from dataclasses import dataclass
from typing import Any

from .types import (
    C4_INTERPRETATIONS_RU,
    AgencyAxis,
    C4Classification,
    C4State,
    ScaleAxis,
    TimeAxis,
)


logger = logging.getLogger(__name__)


@dataclass
class BackendConfig:
    """Конфигурация бэкенда для LLM"""
    name: str
    base_url: str
    api_key_env: str
    default_model: str
    supports_json: bool = True


# Предустановленные конфигурации бэкендов
BACKENDS: dict[str, BackendConfig] = {
    "local": BackendConfig(
        name="local",
        base_url="http://localhost:11434/v1",
        api_key_env="",  # Ollama не требует ключа
        default_model="qwen2.5:7b",
        supports_json=True,
    ),
    "groq": BackendConfig(
        name="groq",
        base_url="https://api.groq.com/openai/v1",
        api_key_env="GROQ_API_KEY",
        default_model="llama-3.3-70b-versatile",
        supports_json=True,
    ),
    "mistral": BackendConfig(
        name="mistral",
        base_url="https://api.mistral.ai/v1",
        api_key_env="MISTRAL_API_KEY",
        default_model="mistral-large-latest",
        supports_json=True,
    ),
    "cerebras": BackendConfig(
        name="cerebras",
        base_url="https://api.cerebras.ai/v1",
        api_key_env="CEREBRAS_API_KEY",
        default_model="llama3.1-70b",
        supports_json=False,
    ),
    "deepseek": BackendConfig(
        name="deepseek",
        base_url="https://api.deepseek.com/v1",
        api_key_env="DEEPSEEK_API_KEY",
        default_model="deepseek-chat",
        supports_json=True,
    ),
    "openai": BackendConfig(
        name="openai",
        base_url="https://api.openai.com/v1",
        api_key_env="OPENAI_API_KEY",
        default_model="gpt-4o-mini",
        supports_json=True,
    ),
    "openrouter": BackendConfig(
        name="openrouter",
        base_url="https://openrouter.ai/api/v1",
        api_key_env="OPENROUTER_API_KEY",
        default_model="meta-llama/llama-3-70b-instruct",  # Free tier!
        supports_json=True,
    ),
    "gemini": BackendConfig(
        name="gemini",
        base_url="https://generativelanguage.googleapis.com/v1beta/openai",
        api_key_env="GEMINI_API_KEY",
        default_model="gemini-2.0-flash",  # Free 60 req/min
        supports_json=True,
    ),
}


class C4Classifier:
    """
    Классификатор текста в C4 координаты.

    Использует LLM для определения когнитивных координат текста:
    - T (Time): Past/Present/Future
    - D (Scale): Concrete/Abstract/Meta
    - I (Agency): Self/Other/System

    Example:
        >>> classifier = C4Classifier(backend='local')
        >>> result = classifier.classify("Вчера я купил хлеб")
        >>> print(result.state)
        F⟨Past, Concrete, Self⟩
    """

    CLASSIFICATION_PROMPT = '''Classify the following text into cognitive coordinates (T,D,I).

== TIME AXIS (T) ==
0 = PAST: Events that happened, history, completed actions, dates before now
1 = PRESENT: Current state, ongoing facts, timeless truths, descriptions of existing things
2 = FUTURE: Plans, predictions, expectations, will/shall/going to

Examples:
- "World War II ended in 1945" → T=0 (Past)
- "The Eiffel Tower is 330 meters tall" → T=1 (Present, timeless fact)
- "Scientists predict temperatures will rise" → T=2 (Future)

== SCALE AXIS (D) - CRITICAL DISTINCTION ==
0 = CONCRETE: Numbers, facts, specific events, named entities, measurements
1 = ABSTRACT: Theories, philosophies, general ideas ABOUT topics
2 = META: ONLY when someone is OBSERVING THEIR OWN MIND as it thinks

CONCRETE (D=0) examples:
- "John Smith was born on March 5, 1980" → D=0
- "The server processed 1000 requests" → D=0
- "She measured 42 units yesterday" → D=0

ABSTRACT (D=1) examples:
- "Freedom is essential for human dignity" → D=1 (philosophy)
- "AI will transform society" → D=1 (theory about AI)
- "Consciousness is mysterious" → D=1 (statement about consciousness)
- "Thinking is complex" → D=1 (general statement about thinking)
- "Metacognition is important" → D=1 (statement ABOUT metacognition)

META (D=2) - ONLY for SELF-OBSERVATION of own thinking:
- "I notice my thoughts racing" → D=2 (observing own thoughts)
- "I caught myself overthinking" → D=2 (caught = observed self)
- "Why do I think this way?" → D=2 (questioning OWN thinking)
- "I am watching how my mind works" → D=2 (watching own mind)

KEY WORDS for META: "I notice", "I caught myself", "I watch my thoughts", "why do I think"

NOT META:
- "Thinking is hard" → D=1 (statement about thinking, not self-observation)
- "Minds are complex" → D=1 (general statement)
- Just MENTIONING "thinking/cognition/metacognition" does NOT make it Meta

== AGENCY AXIS (I) ==
0 = SELF: First person "I/my/me", personal experience, author's feelings
1 = WE: First person plural "we/our/us", shared experience, collective identity
2 = THEY: Third person, describing others, external entities, institutions

Examples:
- "I feel anxious about tomorrow" → I=0 (Self)
- "We launched our product last month" → I=1 (We)
- "Apple Inc. reported record profits" → I=2 (They)

IMPORTANT RULES:
- News/encyclopedia articles = almost always D=0 (Concrete), I=2 (They)
- D=2 (Meta) is RARE - only when someone explicitly observes their own thinking
- If no "I/my/we/our" present → I=2 (They)

Text: "{text}"

Return ONLY three numbers: T,D,I (e.g., 0,1,2)
'''

    CLASSIFICATION_PROMPT_RU = '''Классифицируй текст по когнитивным координатам (T,D,I).

== ОСЬ ВРЕМЕНИ (T) ==
0 = ПРОШЛОЕ: События которые произошли, история, завершённые действия
1 = НАСТОЯЩЕЕ: Текущее состояние, факты, вечные истины
2 = БУДУЩЕЕ: Планы, прогнозы, ожидания, "будет/собирается"

== ОСЬ МАСШТАБА (D) - КРИТИЧНОЕ РАЗЛИЧИЕ ==
0 = КОНКРЕТНОЕ: Числа, факты, конкретные события, имена, измерения
1 = АБСТРАКТНОЕ: Теории, философия, общие идеи О темах
2 = МЕТА: ТОЛЬКО когда кто-то НАБЛЮДАЕТ ЗА СВОИМ УМОМ в процессе мышления

КОНКРЕТНОЕ (D=0) примеры:
- "Иван Петров родился 5 марта 1980" → D=0
- "Сервер обработал 1000 запросов" → D=0
- "Она измерила 42 единицы вчера" → D=0

АБСТРАКТНОЕ (D=1) примеры:
- "Свобода важна для достоинства человека" → D=1 (философия)
- "ИИ трансформирует общество" → D=1 (теория об ИИ)
- "Сознание загадочно" → D=1 (высказывание о сознании)
- "Мышление - это сложно" → D=1 (общее утверждение о мышлении)
- "Метапознание важно" → D=1 (утверждение О метапознании)

МЕТА (D=2) - ТОЛЬКО для САМОНАБЛЮДЕНИЯ за своим мышлением:
- "Я замечаю как мои мысли скачут" → D=2 (наблюдение за своими мыслями)
- "Я поймал себя на том что думаю о плохом" → D=2 (поймал = заметил себя)
- "Почему я так думаю?" → D=2 (вопрос о СВОЁМ мышлении)
- "Я наблюдаю как работает мой ум" → D=2 (наблюдение за своим умом)

КЛЮЧЕВЫЕ СЛОВА для МЕТА: "я замечаю", "я поймал себя", "я наблюдаю за своими мыслями"

НЕ МЕТА:
- "Мышление сложное" → D=1 (утверждение о мышлении, не самонаблюдение)
- "Умы сложны" → D=1 (общее утверждение)
- Простое УПОМИНАНИЕ "мышление/познание/метапознание" НЕ делает текст Мета

== ОСЬ АГЕНТНОСТИ (I) ==
0 = Я: "я/мой/мне", личный опыт
1 = МЫ: "мы/наш/нам", коллективный опыт
2 = ОНИ: Третье лицо, внешние сущности

ВАЖНЫЕ ПРАВИЛА:
- Новости/энциклопедии = почти всегда D=0 (Конкретное), I=2 (Они)
- D=2 (Мета) РЕДКО - только когда кто-то явно наблюдает за своим мышлением
- Если нет "я/мой/мы/наш" → I=2 (Они)

Текст: "{text}"

Ответь ТОЛЬКО тремя числами: T,D,I (например: 0,1,2)
'''

    def __init__(
        self,
        backend: str = "local",
        model: str | None = None,
        api_key: str | None = None,
        language: str = "auto",
    ):
        """
        Args:
            backend: имя бэкенда (local, groq, mistral, cerebras, deepseek, openai)
            model: модель для использования (по умолчанию зависит от бэкенда)
            api_key: API ключ (если не указан, берётся из env)
            language: язык промпта ('auto', 'en' или 'ru')
                     'auto' = авто-определение по тексту (рекомендуется)
        """
        if backend not in BACKENDS:
            raise ValueError(f"Unknown backend: {backend}. Available: {list(BACKENDS.keys())}")

        self.config = BACKENDS[backend]
        self.backend = backend
        self.model = model or self.config.default_model
        self.language = language
        self._client = None
        self._api_key = api_key

    def _get_client(self):
        """Lazy initialization клиента OpenAI"""
        if self._client is None:
            try:
                from openai import OpenAI
            except ImportError as e:
                raise ImportError("openai package required. Install: pip install openai") from e

            api_key = self._api_key
            if not api_key and self.config.api_key_env:
                api_key = os.getenv(self.config.api_key_env)
                if not api_key:
                    raise ValueError(
                        f"API key not found. Set {self.config.api_key_env} env var "
                        f"or pass api_key parameter."
                    )

            self._client = OpenAI(
                base_url=self.config.base_url,
                api_key=api_key or "not-needed",  # Ollama не требует ключа
            )

        return self._client

    def _get_prompt(self, text: str = "") -> str:
        """Возвращает промпт для классификации с авто-определением языка"""
        # Авто-определение языка если не задан явно
        if self.language == "auto" and text:
            lang = self._detect_language(text)
        else:
            lang = self.language

        if lang == "ru":
            return self.CLASSIFICATION_PROMPT_RU
        return self.CLASSIFICATION_PROMPT

    def _detect_language(self, text: str) -> str:
        """Простое определение языка по символам"""
        # Считаем русские буквы
        ru_chars = sum(1 for c in text if 'а' <= c.lower() <= 'я' or c in 'ёЁ')
        # Если более 30% - русский
        if len(text) > 0 and ru_chars / len(text) > 0.3:
            return "ru"
        return "en"

    def classify(self, text: str, max_text_length: int = 1000) -> C4Classification:
        """
        Классифицировать текст в C4 координаты.

        Args:
            text: текст для классификации
            max_text_length: максимальная длина текста (обрезается)

        Returns:
            C4Classification с результатом
        """
        client = self._get_client()

        # Обрезаем слишком длинный текст
        truncated_text = text[:max_text_length]
        prompt = self._get_prompt(truncated_text).format(text=truncated_text)

        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=20,
            )
            result = response.choices[0].message.content.strip()
            state = self._parse_result(result)

        except Exception as e:
            logger.warning(f"Classification failed: {e}. Using default state.")
            state = C4State(TimeAxis.PRESENT, ScaleAxis.CONCRETE, AgencyAxis.SELF)

        return C4Classification(
            state=state,
            text=text,
            source=f"{self.backend}:{self.model}",
            model=self.model,
        )

    def classify_batch(
        self,
        texts: list[str],
        batch_size: int = 10,
        show_progress: bool = False,
    ) -> list[C4Classification]:
        """
        Классифицировать несколько текстов.

        Args:
            texts: список текстов
            batch_size: размер батча (для rate limiting)
            show_progress: показывать прогресс

        Returns:
            Список C4Classification
        """
        results = []
        total = len(texts)

        for i, text in enumerate(texts):
            if show_progress and i % 10 == 0:
                logger.info(f"Progress: {i}/{total}")
            results.append(self.classify(text))

        return results

    def _parse_result(self, result: str) -> C4State:
        """
        Парсинг ответа LLM в C4State.

        Поддерживает форматы: "1,0,2", "1, 0, 2", "(1,0,2)", "T=1, D=0, I=2"
        """
        try:
            # Убираем лишние символы
            clean = result.replace("(", "").replace(")", "").replace(" ", "")
            clean = clean.replace("T=", "").replace("D=", "").replace("I=", "")

            # Ищем три числа
            match = re.search(r"(\d)[,\s]+(\d)[,\s]+(\d)", clean)
            if match:
                t, d, i = int(match.group(1)), int(match.group(2)), int(match.group(3))
            else:
                # Пробуем разбить по запятой
                parts = clean.split(",")
                t, d, i = int(parts[0]), int(parts[1]), int(parts[2])

            # Валидация диапазона
            t = max(0, min(2, t))
            d = max(0, min(2, d))
            i = max(0, min(2, i))

            return C4State(TimeAxis(t), ScaleAxis(d), AgencyAxis(i))

        except (ValueError, IndexError, AttributeError) as e:
            logger.warning(f"Failed to parse '{result}': {e}")
            # Дефолт: Present, Concrete, Self
            return C4State(TimeAxis.PRESENT, ScaleAxis.CONCRETE, AgencyAxis.SELF)

    def explain(self, text: str) -> dict[str, Any]:
        """
        Классифицировать с подробным объяснением.

        Returns:
            Словарь с классификацией и интерпретацией
        """
        classification = self.classify(text)
        state = classification.state
        coords = state.coordinates

        return {
            "text": text[:100] + "..." if len(text) > 100 else text,
            "state": state,
            "coordinates": coords,
            "label": state.label,
            "label_ru": state.label_ru,
            "index": state.index,
            "interpretation_ru": C4_INTERPRETATIONS_RU.get(coords, "Неизвестное состояние"),
            "model": self.model,
            "backend": self.backend,
        }

    def test_connection(self) -> bool:
        """Проверить соединение с бэкендом"""
        try:
            result = self.classify("Test message")
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False

    def __repr__(self) -> str:
        return f"C4Classifier(backend='{self.backend}', model='{self.model}')"


# Фабричные функции для удобства
def create_local_classifier(model: str = "qwen2.5:7b") -> C4Classifier:
    """Создать локальный классификатор (Ollama)"""
    return C4Classifier(backend="local", model=model)


def create_groq_classifier(model: str | None = None) -> C4Classifier:
    """Создать Groq классификатор (бесплатно)"""
    return C4Classifier(backend="groq", model=model)


def create_mistral_classifier(model: str | None = None) -> C4Classifier:
    """Создать Mistral классификатор (бесплатно)"""
    return C4Classifier(backend="mistral", model=model)


def create_deepseek_classifier(model: str | None = None) -> C4Classifier:
    """Создать DeepSeek классификатор (дёшево)"""
    return C4Classifier(backend="deepseek", model=model)


def create_openrouter_classifier(model: str | None = None) -> C4Classifier:
    """Создать OpenRouter классификатор (бесплатные модели!)"""
    return C4Classifier(backend="openrouter", model=model)


def create_gemini_classifier(model: str | None = None) -> C4Classifier:
    """Создать Gemini классификатор (бесплатно 60 req/min)"""
    return C4Classifier(backend="gemini", model=model)
