package tui

import (
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/figuramax/c4reqber-tui-v9/i18n"
	"github.com/figuramax/c4reqber-tui-v9/persist"
)

// TestLangAuthoritativeAcrossDiscovery proves that an explicit C4_LANG=en wins
// over any persisted state.lang, and that the UI language does NOT flip to
// another language (e.g. ru) when a discovery completes and achievements fire.
//
// This guards the regression where a stale build rendered the achievement card
// in Russian ("🏆 Первое открытие") despite C4_LANG=en and state.lang=en.
func TestLangAuthoritativeAcrossDiscovery(t *testing.T) {
	orig := i18n.GetLang()
	defer i18n.SetLang(orig)

	t.Setenv("C4_LANG", "en")

	// Fresh, hermetic on-disk config with an explicit persisted lang=ru to
	// prove C4_LANG overrides it.
	tmp := t.TempDir()
	cfgDir := filepath.Join(tmp, ".c4reqber")
	if err := os.MkdirAll(cfgDir, 0o755); err != nil {
		t.Fatal(err)
	}
	t.Setenv("HOME", tmp)
	t.Setenv("C4REQBER_CONFIG", cfgDir)
	state := `{"langs_seen":["ru"],"achievements":[],"discovery_count":0,"llm_tier":"C2","color_profile":"default","lang":"ru","first_run":false}`
	if err := os.WriteFile(filepath.Join(cfgDir, "tui-v9-state.json"), []byte(state), 0o644); err != nil {
		t.Fatal(err)
	}

	m := NewApp("http://127.0.0.1:8000")
	if got := i18n.GetLang(); got != i18n.LangEN {
		t.Fatalf("after NewApp: lang=%q, want en (C4_LANG must override persisted lang=ru)", got)
	}

	// Simulate a discovery completing and triggering achievements.
	m.startedAt = m.startedAt.Add(0) // keep non-zero guard irrelevant
	m.completedDisc = 1
	m.checkAchievements()

	if got := i18n.GetLang(); got != i18n.LangEN {
		t.Fatalf("after discovery/achievements: lang=%q, want en (must not flip to ru)", got)
	}

	// The achievement card must be English, not Russian.
	var foundAchievement bool
	for _, c := range m.feed {
		if strings.HasPrefix(c.Title, "🏆 ") {
			foundAchievement = true
			if strings.Contains(c.Title, "Первое открытие") {
				t.Fatalf("achievement card rendered in Russian: %q", c.Title)
			}
			if !strings.Contains(c.Title, "First Discovery") {
				t.Fatalf("achievement card not English: %q", c.Title)
			}
		}
	}
	if !foundAchievement {
		t.Fatal("no achievement card appended after FirstDiscovery unlock")
	}
	_ = persist.DefaultPath
}
