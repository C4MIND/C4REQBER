package tui

import (
	"encoding/json"
	"os"
	"path/filepath"
	"time"

	"github.com/figuramax/c4reqber-tui-v9/telemetry"
)

// saveTelemetryHistory writes the current telemetry snapshot to disk
// at ~/.config/c4reqber/tui-v9-history.json. Called on Ctrl+C / shutdown.
func saveTelemetryHistory(tel *telemetry.Telemetry, cfg Config) {
	if tel == nil {
		return
	}
	snap := tel.Get()
	annotated := struct {
		Config     string              `json:"config"`
		SessionEnd time.Time           `json:"session_end"`
		Snapshot   telemetry.Snapshot `json:"snapshot"`
	}{
		Config:     cfg.String(),
		SessionEnd: time.Now(),
		Snapshot:   snap,
	}
	home, _ := os.UserHomeDir()
	dir := filepath.Join(home, ".config", "c4reqber")
	if err := os.MkdirAll(dir, 0755); err != nil {
		return
	}
	path := filepath.Join(dir, "tui-v9-history.json")
	data, err := json.MarshalIndent(annotated, "", "  ")
	if err != nil {
		return
	}
	_ = os.WriteFile(path, data, 0644)
}
