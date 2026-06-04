"""
Heuristic C4 Classifier — Keyword-based fallback (no ML dependencies).
=======================================================================

Used when no neural model is available.
Based on c4factory's keyword dictionaries.
"""



TIME_KEYWORDS = {
    0: ["yesterday", "last week", "last month", "last year", "used to",
        "back then", "in the past", "previously", "historically", "was changed", "crashed in",
        "вчера", "прошл", "раньше", "ранее", "когда-то", "в прошлом"],
    1: ["right now", "currently", "at this moment", "today", "is doing", "is down",
        "is stuck", "I'm thinking", "сейчас", "в данный момент", "сегодня", "прямо сейчас"],
    2: ["tomorrow", "next week", "will", "going to", "aspire", "will transform",
        "future of", "paradigm shift", "завтра", "будущ", "следующ", "планиру", "намерен"],
}

SCALE_KEYWORDS = {
    0: ["specific", "email", "meeting", "server", "line 47", "call",
        "product", "task", "deploy", "send", "launch", "pipeline",
        "конкретн", "детал", "специфичн", "точн", "именно", "конкретика"],
    1: ["pattern", "tend to", "usually", "always", "habit", "trend",
        "cycle", "feedback loop", "dynamics", "culture",
        "паттерн", "тенденци", "обычно", "всегда", "цикл", "динамик"],
    2: ["paradigm", "mental model", "metacognition", "thinking about thinking",
        "framework", "ways of knowing", "epistemology", "mindset",
        "парадигм", "ментальн", "метакогници", "мышлени", "эпистемолог"],
}

AGENCY_KEYWORDS = {
    0: ["I ", "I'm", "my ", "myself", "me ", "I've", "I'll",
        "я ", "мне ", "меня ", "мой", "моя", "сам"],
    1: ["he ", "she ", "they ", "him", "her", "them", "his ", "their",
        "он ", "она ", "они ", "его ", "ее ", "их ", "друг"],
    2: ["the system", "the organization", "the market", "society",
        "the field", "the company", "humanity", "science", "policy",
        "система", "организаци", "рынок", "общество", "компани", "человечество"],
}


def _score_axis(text: str, keywords: dict) -> int:
    text_lower = text.lower()
    scores = {v: 0 for v in keywords}
    for value, kws in keywords.items():
        for kw in kws:
            if kw.lower() in text_lower:
                scores[value] += 1
    best = max(scores, key=lambda k: scores[k])
    return best if scores[best] > 0 else 1


def classify(text: str) -> tuple[int, int, int]:
    """Return C4 coordinates (t, s, a) from keyword heuristics."""
    t = _score_axis(text, TIME_KEYWORDS)
    s = _score_axis(text, SCALE_KEYWORDS)
    a = _score_axis(text, AGENCY_KEYWORDS)
    return t, s, a
