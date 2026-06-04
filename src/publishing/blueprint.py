from __future__ import annotations


"""Blueprint/Schematic Generator for physical inventions."""
from typing import Any


class BlueprintGenerator:
    """BlueprintGenerator."""
    def generate_ascii_schematic(self, discovery_name: str, components: list[Any]) -> str:
        """Generate ascii schematic."""
        s = f"    {'='*50}\n    {discovery_name.upper():^50s}\n    {'='*50}\n"
        for i, c in enumerate(components):
            s += f"    [{i+1}] {c.get('name','?'):30s} {c.get('material','?'):15s}\n"
        s += f"    {'='*50}\n"
        return s

    def generate_svg_schematic(self, name: str, components: list[Any]) -> str:
        """Generate svg schematic."""
        svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 600"><rect width="800" height="600" fill="#0a0a0f"/><text x="400" y="30" text-anchor="middle" fill="#4ECDC4" font-size="20">{name}</text>'
        for i, c in enumerate(components):
            y = 80 + i * 50
            svg += f'<rect x="100" y="{y}" width="150" height="40" rx="6" fill="none" stroke="#4ECDC4" stroke-width="2"/><text x="175" y="{y+25}" text-anchor="middle" fill="#e2e8f0" font-size="12">{c.get("name","?")[:20]}</text>'
        svg += '</svg>'
        return svg

    def generate_cad_spec(self, name: str, components: list[Any]) -> dict[str, Any]:
        return {"project": name, "format": "STEP/STL", "units": "mm", "tolerance": "+/-0.1mm",
                "components": [{"id": f"COMP-{i+1:03d}", "name": c.get("name", f"Part_{i+1}"), "material": c.get("material", "Aluminum 6061"), "dimensions": c.get("dimensions", "100x50x20mm")} for i, c in enumerate(components)],
                "generated_by": "C44TCDI v5.0-alpha"}

    def generate_triz_rationale(self, components: list[Any], triz_principles: list[Any]) -> str:
        return "\n".join(f"  Component {i+1} ({c.get('name','?')}): TRIZ {triz_principles[i%len(triz_principles)] if triz_principles else 'N/A'}" for i, c in enumerate(components))
