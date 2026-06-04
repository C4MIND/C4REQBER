"""Classic conceptual blending examples"""

from typing import TypedDict


class BlendInput(TypedDict):
    """BlendInput."""
    name: str
    entities: list[str]
    relations: list[tuple[str, str, str]]
    attributes: dict[str, list[str]]

CLOCK_BUDDHA: tuple[BlendInput, BlendInput] = (
    {
        "name": "clock",
        "entities": ["hands", "face", "mechanism", "time"],
        "relations": [
            ("hands", "move", "face"),
            ("mechanism", "drives", "hands"),
            ("hands", "indicate", "time"),
        ],
        "attributes": {
            "hands": ["moving", "precise"],
            "mechanism": ["internal", "reliable"],
            "time": ["measured", "continuous"],
        },
    },
    {
        "name": "buddha",
        "entities": ["body", "meditation", "enlightenment", "time"],
        "relations": [
            ("body", "practices", "meditation"),
            ("meditation", "leads_to", "enlightenment"),
        ],
        "attributes": {
            "meditation": ["internal", "continuous"],
            "enlightenment": ["timeless"],
            "body": ["still"],
        },
    },
)

SHIP_EARTH: tuple[BlendInput, BlendInput] = (
    {
        "name": "ship",
        "entities": ["captain", "crew", "course", "destination"],
        "relations": [
            ("captain", "commands", "crew"),
            ("crew", "steers", "course"),
            ("course", "leads_to", "destination"),
        ],
        "attributes": {
            "captain": ["wise", "responsible"],
            "crew": ["coordinated"],
            "course": ["planned"],
        },
    },
    {
        "name": "earth",
        "entities": ["humans", "nature", "environment", "future"],
        "relations": [
            ("humans", "affect", "environment"),
            ("environment", "shapes", "future"),
        ],
        "attributes": {
            "humans": ["diverse", "intelligent"],
            "nature": ["resilient", "fragile"],
            "future": ["uncertain"],
        },
    },
)

EXAMPLES: dict[str, tuple[BlendInput, BlendInput]] = {
    "clock_buddha": CLOCK_BUDDHA,
    "ship_earth": SHIP_EARTH,
}
