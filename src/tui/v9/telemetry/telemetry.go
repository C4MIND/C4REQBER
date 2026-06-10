// Package telemetry collects in-session metrics for the TUI v9.
package telemetry

import (
	"sync"
	"time"
)

// ModeCount tracks how many times each mode was used.
type ModeCount map[string]int

// Snapshot is a point-in-time view of all telemetry.
type Snapshot struct {
	SessionStart     time.Time     `json:"session_start"`
	TotalTicks       uint64        `json:"total_ticks"`
	Discoveries      int           `json:"discoveries"`
	DiscoveriesOK    int           `json:"discoveries_ok"`
	DiscoveriesFail  int           `json:"discoveries_fail"`
	DiscoveriesAbort int           `json:"discoveries_aborted"`
	ModeUseCount     ModeCount     `json:"mode_use_count"`
	LangUseCount     ModeCount     `json:"lang_use_count"`
	TotalLatencySec  float64       `json:"total_latency_sec"`
	LongestRunSec    float64       `json:"longest_run_sec"`
	TotalCost        float64       `json:"total_cost_usd"`
	TotalAPICalls    int           `json:"total_api_calls"`
	APIErrors        int           `json:"api_errors"`
}

// Telemetry is the live metrics collector.
type Telemetry struct {
	mu sync.RWMutex
	s  Snapshot
}

// New creates a new Telemetry.
func New() *Telemetry {
	return &Telemetry{s: Snapshot{SessionStart: time.Now(), ModeUseCount: ModeCount{}, LangUseCount: ModeCount{}}}
}

func (t *Telemetry) IncTick() {
	t.mu.Lock()
	t.s.TotalTicks++
	t.mu.Unlock()
}

func (t *Telemetry) IncDiscovery() {
	t.mu.Lock()
	t.s.Discoveries++
	t.mu.Unlock()
}

func (t *Telemetry) IncDiscoveryResult(ok bool, seconds float64) {
	t.mu.Lock()
	t.s.Discoveries++
	if ok {
		t.s.DiscoveriesOK++
	} else {
		t.s.DiscoveriesFail++
	}
	t.s.TotalLatencySec += seconds
	if seconds > t.s.LongestRunSec {
		t.s.LongestRunSec = seconds
	}
	t.mu.Unlock()
}

func (t *Telemetry) IncAbort() {
	t.mu.Lock()
	t.s.DiscoveriesAbort++
	t.mu.Unlock()
}

func (t *Telemetry) IncMode(mode string) {
	t.mu.Lock()
	t.s.ModeUseCount[mode]++
	t.mu.Unlock()
}

func (t *Telemetry) IncLang(lang string) {
	t.mu.Lock()
	t.s.LangUseCount[lang]++
	t.mu.Unlock()
}

func (t *Telemetry) AddCost(usd float64) {
	t.mu.Lock()
	t.s.TotalCost += usd
	t.mu.Unlock()
}

func (t *Telemetry) IncAPICall() {
	t.mu.Lock()
	t.s.TotalAPICalls++
	t.mu.Unlock()
}

func (t *Telemetry) IncAPIError() {
	t.mu.Lock()
	t.s.APIErrors++
	t.mu.Unlock()
}

// Get returns a copy of the current snapshot.
func (t *Telemetry) Get() Snapshot {
	t.mu.RLock()
	defer t.mu.RUnlock()
	cp := t.s
	cp.ModeUseCount = make(ModeCount, len(t.s.ModeUseCount))
	for k, v := range t.s.ModeUseCount {
		cp.ModeUseCount[k] = v
	}
	cp.LangUseCount = make(ModeCount, len(t.s.LangUseCount))
	for k, v := range t.s.LangUseCount {
		cp.LangUseCount[k] = v
	}
	return cp
}
