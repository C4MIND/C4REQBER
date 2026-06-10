package tui

import (
	"strings"
	"testing"
	"time"

	tea "charm.land/bubbletea/v2"

	"github.com/figuramax/c4reqber-tui-v9/i18n"
	"github.com/figuramax/c4reqber-tui-v9/persist"
	"github.com/figuramax/c4reqber-tui-v9/telemetry"
)

func TestTelemetryPanel_RenderContainsSnapshotStats(t *testing.T) {
	tel := telemetry.New()
	tel.IncMode("DISCOVER")
	tel.IncMode("FLASH")
	tel.IncLang("en")
	tel.IncDiscovery()
	tel.IncDiscoveryResult(true, 12.3)
	tel.AddCost(0.045)
	out := renderTelemetry(tel.Get(), 120, "C2", "default")
	if !strings.Contains(out, "DISCOVER:1") {
		t.Errorf("missing DISCOVER counter in:\n%s", out)
	}
	if !strings.Contains(out, "en:1") {
		t.Errorf("missing lang counter in:\n%s", out)
	}
	if !strings.Contains(out, "cost=$") {
		t.Errorf("missing cost in:\n%s", out)
	}
}

func TestTelemetryPanel_RenderEmpty(t *testing.T) {
	tel := telemetry.New()
	out := renderTelemetry(tel.Get(), 80, "C2", "default")
	if out == "" {
		t.Error("renderTelemetry should return non-empty for empty stats")
	}
}

func TestCtrlT_TogglesTelemetryPanel(t *testing.T) {
	m := NewApp("http://test")
	m.width, m.height = 120, 40
	if m.showTelemetry {
		t.Fatal("showTelemetry should default false")
	}
	u, _ := m.Update(tea.KeyPressMsg{Code: 't', Mod: tea.ModCtrl})
	mm := u.(*model)
	if !mm.showTelemetry {
		t.Error("Ctrl+T should enable showTelemetry")
	}
	u, _ = mm.Update(tea.KeyPressMsg{Code: 't', Mod: tea.ModCtrl})
	mm = u.(*model)
	if mm.showTelemetry {
		t.Error("Ctrl+T twice should disable showTelemetry")
	}
}

func TestTelemetryPanel_AppearsInViewWhenEnabled(t *testing.T) {
	m := NewApp("http://test")
	m.width, m.height = 120, 40
	if m.tel == nil {
		t.Fatal("tel should be wired in NewApp")
	}
	m.tel.IncMode("DISCOVER")
	m.showTelemetry = true
	v := m.View()
	content := v.Content
	if !strings.Contains(content, "Telemetry") {
		t.Errorf("telemetry panel missing in view when enabled:\n%s", content)
	}
}

func TestTelemetryPanel_HiddenByDefault(t *testing.T) {
	m := NewApp("http://test")
	m.width, m.height = 120, 40
	v := m.View()
	content := v.Content
	if strings.Contains(content, "📊 Telemetry") {
		t.Errorf("telemetry panel should be hidden by default:\n%s", content)
	}
}

func TestNewAppWithStore_RestoresLangsFromDisk(t *testing.T) {
	tmp := t.TempDir() + "/state.json"
	store, err := persist.New(tmp)
	if err != nil {
		t.Fatal(err)
	}
	store.AddLangSeen("en")
	store.AddAchievement(0) // first discovery
	if err := store.Save(); err != nil {
		t.Fatal(err)
	}
	// reload
	store2, err := persist.New(tmp)
	if err != nil {
		t.Fatal(err)
	}
	m := NewAppWithStore("http://test", store2)
	if !m.langsSeen["en"] {
		t.Error("NewAppWithStore should restore langsSeen from disk")
	}
}

func TestTelemetry_TabIncrementsMode(t *testing.T) {
	m := NewApp("http://test")
	if m.tel.Get().ModeUseCount["FLASH"] != 0 {
		t.Fatal("FLASH should not be counted yet")
	}
	u, _ := m.Update(tea.KeyPressMsg{Code: tea.KeyTab})
	mm := u.(*model)
	if mm.tel.Get().ModeUseCount["FLASH"] != 1 {
		t.Errorf("expected FLASH:1 after tab, got %v", mm.tel.Get().ModeUseCount)
	}
}

func TestTelemetry_LShiftIncrementsLang(t *testing.T) {
	// Save+restore global lang
	original := i18n.GetLang()
	defer SetLang(original)
	SetLang(i18n.LangEN)
	m := NewAppFresh("http://test")
	if m.tel.Get().LangUseCount["ru"] != 0 {
		t.Fatal("ru should not be counted yet")
	}
	u, _ := m.Update(tea.KeyPressMsg{Code: 'L', Mod: tea.ModShift})
	mm := u.(*model)
	if mm.tel.Get().LangUseCount["ru"] != 1 {
		t.Errorf("expected ru:1 after Shift+L, got %v", mm.tel.Get().LangUseCount)
	}
}

func TestTelemetry_EscIncrementsAbort(t *testing.T) {
	m := NewApp("http://test")
	m.running = true
	m.jobID = "test"
	m.startedAt = time.Now()
	u, _ := m.Update(tea.KeyPressMsg{Code: tea.KeyEsc})
	mm := u.(*model)
	if mm.tel.Get().DiscoveriesAbort != 1 {
		t.Errorf("expected abort=1 after Esc, got %d", mm.tel.Get().DiscoveriesAbort)
	}
}

func TestPersist_ShiftL_SavesLangToStore(t *testing.T) {
	// Note: i18n.GetLang() is global state. To make this test deterministic
	// regardless of prior test order, we cycle through all 7 langs to ensure
	// every lang is recorded in the store, then assert at least 5 are present.
	tmp := t.TempDir() + "/state.json"
	store, err := persist.New(tmp)
	if err != nil {
		t.Fatal(err)
	}
	m := NewAppWithStore("http://test", store)
	// Cycle 7 times — full revolution
	cur := m
	for i := 0; i < 7; i++ {
		u, _ := cur.Update(tea.KeyPressMsg{Code: 'L', Mod: tea.ModShift})
		cur = u.(*model)
	}
	snap := cur.store.Snapshot()
	if len(snap.LangsSeen) < 5 {
		t.Errorf("expected at least 5 langs persisted, got %d (%v)", len(snap.LangsSeen), snap.LangsSeen)
	}
	// All 7 cycle positions should be in the store
	all7 := []string{"en", "ru", "zh", "ja", "de", "ar", "hi"}
	for _, want := range all7 {
		found := false
		for _, have := range snap.LangsSeen {
			if have == want {
				found = true
				break
			}
		}
		if !found {
			t.Errorf("expected %q in store, got %v", want, snap.LangsSeen)
		}
	}
}
