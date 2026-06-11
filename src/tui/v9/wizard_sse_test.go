package tui

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"github.com/figuramax/c4reqber-tui-v9/persist"
)

func TestWizard_StartsInactive(t *testing.T) {
	w := NewWizardState()
	if w.Active() {
		t.Error("wizard should start inactive")
	}
}

func TestWizard_Show(t *testing.T) {
	w := NewWizardState()
	w.Show()
	if !w.Active() {
		t.Error("Show should activate wizard")
	}
	if w.Step() != 0 {
		t.Errorf("first step should be 0, got %d", w.Step())
	}
}

func TestWizard_Next_Advances(t *testing.T) {
	w := NewWizardState()
	w.Show()
	w.Next()
	if w.Step() != 1 {
		t.Errorf("after Next, step = %d", w.Step())
	}
	w.Next()
	if w.Step() != 2 {
		t.Errorf("after 2 Nexts, step = %d", w.Step())
	}
}

func TestWizard_Next_StopsAt3(t *testing.T) {
	w := NewWizardState()
	w.Show()
	for i := 0; i < 10; i++ {
		w.Next()
	}
	if w.Step() != 3 {
		t.Errorf("Next should stop at 3, got %d", w.Step())
	}
}

func TestWizard_Hide(t *testing.T) {
	w := NewWizardState()
	w.Show()
	w.Hide()
	if w.Active() {
		t.Error("Hide should deactivate wizard")
	}
}

func TestWizard_Done(t *testing.T) {
	w := NewWizardState()
	w.Show()
	w.Done()
	if w.Active() {
		t.Error("Done should deactivate")
	}
	if w.Step() != 3 {
		t.Errorf("Done should set step to 3, got %d", w.Step())
	}
}

func TestWizard_RenderContainsTitle(t *testing.T) {
	out := RenderWizard(120, 40)
	if !strings.Contains(out, "wizard") || !strings.Contains(out, "Welcome") {
		t.Errorf("missing wizard content in:\n%s", out)
	}
}

func TestReconnectPolicy_Defaults(t *testing.T) {
	p := DefaultReconnectPolicy()
	if p.MaxAttempts != 0 {
		t.Errorf("MaxAttempts = %d, want 0 (infinite)", p.MaxAttempts)
	}
	if p.InitialDelay != 500*time.Millisecond {
		t.Errorf("InitialDelay = %v", p.InitialDelay)
	}
	if p.MaxDelay != 30*time.Second {
		t.Errorf("MaxDelay = %v", p.MaxDelay)
	}
	if p.Multiplier != 2.0 {
		t.Errorf("Multiplier = %v", p.Multiplier)
	}
}

func TestSSEState_NextDelay_Exponential(t *testing.T) {
	p := ReconnectPolicy{
		MaxAttempts:  5,
		InitialDelay: 100 * time.Millisecond,
		MaxDelay:     1 * time.Second,
		Multiplier:   2.0,
	}
	s := NewSSEState(p, nil)
	// First call: 100ms
	d1 := s.NextDelay()
	if d1 != 100*time.Millisecond {
		t.Errorf("d1 = %v", d1)
	}
	// Second: 200ms
	d2 := s.NextDelay()
	if d2 != 200*time.Millisecond {
		t.Errorf("d2 = %v", d2)
	}
	// Third: 400ms
	d3 := s.NextDelay()
	if d3 != 400*time.Millisecond {
		t.Errorf("d3 = %v", d3)
	}
	// Fourth: 800ms
	d4 := s.NextDelay()
	if d4 != 800*time.Millisecond {
		t.Errorf("d4 = %v", d4)
	}
	// Fifth: 1600ms (but capped at 1s)
	d5 := s.NextDelay()
	if d5 != 1*time.Second {
		t.Errorf("d5 = %v, want 1s (capped)", d5)
	}
	// Sixth: should be 0 (exhausted)
	d6 := s.NextDelay()
	if d6 != 0 {
		t.Errorf("d6 = %v, want 0 (exhausted)", d6)
	}
}

func TestSSEState_Cancel(t *testing.T) {
	p := DefaultReconnectPolicy()
	s := NewSSEState(p, nil)
	s.Cancel()
	if !s.Cancelled() {
		t.Error("Cancel should set cancelled")
	}
	if s.NextDelay() != 0 {
		t.Error("NextDelay should return 0 after cancel")
	}
}

func TestSSEState_AttemptsCounter(t *testing.T) {
	p := DefaultReconnectPolicy()
	s := NewSSEState(p, nil)
	if s.Attempts() != 0 {
		t.Error("attempts should start at 0")
	}
	s.NextDelay()
	s.NextDelay()
	if s.Attempts() != 2 {
		t.Errorf("attempts = %d, want 2", s.Attempts())
	}
}

func TestSSEState_InfinitePolicy(t *testing.T) {
	p := DefaultReconnectPolicy() // MaxAttempts = 0 = infinite
	s := NewSSEState(p, nil)
	// Should always return non-zero
	for i := 0; i < 10; i++ {
		if d := s.NextDelay(); d == 0 {
			t.Errorf("infinite policy returned 0 at attempt %d", i)
		}
	}
}

func TestConfig_LoadConfig_AllNewEnvVars(t *testing.T) {
	tmp := t.TempDir()
	t.Setenv("HOME", tmp)
	os.Setenv("C4_LLM_TIER", "C3")
	os.Setenv("C4_COLOR_PROFILE", "protanopia")
	os.Setenv("C4_LANG", "ru")
	defer func() {
		os.Unsetenv("C4_LLM_TIER")
		os.Unsetenv("C4_COLOR_PROFILE")
		os.Unsetenv("C4_LANG")
	}()
	cfg := LoadConfig()
	if cfg.LLMTier != TierC3 {
		t.Errorf("LLMTier = %s", cfg.LLMTier)
	}
	if cfg.ColorProfile != ProfileProtanopia {
		t.Errorf("ColorProfile = %s", cfg.ColorProfile)
	}
	if cfg.Lang != "ru" {
		t.Errorf("Lang = %s", cfg.Lang)
	}
}

func TestConfig_String_IncludesTierAndProfile(t *testing.T) {
	cfg := Config{
		APIURL:       "http://test",
		Lang:         "en",
		DreamIdle:    60,
		LLMTier:      TierC3,
		ColorProfile: ProfileProtanopia,
	}
	s := cfg.String()
	if !strings.Contains(s, "LLM=C3") {
		t.Errorf("missing LLM in: %s", s)
	}
	if !strings.Contains(s, "Profile=protanopia") {
		t.Errorf("missing Profile in: %s", s)
	}
}

func TestModel_ApplySettings(t *testing.T) {
	tmp := t.TempDir()
	t.Setenv("HOME", tmp)
	// Create a persist store with settings
	store, _ := persist.New(filepath.Join(tmp, "state.json"))
	store.SetSettings(persist.Settings{
		LLMTier:      "C3",
		ColorProfile: "protanopia",
		Lang:         "ru",
	})
	_ = store.Save()
	// Reload
	store2, _ := persist.New(filepath.Join(tmp, "state.json"))
	m := NewAppWithStore("http://test", store2)
	if m.llmTier != TierC3 {
		t.Errorf("tier = %s, want C3", m.llmTier)
	}
	if m.colorProfile != ProfileProtanopia {
		t.Errorf("profile = %s", m.colorProfile)
	}
}

func TestModel_PersistSettings_RoundTrip(t *testing.T) {
	tmp := t.TempDir()
	t.Setenv("HOME", tmp)
	store, _ := persist.New(filepath.Join(tmp, "state.json"))
	m := NewAppWithStore("http://test", store)
	m.llmTier = TierC1
	m.colorProfile = ProfileMonochrome
	m.PersistSettings()
	// Reload
	store2, _ := persist.New(filepath.Join(tmp, "state.json"))
	s := store2.GetSettings()
	if s.LLMTier != "C1" {
		t.Errorf("tier = %s", s.LLMTier)
	}
	if s.ColorProfile != "monochrome" {
		t.Errorf("profile = %s", s.ColorProfile)
	}
}

func TestModel_MarkFirstRunDone(t *testing.T) {
	tmp := t.TempDir()
	t.Setenv("HOME", tmp)
	store, _ := persist.New(filepath.Join(tmp, "state.json"))
	if !store.IsFirstRun() {
		t.Fatal("new store should be first-run")
	}
	store.MarkFirstRunDone()
	_ = store.Save()
	store2, _ := persist.New(filepath.Join(tmp, "state.json"))
	if store2.IsFirstRun() {
		t.Error("after MarkFirstRunDone, should not be first-run")
	}
}

func TestModel_NewAppFresh_DefaultTier(t *testing.T) {
	// Isolate from user's real ~/.config/c4reqber state — NewAppFresh
	// loads from persist.DefaultPath(), which is $HOME-scoped.
	tmp := t.TempDir()
	t.Setenv("HOME", tmp)
	m := NewAppFresh("http://test")
	if m.llmTier != TierC2 {
		t.Errorf("NewAppFresh default tier = %s, want C2", m.llmTier)
	}
	if m.colorProfile != ProfileDefault {
		t.Errorf("NewAppFresh default profile = %s", m.colorProfile)
	}
	if m.wizard == nil {
		t.Error("wizard should be wired in NewAppFresh")
	}
}

func TestModel_NewAppFresh_EmptyFeed(t *testing.T) {
	m := NewAppFresh("http://test")
	if len(m.feed) == 0 {
		t.Error("NewAppFresh should have empty card")
	}
	if m.feed[0].Kind != CardEmpty {
		t.Errorf("first card should be CardEmpty, got %v", m.feed[0].Kind)
	}
}

func TestPersist_AppFresh_NoLoad(t *testing.T) {
	// Set persist state to have C3, but NewAppFresh should not load
	tmp := t.TempDir()
	t.Setenv("HOME", tmp)
	store, _ := persist.New(filepath.Join(tmp, "state.json"))
	store.SetSettings(persist.Settings{LLMTier: "C3"})
	_ = store.Save()
	// We can't test NewAppFresh avoiding load because the env HOME points to tmp
	// but the in-memory store isn't passed. So we test it doesn't take effect:
	m := NewAppFresh("http://test")
	if m.llmTier == TierC3 {
		t.Error("NewAppFresh should ignore persist state")
	}
}
