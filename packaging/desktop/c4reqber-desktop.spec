# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for C4REQBER macOS/Windows desktop bundle (full settings: config + models + keys)."""

import sys
from pathlib import Path

root = Path(SPECPATH).resolve().parents[2]

a = Analysis(
    [str(root / "packaging" / "desktop" / "launcher_entry.py")],
    pathex=[str(root)],
    binaries=[],
    datas=[],
    hiddenimports=[
        "src.mcp_server.server",
        "src.mcp_server.fastmcp_bridge",
        "src.cli.blast_app",
        "src.cli.config_init",
        "src.cli.config_keys",
        "src.cli.tui_launcher",
        "src.config.paths",
        "src.config.secrets_store",
        "src.config.key_registry",
        "toml",
        "rich",
        "typer",
        "pydantic",
        "httpx",
        # Add common runtime needs for packaged desktop (knowledge, llm, etc.)
        "src.knowledge.orchestrator",
        "src.llm.gateway",
        "src.pipeline.config",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # Do not exclude core science libs - many patterns/simulations need numpy etc.
    # Only exclude truly optional heavy GUI ones if desired.
    excludes=["matplotlib", "gensim"],  # keep numpy/pandas/scipy for real sims
    datas=[
        # If any Python-side data files needed in bundle (i18n, templates, etc.)
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="blast",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="C4REQBER",
)

if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="C4REQBER.app",
        icon=None,  # no .icns yet — falls back to generic app icon
        bundle_identifier="org.c4reqber.desktop",
        info_plist={
            # Kept in sync with the canonical Go TUI version
            # (src/tui/v9/cmd/c4tui-v9/main.go: `var version = "v9.13.0"`).
            # When the Go side bumps, update here AND packaging/desktop/mac/Info.plist
            # AND packaging/desktop/win/build.iss (3 places, see CHANGELOG).
            "CFBundleShortVersionString": "9.13.0",
            "CFBundleVersion": "913",
            "LSMinimumSystemVersion": "12.0",
            "LSApplicationCategoryType": "public.app-category.developer-tools",
            "CFBundleCopyright": "(c) 2026 c4reqber",
        },
    )
