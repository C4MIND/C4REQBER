package tui

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	tea "charm.land/bubbletea/v2"
	"github.com/figuramax/c4reqber-tui-v9/telemetry"
)

func TestTier_String(t *testing.T) {
	if TierC1.String() != "C1" {
		t.Errorf("TierC1.String() = %s", TierC1.String())
	}
	if TierC2.String() != "C2" {
		t.Errorf("TierC2.String() = %s", TierC2.String())
	}
	if TierC3.String() != "C3" {
		t.Errorf("TierC3.String() = %s", TierC3.String())
	}
}

func TestTier_ModelFor(t *testing.T) {
	if !strings.Contains(TierC1.ModelFor(), "deepseek") {
		t.Errorf("TierC1 should use deepseek, got %s", TierC1.ModelFor())
	}
	if !strings.Contains(TierC2.ModelFor(), "qwen") {
		t.Errorf("TierC2 should use qwen, got %s", TierC2.ModelFor())
	}
	if !strings.Contains(TierC3.ModelFor(), "claude") {
		t.Errorf("TierC3 should use claude, got %s", TierC3.ModelFor())
	}
}

func TestTier_EstimatedCost(t *testing.T) {
	c1 := TierC1.EstimatedCost()
	c2 := TierC2.EstimatedCost()
	c3 := TierC3.EstimatedCost()
	if !(c1 < c2 && c2 < c3) {
		t.Errorf("cost should increase: C1=%.4f C2=%.4f C3=%.4f", c1, c2, c3)
	}
}

func TestCycleLLMTier(t *testing.T) {
	if CycleLLMTier(TierC1) != TierC2 {
		t.Error("C1 → C2")
	}
	if CycleLLMTier(TierC2) != TierC3 {
		t.Error("C2 → C3")
	}
	if CycleLLMTier(TierC3) != TierC1 {
		t.Error("C3 → C1")
	}
}

func TestTierFromString(t *testing.T) {
	for _, s := range []string{"C1", "c1", "C2", "c3", "C3 "} {
		if _, ok := TierFromString(s); !ok {
			t.Errorf("TierFromString(%q) should succeed", s)
		}
	}
	if _, ok := TierFromString("invalid"); ok {
		t.Error("TierFromString(invalid) should fail")
	}
}

func TestTier_FormatTierBadge(t *testing.T) {
	badge := TierC2.FormatTierBadge()
	for _, want := range []string{"C2", "qwen", "$"} {
		if !strings.Contains(badge, want) {
			t.Errorf("badge %q missing %q", badge, want)
		}
	}
}

func TestCtrlY_CyclesLLMTier(t *testing.T) {
	// Isolate from user's real ~/.config/c4reqber state.
	tmp := t.TempDir()
	t.Setenv("HOME", tmp)
	m := NewAppFresh("http://test")
	if m.llmTier != TierC2 {
		t.Errorf("default tier = %s, want C2", m.llmTier)
	}
	u, _ := m.Update(tea.KeyPressMsg{Code: 'y', Mod: tea.ModCtrl})
	mm := u.(*model)
	if mm.llmTier != TierC3 {
		t.Errorf("after Ctrl+Y, tier = %s, want C3", mm.llmTier)
	}
}

func TestColorProfile_String(t *testing.T) {
	tests := []struct {
		p    ColorProfile
		want string
	}{
		{ProfileDefault, "default"},
		{ProfileHighContrast, "high-contrast"},
		{ProfileProtanopia, "protanopia"},
		{ProfileDeuteranopia, "deuteranopia"},
		{ProfileTritanopia, "tritanopia"},
		{ProfileMonochrome, "monochrome"},
	}
	for _, tt := range tests {
		if got := tt.p.String(); got != tt.want {
			t.Errorf("ColorProfile(%d).String() = %s, want %s", tt.p, got, tt.want)
		}
	}
}

func TestColorProfile_AllProfilesHaveAllKeys(t *testing.T) {
	required := []string{"primary", "success", "warn", "error", "muted", "accent", "highlight", "info"}
	for _, p := range []ColorProfile{ProfileDefault, ProfileHighContrast, ProfileProtanopia, ProfileDeuteranopia, ProfileTritanopia, ProfileMonochrome} {
		cm := ColorsFor(p)
		for _, k := range required {
			if _, ok := cm[k]; !ok {
				t.Errorf("profile %s missing key %q", p, k)
			}
		}
	}
}

func TestProfileFromString(t *testing.T) {
	for s, want := range map[string]ColorProfile{
		"":              ProfileDefault,
		"default":       ProfileDefault,
		"high-contrast": ProfileHighContrast,
		"hc":            ProfileHighContrast,
		"protanopia":    ProfileProtanopia,
		"prot":          ProfileProtanopia,
		"deuteranopia":  ProfileDeuteranopia,
		"deut":          ProfileDeuteranopia,
		"tritanopia":    ProfileTritanopia,
		"trit":          ProfileTritanopia,
		"monochrome":    ProfileMonochrome,
		"mono":          ProfileMonochrome,
		"no-color":      ProfileMonochrome,
	} {
		got, ok := ProfileFromString(s)
		if !ok {
			t.Errorf("ProfileFromString(%q) failed", s)
			continue
		}
		if got != want {
			t.Errorf("ProfileFromString(%q) = %d, want %d", s, got, want)
		}
	}
	if _, ok := ProfileFromString("invalid"); ok {
		t.Error("ProfileFromString(invalid) should fail")
	}
}

func TestHistory_SaveHistoryFile_CreatesTimestampedFile(t *testing.T) {
	tmp := t.TempDir()
	t.Setenv("HOME", tmp)
	tel := telemetry.New()
	tel.IncMode("DISCOVER")
	tel.IncLang("en")
	tel.IncDiscovery()
	tel.IncDiscoveryResult(true, 5.0)
	tel.AddCost(0.012)
	cfg := Config{APIURL: "http://test", Lang: "en", DreamIdle: 300}
	path, err := SaveHistoryFile(tel, cfg)
	if err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(path, "tui-v9-history-") {
		t.Errorf("path should contain timestamp prefix: %s", path)
	}
	if _, err := os.Stat(path); err != nil {
		t.Errorf("history file not created: %v", err)
	}
}

func TestHistory_LoadAllHistoryFiles_ReadsAll(t *testing.T) {
	tmp := t.TempDir()
	t.Setenv("HOME", tmp)
	tel := telemetry.New()
	tel.IncDiscovery()
	cfg := Config{APIURL: "http://test"}
	// Save 3 history files
	for i := 0; i < 3; i++ {
		// Wait a tiny bit so timestamps differ
		time.Sleep(1100 * time.Millisecond) // filename uses seconds
		if _, err := SaveHistoryFile(tel, cfg); err != nil {
			t.Fatal(err)
		}
	}
	files, err := LoadAllHistoryFiles()
	if err != nil {
		t.Fatal(err)
	}
	if len(files) != 3 {
		t.Errorf("got %d files, want 3", len(files))
	}
}

func TestHistory_Aggregate_CombinesAll(t *testing.T) {
	now := time.Now()
	files := []HistoryFile{
		{
			Config:     "test",
			SessionEnd: now,
			Snapshot: telemetry.Snapshot{
				Discoveries: 5, DiscoveriesOK: 4, DiscoveriesFail: 1,
				TotalCost: 0.05, TotalAPICalls: 10, LongestRunSec: 10.0,
				ModeUseCount: map[string]int{"DISCOVER": 3, "FLASH": 2},
				LangUseCount: map[string]int{"en": 3, "ru": 2},
			},
		},
		{
			Config:     "test",
			SessionEnd: now.Add(time.Hour),
			Snapshot: telemetry.Snapshot{
				Discoveries: 3, DiscoveriesOK: 3,
				TotalCost: 0.03, TotalAPICalls: 5, LongestRunSec: 5.0,
				ModeUseCount: map[string]int{"DISCOVER": 2, "TURBO": 1},
				LangUseCount: map[string]int{"en": 1, "zh": 2},
			},
		},
	}
	stats := Aggregate(files)
	if stats.TotalRuns != 2 {
		t.Errorf("TotalRuns = %d", stats.TotalRuns)
	}
	if stats.TotalDiscoveries != 8 {
		t.Errorf("TotalDiscoveries = %d", stats.TotalDiscoveries)
	}
	if stats.TotalOK != 7 {
		t.Errorf("TotalOK = %d", stats.TotalOK)
	}
	if stats.TotalFail != 1 {
		t.Errorf("TotalFail = %d", stats.TotalFail)
	}
	if stats.ModeUseCount["DISCOVER"] != 5 {
		t.Errorf("DISCOVER count = %d", stats.ModeUseCount["DISCOVER"])
	}
	if stats.LangUseCount["en"] != 4 {
		t.Errorf("en count = %d", stats.LangUseCount["en"])
	}
	if stats.LongestRunSec != 10.0 {
		t.Errorf("LongestRun = %v", stats.LongestRunSec)
	}
}

func TestHistory_Aggregate_EmptyFiles(t *testing.T) {
	stats := Aggregate(nil)
	if stats.TotalRuns != 0 {
		t.Error("empty aggregate should have 0 runs")
	}
	if stats.ModeUseCount == nil || len(stats.ModeUseCount) != 0 {
		t.Error("empty aggregate should have empty maps")
	}
}

func TestHistory_FormatStats_ContainsKeyInfo(t *testing.T) {
	stats := AggregatedStats{
		TotalRuns:        10,
		TotalDiscoveries: 20,
		TotalOK:          15,
		TotalFail:        5,
		TotalCost:        0.123,
		TotalAPICalls:    50,
		ModeUseCount:     map[string]int{"DISCOVER": 7, "FLASH": 3},
		LangUseCount:     map[string]int{"en": 4, "ru": 6},
		FirstSession:     time.Date(2026, 6, 1, 10, 0, 0, 0, time.UTC),
		LastSession:      time.Date(2026, 6, 10, 10, 0, 0, 0, time.UTC),
	}
	out := stats.FormatStats()
	for _, want := range []string{"Total runs", "Total discoveries", "Total cost", "Mode usage", "Language usage", "DISCOVER", "ru"} {
		if !strings.Contains(out, want) {
			t.Errorf("FormatStats missing %q in:\n%s", want, out)
		}
	}
}

func TestHistory_FormatStats_LangPercentages(t *testing.T) {
	stats := AggregatedStats{
		LangUseCount: map[string]int{"en": 3, "ru": 7},
	}
	out := stats.FormatStats()
	if !strings.Contains(out, "70.0%") {
		t.Errorf("expected 70%% for ru in:\n%s", out)
	}
	if !strings.Contains(out, "30.0%") {
		t.Errorf("expected 30%% for en in:\n%s", out)
	}
}

func TestHistory_StreakDays_ConsecutiveDays(t *testing.T) {
	// Create 3 files on 3 consecutive days
	day1 := time.Date(2026, 6, 1, 12, 0, 0, 0, time.UTC)
	day2 := day1.Add(24 * time.Hour)
	day3 := day2.Add(24 * time.Hour)
	day4 := day3.Add(48 * time.Hour) // gap

	sortedDays := []string{
		"2026-06-01", "2026-06-02", "2026-06-03", "2026-06-05",
	}
	dayCount := map[string]int{
		"2026-06-01": 1, "2026-06-02": 1, "2026-06-03": 1, "2026-06-05": 1,
	}
	streak := computeStreak(sortedDays, dayCount)
	// streak should be 1 (last day 06-05 → no consecutive 06-04)
	if streak != 1 {
		t.Errorf("streak = %d, want 1", streak)
	}
	_ = day1
	_ = day2
	_ = day3
	_ = day4
}

func TestHistory_IsTimestampedHistory(t *testing.T) {
	tests := []struct {
		name string
		want bool
	}{
		{"tui-v9-history-2026-06-10-08-53-12.json", true},
		{"tui-v9-history-2026-06-10-08-53.json", false}, // wrong format
		{"tui-v9-history.json", false},
		{"other-file.json", false},
	}
	for _, tt := range tests {
		if got := isTimestampedHistory(tt.name); got != tt.want {
			t.Errorf("isTimestampedHistory(%q) = %v, want %v", tt.name, got, tt.want)
		}
	}
}

func TestHistoryDir_CreatesDir(t *testing.T) {
	tmp := t.TempDir()
	t.Setenv("HOME", tmp)
	dir, err := HistoryDir()
	if err != nil {
		t.Fatal(err)
	}
	expected := filepath.Join(tmp, ".config", "c4reqber")
	if dir != expected {
		t.Errorf("HistoryDir = %s, want %s", dir, expected)
	}
	if _, err := os.Stat(expected); err != nil {
		t.Errorf("dir not created: %v", err)
	}
}

func TestAggregate_TopDay(t *testing.T) {
	stats := Aggregate([]HistoryFile{
		{SessionEnd: time.Date(2026, 6, 1, 10, 0, 0, 0, time.UTC)},
		{SessionEnd: time.Date(2026, 6, 1, 14, 0, 0, 0, time.UTC)},
		{SessionEnd: time.Date(2026, 6, 1, 18, 0, 0, 0, time.UTC)},
		{SessionEnd: time.Date(2026, 6, 2, 10, 0, 0, 0, time.UTC)},
	})
	if stats.TopDay != "2026-06-01" {
		t.Errorf("TopDay = %s, want 2026-06-01", stats.TopDay)
	}
	if stats.TopDayCount != 3 {
		t.Errorf("TopDayCount = %d, want 3", stats.TopDayCount)
	}
}
