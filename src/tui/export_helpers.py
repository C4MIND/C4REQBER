"""
TUI: Export Helpers
Export discovery results to JSON, Markdown, LaTeX, HTML, text.
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


EXPORT_DIR = Path("discovery/export")


def export_discovery(results: dict[str, Any], problem: str, fmt: str) -> str:
    """Export discovery results to the specified format."""
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = re.sub(r'[^a-zA-Z0-9_-]', '_', problem[:40])

    if fmt == "json":
        path = EXPORT_DIR / f"discovery_{slug}_{timestamp}.json"
        data = {
            "problem": problem,
            "results": results,
            "exported_at": datetime.now().isoformat(),
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2, default=str, ensure_ascii=False)
        return str(path)

    elif fmt == "markdown":
        path = EXPORT_DIR / f"discovery_{slug}_{timestamp}.md"
        papers = results.get("papers_found", "?")
        isomorphisms = results.get("isomorphisms", {}).get("found", "?") if isinstance(results.get("isomorphisms"), dict) else "?"
        hyp = results.get("hypothesis", {})
        hyp_text = hyp.get("text", str(hyp)) if isinstance(hyp, dict) else str(hyp)
        lines = [
            f"# Научное Открытие: {problem}",
            "",
            f"**Сгенерировано:** {datetime.now().isoformat()}",
            f"**Домен:** {results.get('domain', 'general')}",
            f"**Статус:** {results.get('status', 'completed')}",
            "",
            "---",
            "",
            "## Проблема",
            "",
            problem,
            "",
            "## Результаты",
            "",
            f"- 📚 Найдено статей: {papers}",
            f"- 🧬 Изоморфизмов: {isomorphisms}",
            f"- ⏱️ Время: {results.get('total_time', 'N/A')}с",
            "",
            "## Гипотеза",
            "",
            hyp_text[:2000],
            "",
            "---",
            "",
            "*Сгенерировано Reqber v5.3.0*",
        ]
        with open(path, "w") as f:
            f.write("\n".join(lines))
        return str(path)

    elif fmt == "latex":
        path = EXPORT_DIR / f"discovery_{slug}_{timestamp}.tex"
        hyp = results.get("hypothesis", {})
        hyp_text = hyp.get("text", str(hyp)) if isinstance(hyp, dict) else str(hyp)
        hyp_text = hyp_text.replace("_", "\\_").replace("&", "\\&").replace("#", "\\#")
        problem_esc = problem.replace("_", "\\_").replace("&", "\\&").replace("#", "\\#")
        tex = (
            "\\documentclass{article}\n"
            "\\usepackage[utf8]{inputenc}\n"
            "\\usepackage[russian]{babel}\n"
            f"\\title{{Научное Открытие: {problem_esc}}}\n"
            "\\author{Reqber v5.3.0}\n"
            f"\\date{{{datetime.now().strftime('%Y-%m-%d')}}}\n"
            "\\begin{document}\n"
            "\\maketitle\n"
            "\\section{Проблема}\n"
            + problem_esc + "\n\n"
            "\\section{Результаты}\n"
            "Статей найдено: " + str(results.get("papers_found", "?")) + ". "
            "Изоморфизмов: " + str(results.get("isomorphisms", {}).get("found", "?") if isinstance(results.get("isomorphisms"), dict) else "?") + ". "
            "Время: " + str(results.get("total_time", "N/A")) + "с.\n\n"
            "\\section{Гипотеза}\n"
            + hyp_text[:3000] + "\n\n"
            "\\end{document}\n"
        )
        with open(path, "w") as f:
            f.write(tex)
        return str(path)

    elif fmt == "html":
        path = EXPORT_DIR / f"discovery_{slug}_{timestamp}.html"
        papers = results.get("papers_found", "?")
        isomorphisms = results.get("isomorphisms", {}).get("found", "?") if isinstance(results.get("isomorphisms"), dict) else "?"
        hyp = results.get("hypothesis", {})
        hyp_text = hyp.get("text", str(hyp)) if isinstance(hyp, dict) else str(hyp)
        html = (
            "<!DOCTYPE html>\n"
            '<html lang="ru">\n'
            "<head>\n"
            '<meta charset="UTF-8">\n'
            f"<title>Reqber: {problem}</title>\n"
            "<style>\n"
            "  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 800px; margin: 40px auto; padding: 20px; background: #0a0a0a; color: #e0e0e0; }\n"
            "  h1 { color: #4ECDC4; border-bottom: 2px solid #4ECDC4; padding-bottom: 10px; }\n"
            "  h2 { color: #4ADE80; margin-top: 30px; }\n"
            "  .meta { color: #666; font-size: 0.9em; }\n"
            "  .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 15px; margin: 20px 0; }\n"
            "  .stat { background: #1a1a2e; padding: 15px; border-radius: 8px; border-left: 3px solid #4ECDC4; }\n"
            "  .stat-value { font-size: 1.5em; color: #4ECDC4; font-weight: bold; }\n"
            "  .hypothesis { background: #1a1a2e; padding: 20px; border-radius: 8px; border-left: 3px solid #ec4899; line-height: 1.6; }\n"
            "  footer { margin-top: 40px; color: #444; font-size: 0.8em; text-align: center; }\n"
            "</style>\n"
            "</head>\n"
            "<body>\n"
            f"<h1>Научное Открытие: {problem}</h1>\n"
            f'<p class="meta">Сгенерировано: {datetime.now().isoformat()} | Reqber v5.3.0</p>\n'
            '<div class="stats">\n'
            f'<div class="stat"><div class="stat-value">{papers}</div>Статей найдено</div>\n'
            f'<div class="stat"><div class="stat-value">{isomorphisms}</div>Изоморфизмов</div>\n'
            f'<div class="stat"><div class="stat-value">{results.get("total_time", "N/A")}с</div>Время</div>\n'
            "</div>\n"
            f"<h2>Проблема</h2>\n<p>{problem}</p>\n"
            f"<h2>Гипотеза</h2>\n<div class=\"hypothesis\">{hyp_text[:5000]}</div>\n"
            "<footer>Reqber v5.3.0 — AGPL-3.0</footer>\n"
            "</body>\n</html>\n"
        )
        with open(path, "w") as f:
            f.write(html)
        return str(path)

    elif fmt == "text":
        path = EXPORT_DIR / f"discovery_{slug}_{timestamp}.txt"
        papers = results.get("papers_found", "?")
        isomorphisms = results.get("isomorphisms", {}).get("found", "?") if isinstance(results.get("isomorphisms"), dict) else "?"
        hyp = results.get("hypothesis", {})
        hyp_text = hyp.get("text", str(hyp)) if isinstance(hyp, dict) else str(hyp)
        lines = [
            "=" * 60,
            f"НАУЧНОЕ ОТКРЫТИЕ: {problem}",
            "=" * 60,
            "",
            f"Дата: {datetime.now().isoformat()}",
            f"Домен: {results.get('domain', 'general')}",
            f"Статус: {results.get('status', 'completed')}",
            "",
            "-" * 60,
            "РЕЗУЛЬТАТЫ",
            "-" * 60,
            f"  Статей найдено: {papers}",
            f"  Изоморфизмов: {isomorphisms}",
            f"  Время: {results.get('total_time', 'N/A')}с",
            "",
            "-" * 60,
            "ГИПОТЕЗА",
            "-" * 60,
            hyp_text[:5000],
            "",
            "=" * 60,
            "Reqber v5.3.0 — AGPL-3.0",
        ]
        with open(path, "w") as f:
            f.write("\n".join(lines))
        return str(path)

    return ""
