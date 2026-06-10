package tui

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"time"

	"github.com/figuramax/c4reqber-tui-v9/telemetry"
)

// saveTelemetryHistory writes the current telemetry snapshot to disk
// at ~/.config/c4reqber/tui-v9-history-{timestamp}.json. Called on Ctrl+C / shutdown.
func saveTelemetryHistory(tel *telemetry.Telemetry, cfg Config) {
	if tel == nil {
		return
	}
	_, _ = SaveHistoryFile(tel, cfg)
}

// (HistoryFile, SaveHistoryFile, LoadAllHistoryFiles, Aggregate, etc. above)

// HistoryFile is the per-run telemetry snapshot saved to disk.
type HistoryFile struct {
	Config     string              `json:"config"`
	SessionEnd time.Time           `json:"session_end"`
	Snapshot   telemetry.Snapshot `json:"snapshot"`
}

// HistoryDir returns ~/.config/c4reqber (created if missing).
func HistoryDir() (string, error) {
	home, err := os.UserHomeDir()
	if err != nil {
		return "", err
	}
	dir := filepath.Join(home, ".config", "c4reqber")
	if err := os.MkdirAll(dir, 0755); err != nil {
		return "", err
	}
	return dir, nil
}

// SaveHistoryFile writes a timestamped history file (per run).
// Returns the full path to the saved file.
func SaveHistoryFile(tel *telemetry.Telemetry, cfg Config) (string, error) {
	if tel == nil {
		return "", fmt.Errorf("telemetry is nil")
	}
	dir, err := HistoryDir()
	if err != nil {
		return "", err
	}
	snap := tel.Get()
	annotated := HistoryFile{
		Config:     cfg.String(),
		SessionEnd: time.Now(),
		Snapshot:   snap,
	}
	now := time.Now()
	filename := fmt.Sprintf("tui-v9-history-%s.json", now.Format("2006-01-02-15-04-05"))
	path := filepath.Join(dir, filename)
	data, err := json.MarshalIndent(annotated, "", "  ")
	if err != nil {
		return "", err
	}
	if err := os.WriteFile(path, data, 0644); err != nil {
		return "", err
	}
	return path, nil
}

// LoadAllHistoryFiles reads all tui-v9-history-*.json files from the history dir.
// Returns sorted by SessionEnd ascending.
func LoadAllHistoryFiles() ([]HistoryFile, error) {
	dir, err := HistoryDir()
	if err != nil {
		return nil, err
	}
	entries, err := os.ReadDir(dir)
	if err != nil {
		return nil, err
	}
	var out []HistoryFile
	for _, e := range entries {
		if e.IsDir() {
			continue
		}
		name := e.Name()
		if name != "tui-v9-history.json" && !isTimestampedHistory(name) {
			continue
		}
		path := filepath.Join(dir, name)
		data, err := os.ReadFile(path)
		if err != nil {
			continue
		}
		var hf HistoryFile
		if err := json.Unmarshal(data, &hf); err != nil {
			continue
		}
		out = append(out, hf)
	}
	sort.Slice(out, func(i, j int) bool {
		return out[i].SessionEnd.Before(out[j].SessionEnd)
	})
	return out, nil
}

func isTimestampedHistory(name string) bool {
	const prefix = "tui-v9-history-"
	const suffix = ".json"
	if len(name) < len(prefix)+len(suffix) {
		return false
	}
	if name[:len(prefix)] != prefix || name[len(name)-len(suffix):] != suffix {
		return false
	}
	// Try parsing the middle as 2006-01-02-15-04-05
	_, err := time.Parse("2006-01-02-15-04-05", name[len(prefix):len(name)-len(suffix)])
	return err == nil
}

// AggregatedStats is the cross-run aggregation result.
type AggregatedStats struct {
	TotalRuns        int                      `json:"total_runs"`
	TotalDiscoveries int                      `json:"total_discoveries"`
	TotalOK          int                      `json:"total_ok"`
	TotalFail        int                      `json:"total_fail"`
	TotalAbort       int                      `json:"total_abort"`
	TotalCost        float64                  `json:"total_cost"`
	TotalAPICalls    int                      `json:"total_api_calls"`
	TotalErrors      int                      `json:"total_errors"`
	AvgCostPerRun    float64                  `json:"avg_cost_per_run"`
	AvgRunSec        float64                  `json:"avg_run_sec"`
	LongestRunSec    float64                  `json:"longest_run_sec"`
	ModeUseCount     map[string]int           `json:"mode_use_count"`
	LangUseCount     map[string]int           `json:"lang_use_count"`
	FirstSession     time.Time                `json:"first_session"`
	LastSession      time.Time                `json:"last_session"`
	StreakDays       int                      `json:"streak_days"`
	TopDay           string                   `json:"top_day"` // YYYY-MM-DD
	TopDayCount      int                      `json:"top_day_count"`
}

// Aggregate combines multiple history files into a single stats view.
func Aggregate(files []HistoryFile) AggregatedStats {
	s := AggregatedStats{
		ModeUseCount: map[string]int{},
		LangUseCount: map[string]int{},
		FirstSession: time.Now().AddDate(100, 0, 0),
	}
	if len(files) == 0 {
		return s
	}
	dayCount := map[string]int{}
	for _, f := range files {
		s.TotalRuns++
		s.TotalDiscoveries += f.Snapshot.Discoveries
		s.TotalOK += f.Snapshot.DiscoveriesOK
		s.TotalFail += f.Snapshot.DiscoveriesFail
		s.TotalAbort += f.Snapshot.DiscoveriesAbort
		s.TotalCost += f.Snapshot.TotalCost
		s.TotalAPICalls += f.Snapshot.TotalAPICalls
		s.TotalErrors += f.Snapshot.APIErrors
		if f.Snapshot.LongestRunSec > s.LongestRunSec {
			s.LongestRunSec = f.Snapshot.LongestRunSec
		}
		for k, v := range f.Snapshot.ModeUseCount {
			s.ModeUseCount[k] += v
		}
		for k, v := range f.Snapshot.LangUseCount {
			s.LangUseCount[k] += v
		}
		if f.SessionEnd.Before(s.FirstSession) {
			s.FirstSession = f.SessionEnd
		}
		if f.SessionEnd.After(s.LastSession) {
			s.LastSession = f.SessionEnd
		}
		day := f.SessionEnd.Format("2006-01-02")
		dayCount[day]++
	}
	if s.TotalDiscoveries > 0 {
		// Approx avg run sec from total discover duration across runs
		totalSec := 0.0
		for _, f := range files {
			if f.Snapshot.Discoveries > 0 {
				totalSec += f.Snapshot.LongestRunSec // approximation
			}
		}
		s.AvgRunSec = totalSec / float64(s.TotalRuns)
	}
	if s.TotalRuns > 0 {
		s.AvgCostPerRun = s.TotalCost / float64(s.TotalRuns)
	}
	// Streak: count consecutive days with runs (from last day backward)
	sortedDays := make([]string, 0, len(dayCount))
	for d := range dayCount {
		sortedDays = append(sortedDays, d)
	}
	sort.Strings(sortedDays)
	s.StreakDays = computeStreak(sortedDays, dayCount)
	// Top day
	for d, c := range dayCount {
		if c > s.TopDayCount {
			s.TopDayCount = c
			s.TopDay = d
		}
	}
	return s
}

func computeStreak(sortedDays []string, dayCount map[string]int) int {
	if len(sortedDays) == 0 {
		return 0
	}
	// Walk backward from last day
	last, _ := time.Parse("2006-01-02", sortedDays[len(sortedDays)-1])
	streak := 0
	for i := len(sortedDays) - 1; i >= 0; i-- {
		d, _ := time.Parse("2006-01-02", sortedDays[i])
		if i == len(sortedDays)-1 {
			streak = 1
			last = d
			continue
		}
		// d should be last - 1 day
		if last.Sub(d) == 24*time.Hour {
			streak++
			last = d
		} else {
			break
		}
	}
	return streak
}

// FormatStats returns a human-readable summary of AggregatedStats.
func (s AggregatedStats) FormatStats() string {
	var out string
	out += fmt.Sprintf("Total runs:        %d\n", s.TotalRuns)
	out += fmt.Sprintf("Total discoveries: %d (ok=%d fail=%d abort=%d)\n",
		s.TotalDiscoveries, s.TotalOK, s.TotalFail, s.TotalAbort)
	out += fmt.Sprintf("Total cost:        $%.3f (avg $%.4f/run)\n", s.TotalCost, s.AvgCostPerRun)
	out += fmt.Sprintf("API calls:         %d (errors: %d)\n", s.TotalAPICalls, s.TotalErrors)
	out += fmt.Sprintf("Longest run:       %.1fs\n", s.LongestRunSec)
	if !s.FirstSession.IsZero() && !s.LastSession.IsZero() && s.LastSession.Sub(s.FirstSession) > 0 {
		out += fmt.Sprintf("Period:            %s → %s\n",
			s.FirstSession.Format("2006-01-02"), s.LastSession.Format("2006-01-02"))
	}
	out += fmt.Sprintf("Streak:            %d days\n", s.StreakDays)
	if s.TopDay != "" {
		out += fmt.Sprintf("Top day:           %s (%d runs)\n", s.TopDay, s.TopDayCount)
	}
	out += "\nMode usage:\n"
	for _, k := range sortedKeys(s.ModeUseCount) {
		out += fmt.Sprintf("  %-12s %d\n", k, s.ModeUseCount[k])
	}
	out += "\nLanguage usage:\n"
	totalLang := 0
	for _, v := range s.LangUseCount {
		totalLang += v
	}
	for _, k := range sortedKeys(s.LangUseCount) {
		v := s.LangUseCount[k]
		pct := 0.0
		if totalLang > 0 {
			pct = 100.0 * float64(v) / float64(totalLang)
		}
		out += fmt.Sprintf("  %-4s %4d (%.1f%%)\n", k, v, pct)
	}
	return out
}

func sortedKeys(m map[string]int) []string {
	keys := make([]string, 0, len(m))
	for k := range m {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	return keys
}
