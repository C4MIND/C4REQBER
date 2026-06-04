# SPDX-License-Identifier: AGPL-3.0
# Copyright (c) 2026 c4reqber Contributors
"""TUI Folder Panel — show connected research folder contents."""
from __future__ import annotations

from pathlib import Path

from rich.panel import Panel
from rich.text import Text
from textual.widgets import Static


class FolderPanel(Static):
    """Display connected folder: path, file count, types."""

    def __init__(self, folder: str = "") -> None:
        super().__init__("")
        self.folder = folder
        self.files: list[Path] = []

    def set_folder(self, folder: str) -> None:
        """Set folder."""
        self.folder = folder
        self._scan()

    def _scan(self) -> None:
        if not self.folder:
            self.files = []
            return
        p = Path(self.folder).expanduser()
        if not p.exists():
            self.files = []
            return
        self.files = sorted(
            [f for f in p.iterdir() if f.is_file() and f.suffix.lower() in {".pdf", ".txt", ".md", ".png", ".jpg"}],
            key=lambda f: f.stat().st_mtime, reverse=True,
        )

    def render(self) -> Panel:
        """Render."""
        if not self.folder:
            return Panel(
                Text("No folder connected\nUse: blast turbo --folder ~/papers/", style="dim italic"),
                title="Research Folder", border_style="dim",
            )
        if not self.files:
            return Panel(
                Text(f"Folder: {self.folder}\nNo supported files (.pdf/.txt/.md/.png)", style="dim"),
                title="Research Folder", border_style="yellow",
            )
        lines = [Text(f"📁 {self.folder}", style="bold cyan")]
        types: dict[str, int] = {}
        for f in self.files:
            ext = f.suffix.lower()
            types[ext] = types.get(ext, 0) + 1
        type_line = " · ".join(f"{c}×{ext}" for ext, c in sorted(types.items()))
        lines.append(Text(f"   {len(self.files)} files: {type_line}", style="dim"))
        for f in self.files[:5]:
            size_kb = f.stat().st_size / 1024
            lines.append(Text(f"   {f.suffix} {f.name[:40]:<42} {size_kb:.0f}KB", style="dim"))
        if len(self.files) > 5:
            lines.append(Text(f"   ... and {len(self.files) - 5} more files", style="dim italic"))
        return Panel(Text("\n").join(lines), title="Research Folder", border_style="cyan")
