# SPDX-License-Identifier: AGPL-3.0
# Copyright (c) 2026 c4reqber Contributors
from __future__ import annotations

from rich.panel import Panel
from rich.text import Text
from textual.widgets import Static


class ArticleCanvas(Static):
    """Rendered article/dissertation output with scrolling and section navigation."""

    def __init__(self) -> None:
        super().__init__("")
        self.title = ""
        self.abstract = ""
        self.sections: list[tuple[str, str]] = []  # (heading, body)
        self.citations: list[str] = []
        self.verification_result: str = ""
        self.proof_files: list[str] = []  # v5.3.5
        self._scroll_offset = 0

    def load(self, path: str) -> None:
        try:
            with open(path) as f:
                text = f.read()
            self._parse(text)
        except OSError:
            self.title = "(generating...)"

    def set_content(self, title: str, abstract: str, sections: list[tuple[str, str]], citations: list[str] | None = None) -> None:
        """Set content."""
        self.title = title
        self.abstract = abstract
        self.sections = sections
        self.citations = citations or []
        self._scroll_offset = 0

    def scroll(self, delta: int) -> None:
        self._scroll_offset = max(0, min(self._scroll_offset + delta, max(0, len(self.sections) - 8)))

    def _parse(self, text: str) -> None:
        lines = text.splitlines()
        self.title = lines[0].lstrip("# ") if lines else ""
        sections: list[tuple[str, str]] = []
        current_heading = ""
        current_body: list[str] = []
        in_abstract = False
        abstract_lines: list[str] = []
        for line in lines[1:]:
            if line.startswith("## "):
                if current_heading and current_body:
                    sections.append((current_heading, "\n".join(current_body)))
                current_heading = line[3:].strip()
                current_body = []
                in_abstract = False
            elif line.startswith("**Abstract"):
                in_abstract = True
            elif in_abstract and line.strip() and not line.startswith("**"):
                abstract_lines.append(line.strip())
            elif current_heading:
                current_body.append(line)
        if current_heading and current_body:
            sections.append((current_heading, "\n".join(current_body)))
        self.abstract = " ".join(abstract_lines)[:500]
        self.sections = sections

    def render(self) -> Panel:
        """Render."""
        if not self.title:
            return Panel(
                Text("Article will appear here after pipeline completion", style="dim italic"),
                title="[bold]Article Canvas[/]", border_style="cyan",
            )
        lines: list[Text] = []
        lines.append(Text(self.title, style="bold white underline"))
        lines.append(Text(""))

        if self.abstract:
            lines.append(Text("Abstract", style="bold #06d6a0"))
            lines.append(Text(self.abstract[:400], style="dim"))
            lines.append(Text("─" * 36, style="dim #333355"))
            lines.append(Text(""))

        visible = self.sections[self._scroll_offset:self._scroll_offset + 8]
        for heading, body in visible:
            lines.append(Text(f"▸ {heading}", style="bold #e040fb"))
            lines.append(Text(body[:200] + ("..." if len(body) > 200 else ""), style="dim white"))
            lines.append(Text(""))

        if self._scroll_offset > 0 or len(self.sections) > 8:
            nav = f"▲ scroll up ({self._scroll_offset + 1}-{min(self._scroll_offset + 8, len(self.sections))} of {len(self.sections)}) ▼"
            lines.append(Text(nav, style="dim cyan"))

        if self.citations:
            lines.append(Text(""))
            lines.append(Text("References", style="bold #06d6a0"))
            for i, cite in enumerate(self.citations[:5]):
                lines.append(Text(f"  [{i+1}] {cite[:100]}", style="dim"))

        if self.verification_result:
            color = "green" if "PASS" in self.verification_result else "red"
            lines.append(Text(""))
            lines.append(Text(f"Verification: {self.verification_result}", style=f"bold {color}"))

        if self.proof_files:
            lines.append(Text(""))
            lines.append(Text("Exported Proof Files:", style="bold cyan"))
            for pf in self.proof_files:
                lines.append(Text(f"  📄 {pf}", style="dim"))

        content = Text("\n").join(lines)
        return Panel(content, title="[bold #e040fb]Article Canvas[/]", border_style="#06d6a0", padding=(1, 2))
