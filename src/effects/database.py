"""
TURBO-CDI: Effects Database
Physical and chemical effects for problem solving
"""

from dataclasses import dataclass


@dataclass
class PhysicalEffect:
    """Physical effect for problem solving."""

    name: str
    description: str
    category: str  # mechanical, thermal, electromagnetic, etc.
    formula: str = ""
    parameters: list[str] = None
    applications: list[str] = None

    def __post_init__(self):
        if self.parameters is None:
            self.parameters = []
        if self.applications is None:
            self.applications = []


class EffectsDatabase:
    """
    Database of physical and chemical effects.

    Based on TRIZ Effects Database.
    Helps find physical phenomena to solve problems.
    """

    EFFECTS = {
        # Mechanical effects
        "piezoelectric": PhysicalEffect(
            name="Piezoelectric Effect",
            description="Mechanical stress generates electric charge",
            category="mechanical",
            formula="P = d * σ",
            parameters=["stress", "piezoelectric coefficient"],
            applications=["sensors", "actuators", "energy harvesting"],
        ),
        "shape_memory": PhysicalEffect(
            name="Shape Memory Effect",
            description="Material returns to original shape when heated",
            category="thermal",
            parameters=["temperature", "transition temperature"],
            applications=["actuators", "couplings", "medical devices"],
        ),
        "electromagnetic_induction": PhysicalEffect(
            name="Electromagnetic Induction",
            description="Changing magnetic field induces electric current",
            category="electromagnetic",
            formula="ε = -dΦ/dt",
            parameters=["magnetic flux", "time"],
            applications=["generators", "transformers", "wireless charging"],
        ),
        "thermoelectric": PhysicalEffect(
            name="Thermoelectric Effect",
            description="Temperature difference generates voltage",
            category="thermal",
            formula="V = S * ΔT",
            parameters=["temperature difference", "Seebeck coefficient"],
            applications=["cooling", "power generation", "temperature sensing"],
        ),
        "capillary": PhysicalEffect(
            name="Capillary Action",
            description="Liquid flows in narrow spaces without external forces",
            category="fluid",
            applications=["wicking", "microfluidics", "lubrication"],
        ),
        "electroosmotic": PhysicalEffect(
            name="Electroosmotic Flow",
            description="Electric field drives fluid flow",
            category="fluid",
            applications=["microfluidics", "pumping", "separation"],
        ),
        "photovoltaic": PhysicalEffect(
            name="Photovoltaic Effect",
            description="Light generates electric current",
            category="optical",
            applications=["solar cells", "light sensors", "energy"],
        ),
        "magnetostriction": PhysicalEffect(
            name="Magnetostriction",
            description="Material changes shape in magnetic field",
            category="magnetic",
            applications=["actuators", "sensors", "ultrasonics"],
        ),
    }

    def search_effects(
        self, query: str, category: str | None = None
    ) -> list[PhysicalEffect]:
        """
        Search effects by keyword.

        Args:
            query: Search term
            category: Filter by category

        Returns:
            List of matching effects
        """
        results = []
        query_lower = query.lower()

        for effect in self.EFFECTS.values():
            # Category filter
            if category and effect.category != category:
                continue

            # Search in name and description
            if (
                query_lower in effect.name.lower()
                or query_lower in effect.description.lower()
                or any(query_lower in app.lower() for app in effect.applications)
            ):
                results.append(effect)

        return results

    def get_effect(self, name: str) -> PhysicalEffect | None:
        """Get effect by name."""
        key = name.lower().replace(" ", "_")
        return self.EFFECTS.get(key)

    def get_by_category(self, category: str) -> list[PhysicalEffect]:
        """Get all effects in a category."""
        return [e for e in self.EFFECTS.values() if e.category == category]

    def suggest_effects(self, problem: str) -> list[PhysicalEffect]:
        """Suggest effects based on problem description."""
        problem_lower = problem.lower()
        suggestions = []

        # Keyword matching
        keywords = {
            "temperature": ["thermoelectric", "shape_memory"],
            "pressure": ["piezoelectric", "magnetostriction"],
            "flow": ["capillary", "electroosmotic"],
            "light": ["photovoltaic"],
            "magnetic": ["electromagnetic_induction", "magnetostriction"],
            "electricity": ["piezoelectric", "thermoelectric", "photovoltaic"],
        }

        for keyword, effect_names in keywords.items():
            if keyword in problem_lower:
                for name in effect_names:
                    effect = self.EFFECTS.get(name)
                    if effect and effect not in suggestions:
                        suggestions.append(effect)

        return suggestions

    def list_categories(self) -> list[str]:
        """List all effect categories."""
        return list(set(e.category for e in self.EFFECTS.values()))


# Singleton
_db: EffectsDatabase | None = None


def get_effects_database() -> EffectsDatabase:
    """Get singleton effects database."""
    global _db
    if _db is None:
        _db = EffectsDatabase()
    return _db
