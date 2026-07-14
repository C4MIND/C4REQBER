"""
C4 базовые типы данных
======================

Импортирует канонический C4State из src.c4.types.
Сохраняет нейросетевые типы и интерпретации.

Формальная структура: Z_3^3 = 27 состояний
- Time (T): Past(0), Present(1), Future(2)
- Scale (S): Concrete(0), Abstract(1), Meta(2)
- Agency (A): Self(0), Other(1), System(2)
"""

from dataclasses import dataclass, field
from datetime import datetime

from src.c4.state import Agency, C4State, Scale, Time


# Re-export canonical enums with neural-classifier aliases
TimeAxis = Time
ScaleAxis = Scale
AgencyAxis = Agency


@dataclass
class C4Classification:
    """
    Результат классификации текста.

    Содержит C4State + метаданные классификации.
    """

    state: C4State
    text: str
    confidence: float = 1.0
    probabilities: tuple[list[float], list[float], list[float]] | None = None
    timestamp: datetime = field(default_factory=datetime.now)
    source: str = "unknown"
    model: str = "unknown"

    @property
    def coordinates(self) -> tuple[int, int, int]:
        return self.state.to_tuple()

    @property
    def label(self) -> str:
        """Формальная нотация F⟨T, S, A⟩"""
        t_names = {0: "Past", 1: "Present", 2: "Future"}
        s_names = {0: "Concrete", 1: "Abstract", 2: "Meta"}
        a_names = {0: "Self", 1: "Other", 2: "System"}
        return (
            f"F⟨{t_names[self.state.t]}, {s_names[self.state.s]}, {a_names[self.state.a]}⟩"
        )

    def to_dict(self) -> dict:
        """Сериализация в словарь"""
        return {
            "state_index": self.state.to_tuple(),
            "coordinates": self.coordinates,
            "label": self.label,
            "text_preview": self.text[:100] if len(self.text) > 100 else self.text,
            "confidence": self.confidence,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "model": self.model,
        }


# Предопределенные состояния для удобства
C4_STATES = {i: C4State(i // 9, (i % 9) // 3, i % 3) for i in range(27)}

# Имена состояний для интерпретации
C4_STATE_NAMES = {
    # Past
    (0, 0, 0): "personal_memory",
    (0, 0, 1): "others_past_actions",
    (0, 0, 2): "historical_facts",
    (0, 1, 0): "personal_patterns_past",
    (0, 1, 1): "others_past_patterns",
    (0, 1, 2): "historical_analysis",
    (0, 2, 0): "meta_reflection_past",
    (0, 2, 1): "others_past_thinking",
    (0, 2, 2): "history_of_ideas",
    # Present
    (1, 0, 0): "current_experience",
    (1, 0, 1): "observing_others",
    (1, 0, 2): "current_facts",
    (1, 1, 0): "self_understanding",
    (1, 1, 1): "understanding_others",
    (1, 1, 2): "systemic_analysis",
    (1, 2, 0): "metacognition_now",
    (1, 2, 1): "understanding_others_mind",
    (1, 2, 2): "current_paradigms",
    # Future
    (2, 0, 0): "personal_plans",
    (2, 0, 1): "predicting_others",
    (2, 0, 2): "systemic_forecasts",
    (2, 1, 0): "personal_goals",
    (2, 1, 1): "predicting_patterns",
    (2, 1, 2): "trend_analysis",
    (2, 2, 0): "meta_planning",
    (2, 2, 1): "predicting_thinking",
    (2, 2, 2): "paradigm_shifts",
}

# Интерпретации на русском
C4_INTERPRETATIONS_RU = {
    (0, 0, 0): "Личная память о конкретном событии",
    (0, 0, 1): "Воспоминания о действиях других людей",
    (0, 0, 2): "Исторические факты о системах",
    (0, 1, 0): "Рефлексия о личных паттернах прошлого",
    (0, 1, 1): "Анализ паттернов поведения других в прошлом",
    (0, 1, 2): "Исторический системный анализ",
    (0, 2, 0): "Мета-рефлексия о своем прошлом мышлении",
    (0, 2, 1): "Анализ того, как думали другие раньше",
    (0, 2, 2): "История идей и парадигм",
    (1, 0, 0): "Текущий личный опыт/ситуация",
    (1, 0, 1): "Наблюдение текущих действий других",
    (1, 0, 2): "Текущие системные факты/новости",
    (1, 1, 0): "Текущее самопонимание",
    (1, 1, 1): "Понимание текущих паттернов других",
    (1, 1, 2): "Текущий системный анализ",
    (1, 2, 0): "Метакогниция о текущем мышлении",
    (1, 2, 1): "Понимание того, как думают другие сейчас",
    (1, 2, 2): "Анализ текущих парадигм",
    (2, 0, 0): "Личные планы и намерения",
    (2, 0, 1): "Предсказание конкретных действий других",
    (2, 0, 2): "Конкретные системные прогнозы",
    (2, 1, 0): "Личные цели и паттерны будущего",
    (2, 1, 1): "Предсказание паттернов других",
    (2, 1, 2): "Анализ системных трендов",
    (2, 2, 0): "Мета-планирование будущей когниции",
    (2, 2, 1): "Предсказание эволюции мышления других",
    (2, 2, 2): "Будущие сдвиги парадигм",
}
