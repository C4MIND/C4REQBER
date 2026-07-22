package tui

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	tea "charm.land/bubbletea/v2"

	"github.com/figuramax/c4reqber-tui-v9/i18n"
	"github.com/figuramax/c4reqber-tui-v9/telemetry"
)

func TestConfig_DefaultConfig(t *testing.T) {
	cfg := DefaultConfig()
	if cfg.APIURL != "http://127.0.0.1:8000" {
		t.Errorf("default APIURL = %s", cfg.APIURL)
	}
	if cfg.Lang != i18n.LangEN {
		t.Errorf("default Lang = %s", cfg.Lang)
	}
	if cfg.DreamIdle != 300 {
		t.Errorf("default DreamIdle = %d", cfg.DreamIdle)
	}
}

func TestConfig_LoadConfig_DefaultsWhenNoEnv(t *testing.T) {
	for _, k := range []string{"C4_API_URL", "C4_LANG", "C4_DREAM_IDLE", "C4_NO_COLOR", "C4_WIDTH", "C4_HEIGHT"} {
		os.Unsetenv(k)
	}
	cfg := LoadConfig()
	if cfg.APIURL != "http://127.0.0.1:8000" {
		t.Errorf("got %s", cfg.APIURL)
	}
}

func TestConfig_LoadConfig_AllEnvVars(t *testing.T) {
	os.Setenv("C4_API_URL", "http://example.com:9000")
	os.Setenv("C4_LANG", "ru")
	os.Setenv("C4_DREAM_IDLE", "60")
	os.Setenv("C4_NO_COLOR", "1")
	os.Setenv("C4_WIDTH", "120")
	os.Setenv("C4_HEIGHT", "40")
	os.Setenv("C4_DREAM_QUOTES", "quote1\nquote2\n  quote3  ")
	os.Setenv("C4_SAVE_HISTORY", "0")
	defer func() {
		for _, k := range []string{"C4_API_URL", "C4_LANG", "C4_DREAM_IDLE", "C4_NO_COLOR", "C4_WIDTH", "C4_HEIGHT", "C4_DREAM_QUOTES", "C4_SAVE_HISTORY"} {
			os.Unsetenv(k)
		}
	}()
	cfg := LoadConfig()
	if cfg.APIURL != "http://example.com:9000" {
		t.Errorf("APIURL = %s", cfg.APIURL)
	}
	if cfg.Lang != i18n.LangRU {
		t.Errorf("Lang = %s", cfg.Lang)
	}
	if cfg.DreamIdle != 60 {
		t.Errorf("DreamIdle = %d", cfg.DreamIdle)
	}
	if !cfg.NoColor {
		t.Error("NoColor should be true")
	}
	if cfg.Width != 120 {
		t.Errorf("Width = %d", cfg.Width)
	}
	if cfg.Height != 40 {
		t.Errorf("Height = %d", cfg.Height)
	}
	if len(cfg.ExtraQuotes) != 3 {
		t.Errorf("ExtraQuotes len = %d", len(cfg.ExtraQuotes))
	}
	if cfg.ExtraQuotes[0] != "quote1" || cfg.ExtraQuotes[2] != "quote3" {
		t.Errorf("ExtraQuotes = %v", cfg.ExtraQuotes)
	}
	if cfg.SaveHistory {
		t.Error("SaveHistory should be false when C4_SAVE_HISTORY=0")
	}
}

func TestConfig_InvalidLang(t *testing.T) {
	os.Setenv("C4_LANG", "klingon")
	defer os.Unsetenv("C4_LANG")
	cfg := LoadConfig()
	if cfg.Lang != i18n.LangEN {
		t.Errorf("invalid lang should fall back to EN, got %s", cfg.Lang)
	}
}

func TestConfig_InvalidDreamIdle(t *testing.T) {
	os.Setenv("C4_DREAM_IDLE", "not-a-number")
	defer os.Unsetenv("C4_DREAM_IDLE")
	cfg := LoadConfig()
	if cfg.DreamIdle != 300 {
		t.Errorf("invalid DreamIdle should use default 300, got %d", cfg.DreamIdle)
	}
}

func TestConfig_String(t *testing.T) {
	cfg := Config{
		APIURL: "http://test", Lang: i18n.LangEN, DreamIdle: 60,
	}
	s := cfg.String()
	if !strings.Contains(s, "API=http://test") {
		t.Errorf("missing API: %s", s)
	}
	if !strings.Contains(s, "Lang=en") {
		t.Errorf("missing Lang: %s", s)
	}
	if !strings.Contains(s, "60s") {
		t.Errorf("missing DreamIdle: %s", s)
	}
}

func TestConfig_ApplyToModel_UpdatesDreamIdle(t *testing.T) {
	m := NewApp("http://test")
	cfg := Config{DreamIdle: 7}
	cfg.ApplyToModel(m)
	if m.dream.idleSeconds != 7 {
		t.Errorf("dream.idleSeconds = %d, want 7", m.dream.idleSeconds)
	}
}

func TestConfig_ApplyToModel_AppendsQuotes(t *testing.T) {
	m := NewApp("http://test")
	orig := len(dreamQuotes)
	cfg := Config{ExtraQuotes: []string{"custom1", "custom2"}}
	cfg.ApplyToModel(m)
	if len(dreamQuotes) != orig+2 {
		t.Errorf("dreamQuotes len = %d, want %d", len(dreamQuotes), orig+2)
	}
}

func TestModel_Tel_NotNil(t *testing.T) {
	m := NewApp("http://test")
	if m.Tel() == nil {
		t.Error("Tel() should not be nil")
	}
}

func TestModel_Config_IncludesDreamIdle(t *testing.T) {
	m := NewApp("http://test")
	cfg := m.Config()
	if cfg.DreamIdle != 300 {
		t.Errorf("Config.DreamIdle = %d, want 300", cfg.DreamIdle)
	}
}

func TestHelp_ToggleWithQuestionMark(t *testing.T) {
	m := NewApp("http://test")
	m.width, m.height = 120, 40
	if m.showHelp {
		t.Fatal("showHelp should default false")
	}
	u, _ := m.Update(tea.KeyPressMsg{Code: '?'})
	mm := u.(*model)
	if !mm.showHelp {
		t.Error("? should enable showHelp")
	}
	// Toggle off
	u, _ = mm.Update(tea.KeyPressMsg{Code: '?'})
	mm = u.(*model)
	if mm.showHelp {
		t.Error("? twice should disable showHelp")
	}
}

func TestHelp_RenderContainsTitle(t *testing.T) {
	// HelpOverlay renders via the global i18n lang; pin EN so a leaked
	// non-English lang from another test can't flip the asserted title.
	original := i18n.GetLang()
	defer SetLang(original)
	SetLang(i18n.LangEN)
	out := HelpOverlay(120, 40)
	if !strings.Contains(out, "Keyboard shortcuts") {
		t.Errorf("missing title in:\n%s", out)
	}
}

func TestHelp_RenderContainsAllSections(t *testing.T) {
	out := HelpOverlay(120, 40)
	for _, section := range []string{"Navigation", "Overlays", "Display"} {
		if !strings.Contains(out, section) {
			t.Errorf("missing section %q in:\n%s", section, out)
		}
	}
}

func TestHelp_RenderContainsTabAndQuit(t *testing.T) {
	out := HelpOverlay(120, 40)
	if !strings.Contains(out, "Tab") {
		t.Error("missing Tab key")
	}
	if !strings.Contains(out, "Ctrl+C") {
		t.Error("missing Ctrl+C key")
	}
}

func TestHistory_SaveTelemetryHistory_CreatesFile(t *testing.T) {
	tmp := t.TempDir()
	t.Setenv("HOME", tmp) // redirect UserHomeDir
	tel := telemetry.New()
	tel.IncMode("DISCOVER")
	tel.IncDiscovery()
	tel.AddCost(0.05)
	cfg := Config{APIURL: "http://test", Lang: i18n.LangEN, DreamIdle: 300}
	saveTelemetryHistory(tel, cfg)
	// Wait briefly for write
	time.Sleep(50 * time.Millisecond)
	// New format: timestamped files (one per run)
	// v9.13.x: unified to ~/.c4reqber
	dir := filepath.Join(tmp, ".c4reqber")
	entries, err := os.ReadDir(dir)
	if err != nil {
		t.Fatalf("history dir not created: %v", err)
	}
	found := false
	for _, e := range entries {
		if strings.HasPrefix(e.Name(), "tui-v9-history-") {
			found = true
			break
		}
	}
	if !found {
		t.Errorf("no timestamped history file in: %v", entries)
	}
}

func TestHistory_SaveTelemetryHistory_NilSafe(t *testing.T) {
	// Should not panic with nil tel
	saveTelemetryHistory(nil, Config{})
	// Just shouldn't crash
}
