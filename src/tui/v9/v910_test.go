package tui

import (
	"fmt"
	"strings"
	"testing"
	"time"

	tea "charm.land/bubbletea/v2"

	"github.com/figuramax/c4reqber-tui-v9/demo"
)

func TestAchievementOverlay_ShowAndHide(t *testing.T) {
	a := NewAchievements()
	a.ShowOverlay("🏆 Test", 100*time.Millisecond)
	if !a.OverlayActive() {
		t.Error("overlay should be active after ShowOverlay")
	}
	time.Sleep(150 * time.Millisecond)
	if a.OverlayActive() {
		t.Error("overlay should auto-dismiss after duration")
	}
}

func TestAchievementOverlay_ManualHide(t *testing.T) {
	a := NewAchievements()
	a.ShowOverlay("Test", 10*time.Second)
	if !a.OverlayActive() {
		t.Error("overlay should be active")
	}
	a.HideOverlay()
	if a.OverlayActive() {
		t.Error("HideOverlay should immediately clear")
	}
}

func TestAchievementOverlay_RendersTitle(t *testing.T) {
	a := NewAchievements()
	a.ShowOverlay("Test", time.Hour)
	out := renderAchievementOverlay(*a, 120, 40)
	if !strings.Contains(out, "Achievement") {
		t.Errorf("missing 'Achievement' in overlay:\n%s", out)
	}
}

func TestAchievementOverlay_LastUnlockHighlight(t *testing.T) {
	a := NewAchievements()
	a.Items[0].Unlocked = true
	a.Items[0].UnlockedAt = time.Now()
	a.Unlocked = 1
	a.LastUnlock = a.Items[0].UnlockedAt
	out := renderAchievementOverlay(*a, 120, 40)
	// Derive the expected total from the system so the assertion doesn't drift
	// each time an achievement is added (was "1 / 7", now 11 with sim ones).
	want := fmt.Sprintf("1 / %d", a.Total)
	if !strings.Contains(out, want) {
		t.Errorf("missing progress %q in:\n%s", want, out)
	}
}

func TestSettingsMenu_OpensAndCloses(t *testing.T) {
	m := NewAppFresh("http://test")
	m.width, m.height = 120, 40
	if m.settingsVisible {
		t.Fatal("settings should default closed")
	}
	u, _ := m.Update(tea.KeyPressMsg{Code: ',', Mod: tea.ModCtrl})
	mm := u.(*model)
	if !mm.settingsVisible {
		t.Error("Ctrl+, should open settings")
	}
	u, _ = mm.Update(tea.KeyPressMsg{Code: ',', Mod: tea.ModCtrl})
	mm = u.(*model)
	if mm.settingsVisible {
		t.Error("Ctrl+, again should close settings")
	}
}

func TestSettingsMenu_ArrowKeysNavigate(t *testing.T) {
	m := NewAppFresh("http://test")
	m.settingsVisible = true
	m.width, m.height = 120, 40
	if m.settingsCursor != 0 {
		t.Fatal("cursor should start at 0")
	}
	u, _ := m.Update(tea.KeyPressMsg{Code: tea.KeyDown})
	mm := u.(*model)
	if mm.settingsCursor != 1 {
		t.Errorf("after down, cursor = %d", mm.settingsCursor)
	}
	u, _ = mm.Update(tea.KeyPressMsg{Code: tea.KeyUp})
	mm = u.(*model)
	if mm.settingsCursor != 0 {
		t.Errorf("after up, cursor = %d", mm.settingsCursor)
	}
	u, _ = mm.Update(tea.KeyPressMsg{Code: tea.KeyUp})
	mm = u.(*model)
	if mm.settingsCursor != 0 {
		t.Errorf("up at top, cursor = %d, want 0", mm.settingsCursor)
	}
}

func TestSettingsMenu_ContainsAllOptions(t *testing.T) {
	m := NewAppFresh("http://test")
	rows := m.CurrentSettings()
	if len(rows) < 5 {
		t.Errorf("settings should have >= 5 rows, got %d", len(rows))
	}
	keys := make([]string, len(rows))
	for i, r := range rows {
		keys[i] = r.Key
	}
	wantKeys := []string{"settings.llm_tier", "settings.color_profile", "settings.dream_idle", "settings.lang", "settings.api_url"}
	for _, want := range wantKeys {
		found := false
		for _, k := range keys {
			if k == want {
				found = true
				break
			}
		}
		if !found {
			t.Errorf("missing setting key %q in %v", want, keys)
		}
	}
}

func TestSettingsMenu_RenderContainsCurrentValues(t *testing.T) {
	rows := []SettingsRow{
		{Key: "settings.test", Value: "TEST_VALUE", Description: "settings.test.desc"},
	}
	out := RenderSettingsMenuWith(rows, 0, 120, 40)
	if !strings.Contains(out, "TEST_VALUE") {
		t.Errorf("missing value in:\n%s", out)
	}
}

func TestSettingsMenu_CursorHighlight(t *testing.T) {
	rows := []SettingsRow{
		{Key: "k1", Value: "v1", Description: "d1"},
		{Key: "k2", Value: "v2", Description: "d2"},
		{Key: "k3", Value: "v3", Description: "d3"},
	}
	out := RenderSettingsMenuWith(rows, 1, 120, 40)
	if !strings.Contains(out, "▶") {
		t.Errorf("missing cursor marker in:\n%s", out)
	}
}

func TestMouseWheel_ScrollsFeed(t *testing.T) {
	m := NewAppFresh("http://test")
	m.width, m.height = 120, 40
	u, _ := m.Update(tea.MouseWheelMsg{X: 10, Y: 5, Button: tea.MouseWheelUp})
	mm := u.(*model)
	_ = mm
	u, _ = mm.Update(tea.MouseWheelMsg{X: 10, Y: 5, Button: tea.MouseWheelDown})
	mm = u.(*model)
	_ = mm
}

func TestArrowUpDown_OutsideSettings_ScrollsFeed(t *testing.T) {
	m := NewAppFresh("http://test")
	m.width, m.height = 120, 40
	u, _ := m.Update(tea.KeyPressMsg{Code: tea.KeyUp})
	mm := u.(*model)
	if mm.settingsCursor != 0 {
		t.Error("cursor shouldn't change when settings not visible")
	}
	u, _ = mm.Update(tea.KeyPressMsg{Code: tea.KeyDown})
	mm = u.(*model)
	if mm.settingsCursor != 0 {
		t.Error("cursor shouldn't change when settings not visible")
	}
}

func TestDemo_StoryCRISPR(t *testing.T) {
	s := demo.Story("crispr", "test topic")
	if s.Topic == "" {
		t.Error("story should have topic")
	}
	if len(s.Events) < 5 {
		t.Errorf("CRISPR story should have >= 5 events, got %d", len(s.Events))
	}
}

func TestDemo_StorySleep(t *testing.T) {
	s := demo.Story("sleep", "test topic")
	// Find the ALREADY_SHIFTED verdict event
	found := false
	for _, e := range s.Events {
		if strings.Contains(e.Body, "ALREADY_SHIFTED") {
			found = true
			break
		}
	}
	if !found {
		t.Error("sleep story should contain ALREADY_SHIFTED verdict")
	}
}

func TestDemo_StoryLang(t *testing.T) {
	s := demo.Story("lang", "test topic")
	found := false
	for _, e := range s.Events {
		if strings.Contains(e.Body, "SHIFTED") {
			found = true
			break
		}
	}
	if !found {
		t.Error("lang story should contain SHIFTED verdict")
	}
}

func TestDemo_StoryUnknownFallsBackToDefault(t *testing.T) {
	s := demo.Story("nonexistent", "test topic")
	if s.Topic == "" {
		t.Error("default story should still have topic")
	}
}
