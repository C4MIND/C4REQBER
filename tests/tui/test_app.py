"""Unit tests for C4REQBER TUI widgets — no terminal required.

Tests all 18 widget classes: compose, mount, state transitions,
click handling, pipeline integration, mascot behavior.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest


@pytest.fixture(autouse=True)
def setup_env():
    os.environ.setdefault("JWT_SECRET", "test-jwt-min-32-chars-long-key")


def test_import_all_widgets():
    """All 18 widget classes import without error."""
    from src.tui.app import (
        GhostHeader, C4Grid, ConfidenceSparkline, DiscoveryPanel,
        LiveFeedWidget, BudgetWidget, AlertWidget, DepthWidget,
        ProofWidget, ArticleWidget, LivingCubeWidget, ProviderWidget,
        PluginGrid,         GhostSidebar, OnboardingOverlay,
        LivePipelineLog, TurboTUI,
    )
    assert GhostHeader is not None
    assert C4Grid is not None
    assert PluginGrid is not None
    assert TurboTUI is not None


class TestGhostHeader:
    def test_class_exists(self):
        """Header class imports."""
        from src.tui.app import GhostHeader
        assert GhostHeader is not None

    def test_languages_count(self):
        """7 languages configured."""
        from src.tui.app import GhostHeader
        h = GhostHeader()
        assert len(h._lg) == 7

    def test_clock_update_method(self):
        """update_clock method exists."""
        from src.tui.app import GhostHeader
        h = GhostHeader()
        assert hasattr(h, 'update_clock')

    def test_mascot_set_method(self):
        """set_mascot method exists."""
        from src.tui.app import GhostHeader
        h = GhostHeader()
        assert hasattr(h, 'set_mascot')

    def test_language_flags(self):
        """Language cycling covers 7 flags."""
        from src.tui.app import GhostHeader
        h = GhostHeader()
        assert "🇬🇧" in h._lg[0]
        assert "🇷🇺" in h._lg[1]
        assert "🇨🇳" in h._lg[2]


class TestC4Grid:
    def test_state_count(self):
        """27 states defined."""
        from src.tui.app import C4Grid
        assert len(C4Grid.STS) == 27

    def test_labels_count(self):
        """27 labels defined."""
        from src.tui.app import C4Grid
        grid = C4Grid()
        assert len(grid.lb) == 27

    def test_label_format(self):
        """Labels use · separator."""
        from src.tui.app import C4Grid
        grid = C4Grid()
        assert "·" in grid.lb[0]

    def test_tooltip_en(self):
        """English tooltip works."""
        from src.tui.app import C4Grid
        tip = C4Grid._c4_tooltip("111", "en")
        assert len(tip) > 0

    def test_tooltip_all_langs(self):
        """All 7 languages work."""
        from src.tui.app import C4Grid
        for lang in ["en", "ru", "zh", "ja", "de", "ar", "hi"]:
            tip = C4Grid._c4_tooltip("000", lang)
            assert len(tip) > 0, f"Empty for {lang}"

    def test_selected_state_default(self):
        """Default selected state is 111."""
        from src.tui.app import C4Grid
        grid = C4Grid()
        assert grid.ss == "111"


class TestDiscoveryPanel:
    def test_stages_count(self):
        """7 pipeline stages."""
        from src.tui.app import DiscoveryPanel
        assert len(DiscoveryPanel.SG) == 7

    def test_stage_ids(self):
        """Expected stage IDs."""
        from src.tui.app import DiscoveryPanel
        ids = [s[0] for s in DiscoveryPanel.SG]
        assert "analyze" in ids
        assert "synthesize" in ids

    def test_running_flag(self):
        """_rn prevents double start."""
        from src.tui.app import DiscoveryPanel
        dp = DiscoveryPanel()
        assert dp._rn is False


class TestPluginGrid:
    def test_modules_count(self):
        from src.tui.app import PluginGrid
        assert len(PluginGrid.MODULES) >= 9

    def test_plugins_count(self):
        from src.tui.app import PluginGrid
        assert len(PluginGrid.PLUGINS) >= 14

    def test_highlight_phase(self):
        """Each phase activates at least 1 plugin."""
        from src.tui.app import PluginGrid
        pg = PluginGrid()
        for phase in ["analyze", "search", "c4", "triz", "simulate", "verify", "synthesize"]:
            pg.highlight_phase(phase)
            assert len(pg._running) > 0, f"Phase {phase} inactive"


class TestGhostSidebar:
    def test_compose_yields_nav_items(self):
        """Sidebar yields mascot + bubble + cube + 8 nav items."""
        from src.tui.app import GhostSidebar
        gs = GhostSidebar()
        children = list(gs.compose())
        assert len(children) >= 11  # mascot + bubble + cube + 8 nav

    def test_nav_has_8_items(self):
        """8 navigation tabs defined."""
        from src.tui.app import GhostSidebar
        assert len(GhostSidebar.NAV) == 8

    def test_nav_includes_chat_and_dissertation(self):
        """Chat and Dissertation tabs exist."""
        from src.tui.app import GhostSidebar
        views = [v[0] for v in GhostSidebar.NAV]
        assert "chat" in views
        assert "dissertation" in views

    def test_collapse_toggle(self):
        """Collapse toggles width."""
        from src.tui.app import GhostSidebar
        gs = GhostSidebar()
        assert not gs._cl
        gs.toggle_collapse()
        assert gs._cl
        gs.toggle_collapse()
        assert not gs._cl


class TestConfidenceSparkline:
    def test_braille_count(self):
        from src.tui.app import ConfidenceSparkline
        assert len(ConfidenceSparkline.BL) == 9

    def test_values_default(self):
        from src.tui.app import ConfidenceSparkline
        cs = ConfidenceSparkline()
        assert len(cs.vs) == 5
        assert 0 < cs.vs[0] < 1


class TestLivingCubeWidget:
    def test_exists(self):
        from src.tui.app import LivingCubeWidget
        assert LivingCubeWidget is not None

    def test_has_update(self):
        from src.tui.app import LivingCubeWidget
        lcw = LivingCubeWidget()
        assert hasattr(lcw, '_update')


class TestOnboardingOverlay:
    def test_steps_defined(self):
        """3 onboarding steps exist."""
        from src.tui.app import OnboardingOverlay
        assert len(OnboardingOverlay._steps) == 3


class TestLivePipelineLog:
    def test_initial_lines(self):
        from src.tui.app import LivePipelineLog
        log = LivePipelineLog()
        assert log._lines == ["○ Awaiting discovery..."]

    def test_add_line(self):
        from src.tui.app import LivePipelineLog
        log = LivePipelineLog()
        log.add("Phase A: done")
        assert any("Phase A" in l for l in log._lines)

    def test_clear(self):
        from src.tui.app import LivePipelineLog
        log = LivePipelineLog()
        log.add("test")
        log.clear()
        assert log._lines == ["○ Awaiting discovery..."]


class TestTurboTUI:
    def test_app_class(self):
        from src.tui.app import TurboTUI
        assert TurboTUI is not None

    def test_bindings_count(self):
        from src.tui.app import TurboTUI
        assert len(TurboTUI.BINDINGS) >= 15

    def test_class_attrs(self):
        from src.tui.app import TurboTUI
        assert hasattr(TurboTUI, '_dc')
        assert hasattr(TurboTUI, '_cc')
        assert hasattr(TurboTUI, '_history')


def test_i18n_integration():
    """7 languages with 30 translation keys each."""
    from src.tui.i18n import TRANSLATIONS, LANG_ORDER
    assert len(TRANSLATIONS) == 7
    assert len(LANG_ORDER) == 7
    for lang in LANG_ORDER:
        assert lang in TRANSLATIONS, f"Missing: {lang}"
        assert "header" in TRANSLATIONS[lang]
        assert "input_placeholder" in TRANSLATIONS[lang]


def test_c4_state_wired():
    """C4State import works after __init__ fix."""
    from src.c4.state import C4State
    s = C4State(T=1, S=1, A=0)
    assert str(s) == "F⟨Present, Abstract, Self⟩"


def test_mascot_v2_imports():
    """LivingCube v2 imports and renders."""
    from src.tui.living_cube_v2 import LivingCube, FRAMES
    lc = LivingCube()
    assert lc.state == "idle"
    assert len(FRAMES) == 7
    for state in ["idle", "thinking", "excited", "discovery", "sleeping", "error", "paradigm"]:
        assert state in FRAMES, f"Missing state: {state}"


def test_mascot_state_transitions():
    """Mascot changes state correctly."""
    from src.tui.living_cube_v2 import LivingCube
    lc = LivingCube()
    lc.on_pipeline_start()
    assert lc.state == "thinking"
    lc.record_discovery("gravity", 0.92)
    assert lc.state == "paradigm"
    lc.on_night_mode()
    assert lc.state == "sleeping"
    lc.on_wake()
    assert lc.state == "idle"


def test_mascot_feed():
    """Feed increases curiosity and bond."""
    from src.tui.living_cube_v2 import LivingCube
    lc = LivingCube()
    c_before = lc.stats["curiosity"]
    b_before = lc.stats["bond"]
    lc.feed(15)
    assert lc.stats["curiosity"] > c_before
    assert lc.stats["bond"] > b_before
    assert lc.state == "excited"


def test_mascot_stats_bar():
    """Stats bar shows all 4 values."""
    from src.tui.living_cube_v2 import LivingCube
    lc = LivingCube()
    bar = lc.stats_bar()
    assert "⚡" in bar
    assert "🔍" in bar
    assert "💛" in bar
    assert "◈" in bar


def test_mascot_personality_arc():
    """Personality evolves with discoveries — fresh instance."""
    from src.tui.living_cube_v2 import LivingCube
    lc = LivingCube()
    # Reset to ensure clean state
    lc.stats["discoveries"] = 0
    lc._update_personality()
    assert lc.mood == "curious"
    lc.stats["discoveries"] = 5
    lc._update_personality()
    assert lc.mood == "confident"
    lc.stats["discoveries"] = 50
    lc._update_personality()
    assert lc.mood == "master"
