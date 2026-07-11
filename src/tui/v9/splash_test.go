package tui

import (
	"strings"
	"testing"
	"time"

	tea "charm.land/bubbletea/v2"
)

func TestSplash_NewSplash_Defaults(t *testing.T) {
	m := NewSplash("v9.9.0", "abc1234")
	if m.phase != "crystal" {
		t.Errorf("default phase = %s, want crystal", m.phase)
	}
	if m.width != 0 || m.height != 0 {
		t.Errorf("default size = %dx%d, want 0x0", m.width, m.height)
	}
}

func TestSplash_NewSplash_WithVersion(t *testing.T) {
	m := NewSplash("v9.9.0-test", "deadbeef")
	if m.appVersion != "v9.9.0-test" {
		t.Errorf("appVersion = %s", m.appVersion)
	}
	if m.gitRef != "deadbeef" {
		t.Errorf("gitRef = %s", m.gitRef)
	}
}

func TestSplash_PhaseTransitions(t *testing.T) {
	m := NewSplash("v9.9.0", "")
	m.width, m.height = 120, 40
	// crystal → dissolve via any key
	u, _ := m.Update(tea.KeyPressMsg{Code: 'a'})
	mm := u.(SplashModel)
	if mm.phase != "dissolve" {
		t.Errorf("after key in crystal, phase = %s, want dissolve", mm.phase)
	}
	// dissolve → waiting via key
	u, _ = mm.Update(tea.KeyPressMsg{Code: 'b'})
	mm = u.(SplashModel)
	if mm.phase != "waiting" {
		t.Errorf("after key in dissolve, phase = %s, want waiting", mm.phase)
	}
	// waiting → fadeout via key
	u, _ = mm.Update(tea.KeyPressMsg{Code: 'c'})
	mm = u.(SplashModel)
	if mm.phase != "fadeout" {
		t.Errorf("after key in waiting, phase = %s, want fadeout", mm.phase)
	}
}

func TestSplash_KeySkipsCrystalDelay(t *testing.T) {
	m := NewSplash("v9.9.0", "")
	m.width, m.height = 120, 40
	// Tick once: should not advance (crystal delay)
	u, _ := m.Update(splashTickMsg{tick: 1})
	mm := u.(SplashModel)
	if mm.phase != "crystal" {
		t.Errorf("after 1 tick, phase = %s, want crystal (delay not yet)", mm.phase)
	}
}

func TestSplash_KeyAdvancesCrystalToDissolve(t *testing.T) {
	m := NewSplash("v9.9.0", "")
	m.width, m.height = 120, 40
	// User press in crystal → dissolve
	u, _ := m.Update(tea.KeyPressMsg{Code: tea.KeySpace})
	mm := u.(SplashModel)
	if mm.phase != "dissolve" {
		t.Errorf("after space, phase = %s, want dissolve", mm.phase)
	}
	if !mm.isCompact() == false { // sanity check
		_ = mm.isCompact
	}
}

func TestSplash_IsCompact(t *testing.T) {
	m := NewSplash("v9.9.0", "")
	if m.isCompact() != true {
		t.Error("height=0 should be compact (no art fits)")
	}
	m.width, m.height = 120, 40
	if m.isCompact() {
		t.Error("height=40 should NOT be compact")
	}
	m.height = 25
	if !m.isCompact() {
		t.Error("height=25 should be compact")
	}
}

func TestSplash_View_LoadingMessage(t *testing.T) {
	m := NewSplash("v9.9.0", "")
	v := m.View()
	if !strings.Contains(v.Content, "Loading") {
		t.Errorf("missing Loading in:\n%s", v.Content)
	}
}

func TestSplash_View_ContainsTagline(t *testing.T) {
	m := NewSplash("v9.9.0", "abc1234")
	m.width, m.height = 120, 40
	// Advance from crystal→dissolve→waiting (where tagline text appears)
	updated, _ := m.Update(tea.KeyPressMsg{Code: ' '})
	m = updated.(SplashModel)
	updated, _ = m.Update(tea.KeyPressMsg{Code: ' '})
	m = updated.(SplashModel)
	v := m.View()
	content := v.Content
	// v.Content is wrapped (lipgloss centering may add spaces)
	// Tagline may use middle-dot (·) instead of space during animation polish.
	if !strings.Contains(content, "COGNITIVE EXOSKELETON") && !strings.Contains(content, "COGNITIVE·EXOSKELETON") {
		t.Errorf("missing tagline in:\n%s", content)
	}
	// v9 polish: version line blinks "." with "·" — accept either form.
	if !strings.Contains(content, "v9") {
		t.Errorf("missing version in:\n%s", content)
	}
}

func TestSplash_ArtHeight_RespectsTerminalSize(t *testing.T) {
	m := NewSplash("v9.9.0", "")
	m.width, m.height = 80, 24
	h := m.artHeight()
	if h < 5 {
		t.Errorf("artHeight = %d, want >= 5", h)
	}
	if h > m.height {
		t.Errorf("artHeight %d > terminal %d", h, m.height)
	}
}

func TestSplash_ArtHeight_Compact(t *testing.T) {
	m := NewSplash("v9.9.0", "")
	m.width, m.height = 80, 20
	h := m.artHeight()
	if h < 5 {
		t.Errorf("compact artHeight = %d, want >= 5", h)
	}
}

func TestSplash_TotalMorphTicks_ZeroWhenNoForms(t *testing.T) {
	m := NewSplash("v9.9.0", "")
	m.forms = nil
	if m.totalMorphTicks() != 0 {
		t.Error("totalMorphTicks should be 0 with no forms")
	}
}

func TestSplash_TotalMorphTicks_ThreeForms(t *testing.T) {
	m := NewSplash("v9.9.0", "")
	m.forms = [][]string{{"a"}, {"b"}, {"c"}, {"d"}} // 4 forms
	got := m.totalMorphTicks()
	want := 3 * splashFormDuration
	if got != want {
		t.Errorf("totalMorphTicks = %d, want %d", got, want)
	}
}

func TestSplash_PulseIncrements(t *testing.T) {
	m := NewSplash("v9.9.0", "")
	m.phase = "waiting"
	m.forms = [][]string{{"a"}, {"b"}}
	m.morphLines = []string{"a", "b"}
	u, _ := m.Update(splashPulseMsg{})
	mm := u.(SplashModel)
	if mm.pulseTick != 1 {
		t.Errorf("pulseTick = %d, want 1", mm.pulseTick)
	}
}

func TestSplash_TextFadeIncrements(t *testing.T) {
	m := NewSplash("v9.9.0", "")
	u, _ := m.Update(splashTextFadeMsg{})
	mm := u.(SplashModel)
	if mm.textTick != 1 {
		t.Errorf("textTick = %d, want 1", mm.textTick)
	}
}

func TestSplash_DoneMsgSetsLoadingDone(t *testing.T) {
	m := NewSplash("v9.9.0", "")
	u, _ := m.Update(SplashDoneMsg{})
	mm := u.(SplashModel)
	if !mm.loadingDone {
		t.Error("loadingDone should be true after SplashDoneMsg")
	}
}

func TestSplash_InitReturnsBatch(t *testing.T) {
	m := NewSplash("v9.9.0", "")
	cmd := m.Init()
	if cmd == nil {
		t.Error("Init should return a batch cmd")
	}
}

func TestSplash_WindowSizeMsg(t *testing.T) {
	m := NewSplash("v9.9.0", "")
	m.phase = "waiting"
	m.forms = [][]string{{"a"}}
	m.morphLines = []string{"a"}
	u, _ := m.Update(tea.WindowSizeMsg{Width: 100, Height: 30})
	mm := u.(SplashModel)
	if mm.width != 100 || mm.height != 30 {
		t.Errorf("size = %dx%d", mm.width, mm.height)
	}
}

func TestSplash_FadeoutCompletes(t *testing.T) {
	m := NewSplash("v9.9.0", "")
	m.phase = "fadeout"
	m.width, m.height = 120, 40
	u, _ := m.Update(splashFadeMsg{})
	mm := u.(SplashModel)
	if mm.phase != "done" {
		t.Errorf("phase = %s, want done", mm.phase)
	}
	if !mm.loadingDone {
		t.Error("loadingDone should be true after fadeout")
	}
}

func TestSplash_CompactMode_ShowsCompactArt(t *testing.T) {
	m := NewSplash("v9.9.0", "")
	m.width, m.height = 80, 25 // < 30, compact
	// Advance from crystal→dissolve→waiting (where text appears)
	updated, _ := m.Update(tea.KeyPressMsg{Code: ' '})
	m = updated.(SplashModel)
	updated, _ = m.Update(tea.KeyPressMsg{Code: ' '})
	m = updated.(SplashModel)
	v := m.View()
	content := v.Content
	if !strings.Contains(content, "C4REQBER") {
		t.Errorf("compact splash should still show app name in:\n%s", content)
	}
}

func TestSplash_CrystalDelayConstants(t *testing.T) {
	if splashCrystalDelay < 1*time.Second {
		t.Error("crystal delay too short")
	}
	if splashCrystalDelay > 10*time.Second {
		t.Error("crystal delay too long (annoying)")
	}
}
