// Package capsim aggregates simulation/verification engine capabilities
// for the TUI v9 "what works on this machine" surface (Ctrl+Shift+C overlay).
//
// BE-SIM-01 in the unified plan. Aggregates:
//   - 32 simulation engine bridges (src/simulations/*_bridge.py)
//   - 27 verification/formal backends (src/verification/*_bridge.py)
//   - Hardware detection (Metal/CUDA/CPU)
//
// Cache TTL: 5 minutes, process-local. The backend has the same TTL on its side;
// the TUI consults its local cache first to keep overlay open < 100ms.
package capsim

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"sync"
	"time"
)

// EngineStatus is the user-facing status of one engine on the current machine.
type EngineStatus string

const (
	StatusAvailable   EngineStatus = "available"   // ● fast, primary path
	StatusSlow        EngineStatus = "slow"        // ◐ available, CPU fallback
	StatusUnavailable EngineStatus = "unavailable" // ○ engine itself not on this platform
	StatusBudget      EngineStatus = "budget_exceeded"
	StatusDelegated   EngineStatus = "delegated_to_cloud"
)

// Domain is a high-level subject area grouping engines.
type Domain string

const (
	DomainPhysics      Domain = "physics"
	DomainBiology      Domain = "biology"
	DomainChemistry    Domain = "chemistry"
	DomainMaterials    Domain = "materials"
	DomainClimate      Domain = "climate"
	DomainMedicine     Domain = "medicine"
	DomainNeuroscience Domain = "neuroscience"
	DomainRobotics     Domain = "robotics"
	DomainQuantum      Domain = "quantum"
	DomainAstrophysics Domain = "astrophysics"
	DomainEconomics    Domain = "economics"
	DomainGeneral      Domain = "general"
)

// Engine is one simulation engine bridge as the TUI sees it.
type Engine struct {
	ID            string       `json:"id"`
	Name          string       `json:"name"`
	Domain        Domain       `json:"domain"`
	Status        EngineStatus `json:"status"`
	MacNative     bool         `json:"mac_native"`
	Tier          string       `json:"tier"` // "fast" | "slow" | "linux_only" | "cloud"
	InstallHint   string       `json:"install_hint,omitempty"`
	MissingReason string       `json:"missing_reason,omitempty"`
	Patterns      []string     `json:"patterns,omitempty"`
}

// Verifier is one formal-verification backend.
type Verifier struct {
	ID          string `json:"id"`
	Name        string `json:"name"`
	Available   bool   `json:"available"`
	Version     string `json:"version,omitempty"`
	Path        string `json:"path,omitempty"`
	InstallHint string `json:"install_hint,omitempty"`
}

// Hardware is the host machine's compute capabilities.
type Hardware struct {
	Metal        bool    `json:"metal"`
	CUDA         bool    `json:"cuda"`
	AppleSilicon bool    `json:"apple_silicon"`
	GPUName      string  `json:"gpu_name"`
	GPUMemoryGB  float64 `json:"gpu_memory_gb"`
	CPUCount     int     `json:"cpu_count"`
	RAMGB        float64 `json:"ram_gb"`
}

// Platform identifies the host OS/arch.
type Platform struct {
	System string `json:"system"` // "Darwin", "Linux", "Windows"
	Arch   string `json:"arch"`   // "arm64", "x86_64"
}

// Report is the full response of GET /v8/simulations/capabilities.
type Report struct {
	Platform        Platform   `json:"platform"`
	Hardware        Hardware   `json:"hardware"`
	Engines         []Engine   `json:"engines"`
	Verifiers       []Verifier `json:"verifiers"`
	Domains         []DomainGroup `json:"domains"`
	ProbeTimestamp  time.Time  `json:"probe_timestamp"`
	ProbeLatencyMS  int64      `json:"probe_latency_ms"`
}

// DomainGroup groups engines under a domain for the overlay UI.
type DomainGroup struct {
	Domain  Domain  `json:"domain"`
	Engines []string `json:"engines"`
}

// Client fetches the capabilities report from the backend.
type Client struct {
	baseURL    string
	httpClient *http.Client
	mu         sync.RWMutex
	cache      *Report
	cacheAt    time.Time
	ttl        time.Duration
}

// NewClient returns a client with 5-minute cache TTL.
func NewClient(baseURL string) *Client {
	return &Client{
		baseURL:    baseURL,
		httpClient: &http.Client{Timeout: 8 * time.Second},
		ttl:        5 * time.Minute,
	}
}

// Get returns the capabilities report. Uses cache if fresh.
// Pass forceRefresh=true to bypass the cache (used by :capabilities refresh).
func (c *Client) Get(ctx context.Context, forceRefresh bool) (*Report, error) {
	if !forceRefresh {
		c.mu.RLock()
		if c.cache != nil && time.Since(c.cacheAt) < c.ttl {
			cp := *c.cache
			c.mu.RUnlock()
			return &cp, nil
		}
		c.mu.RUnlock()
	}

	started := time.Now()
	req, err := http.NewRequestWithContext(ctx, "GET", c.baseURL+"/v8/simulations/capabilities", nil)
	if err != nil {
		return nil, err
	}
	req.Header.Set("Accept", "application/json")
	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("capabilities fetch: %w", err)
	}
	defer resp.Body.Close()
	if resp.StatusCode >= 400 {
		return nil, fmt.Errorf("capabilities status %d", resp.StatusCode)
	}
	var report Report
	if err := json.NewDecoder(resp.Body).Decode(&report); err != nil {
		return nil, fmt.Errorf("capabilities decode: %w", err)
	}
	report.ProbeLatencyMS = time.Since(started).Milliseconds()
	if report.ProbeTimestamp.IsZero() {
		report.ProbeTimestamp = time.Now()
	}

	c.mu.Lock()
	c.cache = &report
	c.cacheAt = time.Now()
	c.mu.Unlock()
	return &report, nil
}

// Invalidate forces the next Get to re-fetch.
func (c *Client) Invalidate() {
	c.mu.Lock()
	c.cache = nil
	c.cacheAt = time.Time{}
	c.mu.Unlock()
}

// Fallback returns a static minimal report when the backend is unreachable.
// The TUI never crashes on missing capabilities — it shows this instead.
func Fallback() *Report {
	now := time.Now()
	return &Report{
		Platform:       Platform{System: "unknown", Arch: "unknown"},
		Hardware:       Hardware{},
		Engines:        []Engine{},
		Verifiers:      []Verifier{},
		Domains:        []DomainGroup{},
		ProbeTimestamp: now,
		ProbeLatencyMS: 0,
	}
}

// GroupByDomain re-bins the report's engines into the DomainGroups the TUI renders.
// The backend may already return this, but we always recompute on the client side
// to keep the rendering logic local and resilient.
func (r *Report) GroupByDomain() []DomainGroup {
	bucket := map[Domain][]string{}
	for _, e := range r.Engines {
		bucket[e.Domain] = append(bucket[e.Domain], e.ID)
	}
	out := make([]DomainGroup, 0, len(bucket))
	// Stable order for rendering
	order := []Domain{
		DomainPhysics, DomainBiology, DomainChemistry, DomainMaterials,
		DomainClimate, DomainMedicine, DomainNeuroscience, DomainRobotics,
		DomainQuantum, DomainAstrophysics, DomainEconomics, DomainGeneral,
	}
	for _, d := range order {
		if ids, ok := bucket[d]; ok && len(ids) > 0 {
			out = append(out, DomainGroup{Domain: d, Engines: ids})
		}
	}
	return out
}

// FilterAvailable returns only engines with Status == available or slow.
func (r *Report) FilterAvailable() []Engine {
	out := make([]Engine, 0, len(r.Engines))
	for _, e := range r.Engines {
		if e.Status == StatusAvailable || e.Status == StatusSlow {
			out = append(out, e)
		}
	}
	return out
}

// ByID looks up one engine by ID. Returns nil if not found.
func (r *Report) ByID(id string) *Engine {
	for i := range r.Engines {
		if r.Engines[i].ID == id {
			return &r.Engines[i]
		}
	}
	return nil
}
