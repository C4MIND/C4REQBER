"""
TURBO-CDI: Presentation Mode
Export discoveries to slide decks
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import json


@dataclass
class Slide:
    """A presentation slide."""

    title: str
    content: str
    bullet_points: List[str]
    notes: str = ""


class PresentationExporter:
    """
    Export discoveries to presentation formats.

    Supports:
    - Markdown (for Marp, Slidev)
    - HTML (reveal.js)
    - PowerPoint (via python-pptx)
    """

    def __init__(self):
        pass

    def create_presentation(
        self, discovery_id: str, title: str = "Research Discovery"
    ) -> List[Slide]:
        """
        Create slides from a discovery.

        Args:
            discovery_id: Discovery to export
            title: Presentation title

        Returns:
            List of slides
        """
        from src.graph.knowledge_graph import get_knowledge_graph

        kg = get_knowledge_graph()
        discovery = kg.get_node(discovery_id)

        if not discovery:
            return []

        meta = discovery.get("metadata", {})
        problem = meta.get("problem", "")
        hypothesis = meta.get("hypothesis", "")
        c4_path = meta.get("c4_path", [])

        slides = []

        # Title slide
        slides.append(
            Slide(
                title=title,
                content=f"Scientific Discovery: {discovery_id}",
                bullet_points=[],
                notes="Introduction to the research findings",
            )
        )

        # Problem slide
        slides.append(
            Slide(
                title="Research Problem",
                content="The challenge we set out to solve",
                bullet_points=[
                    f"Problem: {problem}",
                    "Key constraints and requirements",
                    "Why existing solutions are insufficient",
                ],
                notes="Set up the problem context",
            )
        )

        # Methodology slide
        slides.append(
            Slide(
                title="Methodology: C4 Cognitive Geometry",
                content="How we approached the problem",
                bullet_points=[
                    f"Applied C4 operators: {' → '.join(c4_path)}",
                    "Systematic cognitive transformation",
                    "Cross-domain analogy and TRIZ principles",
                ],
                notes="Explain the methodology",
            )
        )

        # Hypothesis slide
        slides.append(
            Slide(
                title="Generated Hypothesis",
                content="Our proposed solution",
                bullet_points=[
                    hypothesis[:200] + "..." if len(hypothesis) > 200 else hypothesis,
                    "Key innovation: Context-aware mechanism",
                    "Eliminates apparent contradiction",
                ],
                notes="Present the core hypothesis",
            )
        )

        # Validation slide
        slides.append(
            Slide(
                title="Validation Plan",
                content="How to test this hypothesis",
                bullet_points=[
                    "Define falsifiability criteria",
                    "Design controlled experiments",
                    "Measure key performance indicators",
                ],
                notes="Outline next steps",
            )
        )

        # Conclusion slide
        slides.append(
            Slide(
                title="Summary & Next Steps",
                content="Key takeaways",
                bullet_points=[
                    "Novel solution generated via C4+TRIZ",
                    "Ready for experimental validation",
                    "Potential for significant impact",
                ],
                notes="Wrap up and call to action",
            )
        )

        return slides

    def export_to_markdown(
        self, slides: List[Slide], output_path: str, theme: str = "default"
    ):
        """
        Export slides to Markdown (Marp/Slidev format).

        Args:
            slides: List of slides
            output_path: Output file path
            theme: Theme name
        """
        md_lines = [
            "---",
            f"marp: true",
            f"theme: {theme}",
            "paginate: true",
            "---",
            "",
        ]

        for slide in slides:
            md_lines.append(f"# {slide.title}")
            md_lines.append("")

            if slide.content:
                md_lines.append(slide.content)
                md_lines.append("")

            for point in slide.bullet_points:
                md_lines.append(f"- {point}")

            md_lines.append("")
            md_lines.append("---")
            md_lines.append("")

        Path(output_path).write_text("\n".join(md_lines))

    def export_to_html(self, slides: List[Slide], output_path: str):
        """
        Export slides to HTML (reveal.js format).

        Args:
            slides: List of slides
            output_path: Output file path
        """
        slides_html = ""
        for slide in slides:
            bullets = "".join(f"<li>{p}</li>" for p in slide.bullet_points)

            slides_html += f"""
            <section>
                <h2>{slide.title}</h2>
                <p>{slide.content}</p>
                <ul>{bullets}</ul>
                <aside class="notes">{slide.notes}</aside>
            </section>
            """

        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Presentation</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@4/dist/reveal.css">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@4/dist/theme/white.css">
</head>
<body>
    <div class="reveal">
        <div class="slides">
            {slides_html}
        </div>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/reveal.js@4/dist/reveal.js"></script>
    <script>Reveal.initialize();</script>
</body>
</html>"""

        Path(output_path).write_text(html)


# Singleton
_exporter: Optional[PresentationExporter] = None


def get_presentation_exporter() -> PresentationExporter:
    """Get singleton presentation exporter."""
    global _exporter
    if _exporter is None:
        _exporter = PresentationExporter()
    return _exporter
