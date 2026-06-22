# SPDX-License-Identifier: AGPL-3.0
# Copyright (c) 2026 c4reqber Contributors
from __future__ import annotations


"""
Centralized Design System for c44tcdi
Single source of truth for all visual properties
"""
from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class ColorToken:
    """Immutable color definition with semantic meaning."""

    hex: str
    rgb: tuple[int, int, int]
    name: str
    usage: str

class DesignTokens:
    """Complete design token system."""

    # Brand Colors
    PRIMARY = ColorToken(
        hex="#4ECDC4",
        rgb=(78, 205, 196),
        name="Teal",
        usage="Primary actions, discovery, innovation",
    )

    SECONDARY = ColorToken(
        hex="#FF6B6B",
        rgb=(255, 107, 107),
        name="Coral",
        usage="Warnings, alerts, attention",
    )

    ACCENT = ColorToken(
        hex="#FFE66D",
        rgb=(255, 230, 109),
        name="Sunshine",
        usage="Highlights, confidence scores, stars",
    )

    SUCCESS = ColorToken(
        hex="#2ecc71",
        rgb=(46, 204, 113),
        name="Emerald",
        usage="Validation, success, completion",
    )

    WARNING = ColorToken(
        hex="#f39c12",
        rgb=(243, 156, 18),
        name="Amber",
        usage="Cautions, pending states",
    )

    ERROR = ColorToken(
        hex="#e74c3c",
        rgb=(231, 76, 60),
        name="Crimson",
        usage="Errors, failures, critical",
    )

    INFO = ColorToken(
        hex="#3498db",
        rgb=(52, 152, 219),
        name="Azure",
        usage="Information, IDs, neutral data",
    )

    # Neutral Scale
    WHITE = ColorToken("#ffffff", (255, 255, 255), "White", "Primary text on dark")
    GRAY_100 = ColorToken("#f8f9fa", (248, 249, 250), "Gray 100", "Light backgrounds")
    GRAY_200 = ColorToken("#e9ecef", (233, 236, 239), "Gray 200", "Borders light")
    GRAY_300 = ColorToken("#dee2e6", (222, 226, 230), "Gray 300", "Borders")
    GRAY_400 = ColorToken("#ced4da", (206, 212, 218), "Gray 400", "Disabled")
    GRAY_500 = ColorToken("#adb5bd", (173, 181, 189), "Gray 500", "Placeholder")
    GRAY_600 = ColorToken("#6c757d", (108, 117, 125), "Gray 600", "Secondary text")
    GRAY_700 = ColorToken("#495057", (73, 80, 87), "Gray 700", "Body text")
    GRAY_800 = ColorToken("#343a40", (52, 58, 64), "Gray 800", "Headers")
    GRAY_900 = ColorToken("#212529", (33, 37, 41), "Gray 900", "Deep backgrounds")

    # Dark Theme Specific
    DARK_BG_PRIMARY = ColorToken(
        "#0f0f1a", (15, 15, 26), "Dark Void", "Main background"
    )
    DARK_BG_SECONDARY = ColorToken("#1a1a2e", (26, 26, 46), "Dark Surface", "Cards")
    DARK_BG_TERTIARY = ColorToken(
        "#16213e", (22, 33, 62), "Dark Elevated", "Elevated surfaces"
    )
    DARK_BG_ELEVATED = ColorToken(
        "#0f3460", (15, 52, 96), "Dark Accent", "Active/Selected"
    )

    # Semantic Mapping
    SEMANTIC = {
        "identifier": INFO,  # IDs, codes
        "name": PRIMARY,  # Names, titles
        "value": SUCCESS,  # Values, metrics
        "status_pending": WARNING,
        "status_success": SUCCESS,
        "status_error": ERROR,
        "status_info": INFO,
    }

# Spacing System (8px grid)
SPACING = {
    "0": 0,
    "px": 1,
    "0.5": 2,  # xs
    "1": 4,  # sm
    "2": 8,  # md
    "3": 12,
    "4": 16,  # lg
    "5": 20,
    "6": 24,  # xl
    "8": 32,  # 2xl
    "10": 40,
    "12": 48,  # 3xl
    "16": 64,  # 4xl
    "20": 80,
    "24": 96,  # 5xl
}

# Typography Scale
TYPOGRAPHY = {
    "family": {
        "sans": "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
        "mono": "'JetBrains Mono', 'Fira Code', Consolas, monospace",
        "display": "'Inter', sans-serif",  # For headers
    },
    "size": {
        "xs": 12,  # Captions, labels
        "sm": 14,  # Small text
        "base": 16,  # Body
        "lg": 18,  # Large body
        "xl": 20,  # Lead text
        "2xl": 24,  # H3
        "3xl": 30,  # H2
        "4xl": 36,  # H1
        "5xl": 48,  # Display
        "6xl": 60,  # Hero
    },
    "weight": {
        "light": 300,
        "normal": 400,
        "medium": 500,
        "semibold": 600,
        "bold": 700,
        "extrabold": 800,
    },
    "line_height": {
        "none": 1,
        "tight": 1.25,
        "snug": 1.375,
        "normal": 1.5,
        "relaxed": 1.625,
        "loose": 2,
    },
}

# Border Radius
RADIUS = {
    "none": 0,
    "sm": 2,
    "base": 4,
    "md": 6,
    "lg": 8,
    "xl": 12,
    "2xl": 16,
    "3xl": 24,
    "full": 9999,
}

# Shadows
SHADOWS = {
    "none": "none",
    "sm": "0 1px 2px 0 rgba(0, 0, 0, 0.05)",
    "base": "0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)",
    "md": "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)",
    "lg": "0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)",
    "xl": "0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)",
    "2xl": "0 25px 50px -12px rgba(0, 0, 0, 0.25)",
    "inner": "inset 0 2px 4px 0 rgba(0, 0, 0, 0.06)",
    "glow_primary": "0 0 20px rgba(78, 205, 196, 0.4)",
    "glow_secondary": "0 0 20px rgba(255, 107, 107, 0.4)",
    "glow_accent": "0 0 20px rgba(255, 230, 109, 0.4)",
}

# Animation
ANIMATION = {
    "duration": {
        "75": "75ms",
        "100": "100ms",
        "150": "150ms",
        "200": "200ms",
        "300": "300ms",
        "500": "500ms",
        "700": "700ms",
        "1000": "1000ms",
    },
    "easing": {
        "linear": "linear",
        "in": "cubic-bezier(0.4, 0, 1, 1)",
        "out": "cubic-bezier(0, 0, 0.2, 1)",
        "in_out": "cubic-bezier(0.4, 0, 0.2, 1)",
        "bounce": "cubic-bezier(0.68, -0.55, 0.265, 1.55)",
    },
}

# Icons
ICONS = {
    # Navigation
    "home": "🏠",
    "discover": "🔬",
    "search": "🔍",
    "validate": "✓",
    "dashboard": "📊",
    "settings": "⚙️",
    # Actions
    "add": "+",
    "edit": "✎",
    "delete": "🗑",
    "save": "💾",
    "export": "📤",
    "import": "📥",
    "refresh": "↻",
    "close": "✕",
    "expand": "◀",
    "collapse": "▼",
    # States
    "success": "✓",
    "error": "✗",
    "warning": "⚠️",
    "info": "ℹ",
    "loading": "◌",
    "pending": "○",
    "check": "✓",
    "cross": "✗",
    # Features
    "hypothesis": "💡",
    "analogy": "🔗",
    "triz": "⚡",
    "c4": "◈",
    "graph": "🕸",
    "evolution": "📈",
    "effects": "⚛",
    "agent": "🤖",
    "multi_agent": "👥",
    # Data
    "paper": "📄",
    "patent": "📜",
    "reference": "📚",
    "experiment": "🧪",
    "metric": "📐",
    "database": "🗄",
    "folder": "📁",
    # C4 Specific
    "dimension_time": "⏱",
    "dimension_scale": "📏",
    "dimension_agency": "👤",
    "state_0": "0",
    "state_1": "1",
    "state_2": "2",
    # TRIZ
    "principle": "📋",
    "contradiction": "⚔️",
    "matrix": "🔲",
}

# Z-Index Scale
Z_INDEX = {
    "hide": -1,
    "auto": "auto",
    "base": 0,
    "docked": 10,
    "dropdown": 100,
    "sticky": 200,
    "banner": 300,
    "overlay": 400,
    "modal": 500,
    "popover": 600,
    "skip_link": 700,
    "toast": 800,
    "tooltip": 900,
}

# Breakpoints
BREAKPOINTS = {
    "sm": "640px",
    "md": "768px",
    "lg": "1024px",
    "xl": "1280px",
    "2xl": "1536px",
}

# Grid System
GRID = {
    "columns": 12,
    "gutter": SPACING["6"],
    "container_max": {
        "sm": "640px",
        "md": "768px",
        "lg": "1024px",
        "xl": "1280px",
        "2xl": "1536px",
    },
}

def get_color_by_status(status: str) -> ColorToken:
    """Get color token for a given status."""
    status_map = {
        "success": DesignTokens.SUCCESS,
        "completed": DesignTokens.SUCCESS,
        "validated": DesignTokens.SUCCESS,
        "error": DesignTokens.ERROR,
        "failed": DesignTokens.ERROR,
        "critical": DesignTokens.ERROR,
        "warning": DesignTokens.WARNING,
        "pending": DesignTokens.WARNING,
        "info": DesignTokens.INFO,
        "neutral": DesignTokens.GRAY_500,
    }
    return status_map.get(status.lower(), DesignTokens.INFO)

def get_icon_by_category(category: str) -> str:
    """Get icon for a given category."""
    category_map = {
        "hypothesis": ICONS["hypothesis"],
        "discovery": ICONS["discover"],
        "search": ICONS["search"],
        "validate": ICONS["validate"],
        "dashboard": ICONS["dashboard"],
        "settings": ICONS["settings"],
        "triz": ICONS["triz"],
        "analogy": ICONS["analogy"],
        "c4": ICONS["c4"],
        "graph": ICONS["graph"],
        "paper": ICONS["paper"],
        "patent": ICONS["patent"],
        "reference": ICONS["reference"],
        "experiment": ICONS["experiment"],
        "agent": ICONS["agent"],
        "multi_agent": ICONS["multi_agent"],
    }
    return category_map.get(category.lower(), ICONS["info"])
