# Desktop packaging — INTERNAL / NOT SHIPPED

This directory contains **maintainer-only** PyInstaller experiments wrapping TUI v9.
It is **not** part of the production release:

- **Production install:** `pip install c4reqber` + `blast tui`
- **CI artifact:** `registry.gitlab.com/cognitive-functors/turbo-cdi/api:latest`
- **Not published:** macOS `.dmg`, Windows `.exe`, or Tauri bundles from this tree

Do not reference these paths in user-facing docs, landing pages, or PyPI metadata.

To run TUI: `blast tui` or `pip install c4reqber && blast tui`.
