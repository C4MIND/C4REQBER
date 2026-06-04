"""c4reqber: LaTeX Compiler — pdflatex wrapper with auto-fix. Used by arXiv submission path."""
from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any


class LatexCompiler:
    """Compiles .tex to .pdf with pdflatex. Auto-fixes common errors.

    Requires ``pdflatex`` on system PATH.
    Install: ``brew install texlive`` (macOS) or ``apt install texlive`` (Linux).
    """

    COMMON_PACKAGES = [
        "amsmath", "amssymb", "graphicx", "hyperref", "geometry",
        "biblatex", "booktabs", "xcolor", "enumitem", "cleveref",
    ]

    def __init__(self, texlive_bin: str = "") -> None:
        self.pdflatex = shutil.which(texlive_bin or "pdflatex")

    @property
    def available(self) -> bool:
        return self.pdflatex is not None

    def compile(self, tex_source: str, output_dir: Path | None = None) -> dict[str, Any]:
        """Compile .tex to .pdf. Returns {success, pdf_path, log, errors}."""
        if not self.available:
            return {"success": False, "error": "pdflatex not found. Install: brew install texlive"}

        output_dir = output_dir or Path(tempfile.mkdtemp(prefix="c4reqber_tex_"))
        tex_file = output_dir / "preprint.tex"
        assert self.pdflatex is not None

        # Auto-fix: inject missing packages
        tex_source = self._auto_fix_packages(tex_source)

        tex_file.write_text(tex_source, encoding="utf-8")

        try:
            from src.utils.safe_subprocess import safe_subprocess_run

            result = safe_subprocess_run(
                [self.pdflatex, "-interaction=nonstopmode", "-output-directory", str(output_dir), str(tex_file)],
                cwd=output_dir,
                capture_output=True,
                text=True,
                timeout=120,
            )
            pdf = output_dir / "preprint.pdf"
            success = pdf.exists() and result.returncode == 0

            errors: list[str] = []
            if not success:
                for line in result.stdout.splitlines():
                    if line.startswith("!"):
                        errors.append(line.strip())

            # Second pass for ToC/refs
            if success and ("\\tableofcontents" in tex_source or "\\ref{" in tex_source or "\\cite{" in tex_source):
                safe_subprocess_run(
                    [self.pdflatex, "-interaction=nonstopmode", "-output-directory", str(output_dir), str(tex_file)],
                    cwd=output_dir,
                    capture_output=True,
                    text=True,
                    timeout=60,
                )

            return {"success": success, "pdf_path": str(pdf) if success else None, "log": result.stdout[-2000:], "errors": errors}

        except subprocess.TimeoutExpired:
            return {"success": False, "error": "pdflatex timed out (>120s)"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _auto_fix_packages(self, tex_source: str) -> str:
        """Inject missing common packages if not already present."""
        header_end = tex_source.find("\\begin{document}")
        if header_end == -1:
            return tex_source

        preamble = tex_source[:header_end]
        injected: list[str] = []

        for pkg in self.COMMON_PACKAGES:
            pattern = rf"\\usepackage\s*(\[.*?\])?\s*\{{{pkg}\}}"
            if not re.search(pattern, preamble):
                injected.append(f"\\usepackage{{{pkg}}}")

        if injected:
            inject_str = "% Auto-injected by c4reqber LatexCompiler\n" + "\n".join(injected) + "\n"
            doc_start = tex_source.find("\\begin{document}")
            return tex_source[:doc_start] + inject_str + tex_source[doc_start:]

        return tex_source
