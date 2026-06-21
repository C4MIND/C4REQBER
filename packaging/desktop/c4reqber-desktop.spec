# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for C4REQBER macOS/Windows desktop bundle."""

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
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["matplotlib", "pandas", "scipy", "gensim"],
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
        icon=None,
        bundle_identifier="org.c4reqber.desktop",
        info_plist={
            "CFBundleShortVersionString": "5.6.0",
            "CFBundleVersion": "560",
            "LSMinimumSystemVersion": "12.0",
        },
    )