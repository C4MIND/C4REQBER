"""
Preprint submitter — generates real arXiv/bioRxiv submission packages with LaTeX + BibTeX.
"""
from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any


logger = logging.getLogger(__name__)

_BIBTEX_TEMPLATE = """@article{{{cite_key},
  title = {{{title}}},
  author = {{{authors}}},
  year = {{{year}}},
  journal = {{{journal}}},
  doi = {{{doi}}},
  url = {{{url}}},
}}"""

_LATEX_TEMPLATE = r"""\documentclass[12pt,a4paper]{{article}}
\usepackage[utf8]{{inputenc}}
\usepackage{{amsmath,amssymb,amsfonts}}
\usepackage{{hyperref}}
\usepackage{{geometry}}
\usepackage{{natbib}}
\geometry{{margin=1in}}

\title{{{title}}}
\author{{{author}}}
\date{{{date}}}

\begin{{document}}

\maketitle

\begin{{abstract}}
{abstract}
\end{{abstract}}

{body}

\bibliographystyle{{plainnat}}
\bibliography{{{bibfile}}}

\end{{document}}
"""


class PreprintSubmitter:
    """Generates ready-to-submit arXiv/bioRxiv packages."""

    @staticmethod
    def _escape_latex(text: str) -> str:
        for char, repl in [("\\", "\\textbackslash "), ("&", "\\&"), ("%", "\\%"),
                           ("$", "\\$"), ("#", "\\#"), ("_", "\\_"), ("{", "\\{"), ("}", "\\}"),
                           ("~", "\\textasciitilde "), ("^", "\\^{}"), ("<", "\\textless "),
                           (">", "\\textgreater "), ("\x00", ""), ("\x01", ""),
                           ("<jats:", ""), ("</jats:", ""), ("<italic>", "\\textit{"), ("</italic>", "}")]:
            text = text.replace(char, repl) if char in text else text
        return text

    @staticmethod
    def _references_to_bibtex(references: list[dict[str, Any]]) -> str:
        entries = []
        for i, ref in enumerate(references[:50]):
            authors_raw = ref.get("authors", ref.get("author", "Unknown"))
            if isinstance(authors_raw, list):
                authors_raw = " and ".join(str(a).strip() for a in authors_raw[:5])
            cite_key = ref.get("cite_key", f"ref{i+1}")
            if not cite_key or cite_key == "unknown":
                authors_first = str(authors_raw).split(",")[0].split(" ")[-1] if authors_raw else "Unknown"
                year = ref.get("year", "2025")
                cite_key = f"{authors_first}{year}"
            entry = _BIBTEX_TEMPLATE.format(
                cite_key=cite_key,
                title=PreprintSubmitter._escape_latex(str(ref.get("title", "Untitled"))[:200]),
                authors=PreprintSubmitter._escape_latex(str(authors_raw)[:300]),
                year=ref.get("year", "2025"),
                journal=PreprintSubmitter._escape_latex(str(ref.get("journal", ref.get("source", "Unknown")))[:100]),
                doi=ref.get("doi", ""),
                url=ref.get("url", f"https://doi.org/{ref.get('doi', '')}" if ref.get("doi") else ""),
            )
            entries.append(entry)
        return "\n\n".join(entries)

    @classmethod
    def generate_arxiv_submission(
        cls, paper_body: str, abstract: str, title: str = "",
        author: str = "C4Reqber Research", references: list[dict[str, Any]] | None = None,
        output_dir: str | None = None,
    ) -> dict[str, Any]:
        """Generate complete arXiv-ready submission package with LaTeX + BibTeX."""
        out_path = Path(output_dir or "exports/arxiv")
        out_path.mkdir(parents=True, exist_ok=True)
        today = datetime.now().strftime("%Y-%m-%d")

        safe_title = cls._escape_latex(title or "Research Discovery")[:200]
        safe_abstract = cls._escape_latex(abstract)[:500]
        safe_body = paper_body.replace("##", "\\section{").replace("###", "\\subsection{")
        if "\\section{" in safe_body:
            safe_body = safe_body.replace("\\section{", "\n\\section{")
        safe_body = cls._escape_latex(safe_body) if "\\section" not in safe_body else safe_body[:8000]
        safe_author = cls._escape_latex(author)[:100]

        latex_content = _LATEX_TEMPLATE.format(
            title=safe_title, author=safe_author, date=today,
            abstract=safe_abstract, body=safe_body, bibfile="references",
        )
        tex_path = out_path / "paper.tex"
        tex_path.write_text(latex_content, encoding="utf-8")

        bib_content = cls._references_to_bibtex(references or [])
        bib_path = out_path / "references.bib"
        bib_path.write_text(bib_content, encoding="utf-8")

        logger.info("arXiv package generated: %s", out_path)
        return {
            "latex": latex_content[:1000] + "..." if len(latex_content) > 1000 else latex_content,
            "bibtex": bib_content[:500] + "..." if len(bib_content) > 500 else bib_content,
            "abstract": safe_abstract,
            "title": safe_title,
            "category": "cs.AI",
            "format": "arXiv-ready LaTeX + BibTeX",
            "tex_path": str(tex_path),
            "bib_path": str(bib_path),
            "output_dir": str(out_path),
        }

    @classmethod
    def generate_biorxiv_submission(
        cls, paper_body: str, abstract: str, title: str = "",
        author: str = "C4Reqber Research", references: list[dict[str, Any]] | None = None,
        output_dir: str | None = None,
    ) -> dict[str, Any]:
        """Generate bioRxiv-ready submission package."""
        result = cls.generate_arxiv_submission(
            paper_body=paper_body, abstract=abstract, title=title,
            author=author, references=references,
            output_dir=output_dir or "exports/biorxiv",
        )
        result["format"] = "bioRxiv-ready LaTeX + BibTeX"
        result["category"] = "quantitative-biology"
        return result


def generate_arxiv_package(paper_body: str, abstract: str, **kwargs: Any) -> dict[str, Any]:
    return PreprintSubmitter.generate_arxiv_submission(paper_body, abstract, **kwargs)


def generate_biorxiv_package(paper_body: str, abstract: str, **kwargs: Any) -> dict[str, Any]:
    return PreprintSubmitter.generate_biorxiv_submission(paper_body, abstract, **kwargs)
