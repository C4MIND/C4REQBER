package tui

import (
	"fmt"
	"sort"
	"strconv"
	"sync"
	"time"

	"charm.land/lipgloss/v2"

	"github.com/figuramax/c4reqber-tui-v9/i18n"
	"github.com/figuramax/c4reqber-tui-v9/persist"
	"github.com/figuramax/c4reqber-tui-v9/telemetry"
)

// Achievement kinds
type AchievementKind int

const (
	AchFirstDiscovery AchievementKind = iota
	AchQualityS
	AchMultiPaper
	AchTenDiscoveries
	AchSpeedster
	AchLinguist
	AchStreak
	// v9.13: sim-specific achievements (TI-SIM-08).
	AchSimExplorer // 5+ different sim engines in one session
	AchSimSaver    // got a 'refutes_hypothesis' verdict
	AchSimChef     // used fallback chain 3+ times
	AchSimDelegate // cloud-delegated (vast.ai) at least once
)

type Achievement struct {
	Kind        AchievementKind
	Name        string // i18n key
	Description string // i18n key
	Unlocked    bool
	UnlockedAt  time.Time
}

// AchievementSystem tracks user achievements.
type AchievementSystem struct {
	mu         sync.Mutex
	Items      []Achievement
	Unlocked   int
	Total      int
	LastUnlock time.Time
	// overlayActive + overlayUntil control the fullscreen achievement overlay.
	overlayActive  bool
	overlayUntil   time.Time
	overlayMessage string // i18n-rendered "🏆 Name · description"
}

func NewAchievements() *AchievementSystem {
	return &AchievementSystem{
		Items: []Achievement{
			{Kind: AchFirstDiscovery, Name: "achievement.first.name", Description: "achievement.first.desc"},
			{Kind: AchQualityS, Name: "achievement.qualityS.name", Description: "achievement.qualityS.desc"},
			{Kind: AchMultiPaper, Name: "achievement.multiPaper.name", Description: "achievement.multiPaper.desc"},
			{Kind: AchTenDiscoveries, Name: "achievement.ten.name", Description: "achievement.ten.desc"},
			{Kind: AchSpeedster, Name: "achievement.speed.name", Description: "achievement.speed.desc"},
			{Kind: AchLinguist, Name: "achievement.linguist.name", Description: "achievement.linguist.desc"},
			{Kind: AchStreak, Name: "achievement.streak.name", Description: "achievement.streak.desc"},
			// v9.13 (TI-SIM-08): sim achievements
			{Kind: AchSimExplorer, Name: "achievement.sim_explorer.name", Description: "achievement.sim_explorer.desc"},
			{Kind: AchSimSaver, Name: "achievement.sim_saver.name", Description: "achievement.sim_saver.desc"},
			{Kind: AchSimChef, Name: "achievement.sim_chef.name", Description: "achievement.sim_chef.desc"},
			{Kind: AchSimDelegate, Name: "achievement.sim_delegate.name", Description: "achievement.sim_delegate.desc"},
		},
		Total: 11,
	}
}

// LoadFromStore hydrates the AchievementSystem with already-unlocked
// achievements from a persistent store. This prevents the same
// achievement from being re-unlocked on every TUI restart (which
// used to create duplicate cards in the feed across sessions).
// v9.13.x fix: was missing — every restart was re-unlocking everything.
func (a *AchievementSystem) LoadFromStore(store *persist.Store) {
	if store == nil {
		return
	}
	a.mu.Lock()
	defer a.mu.Unlock()
	unlockedCount := 0
	for i := range a.Items {
		if store.HasAchievement(int(a.Items[i].Kind)) {
			a.Items[i].Unlocked = true
			unlockedCount++
		}
	}
	a.Unlocked = unlockedCount
}

// ShowOverlay triggers a 2s fullscreen achievement overlay.
// Called by Update when a new achievement is unlocked.
func (a *AchievementSystem) ShowOverlay(message string, duration time.Duration) {
	a.overlayActive = true
	a.overlayUntil = time.Now().Add(duration)
	a.overlayMessage = message
}

// OverlayMessage returns the i18n-rendered name of the most recent
// unlock shown on the overlay (or "" if no overlay is active).
// Exposed for tests; renderAchievementOverlay uses it indirectly
// via the same Items[] walk.
func (a *AchievementSystem) OverlayMessage() string {
	a.mu.Lock()
	defer a.mu.Unlock()
	return a.overlayMessage
}

// HideOverlay clears the overlay (called from Update tick).
func (a *AchievementSystem) HideOverlay() {
	a.overlayActive = false
	a.overlayMessage = ""
}

// OverlayActive returns true if the achievement overlay should be drawn.
func (a *AchievementSystem) OverlayActive() bool {
	if !a.overlayActive {
		return false
	}
	if time.Now().After(a.overlayUntil) {
		a.overlayActive = false
		return false
	}
	return true
}

// renderAchievementOverlay returns a fullscreen overlay (centered) for
// the most recent unlock. Auto-dismisses after the configured duration.
func renderAchievementOverlay(a *AchievementSystem, width, height int) string {
	// Build big centered card
	title := lipgloss.NewStyle().Bold(true).Foreground(lipgloss.Color("3")).Render(
		"🏆  " + i18n.T("achievement.unlocked"),
	)

	// Find the most-recently-unlocked achievement to feature. The
	// previous code picked the FIRST unlocked item in registry order,
	// which was always AchFirstDiscovery — so even after unlocking
	// QualityS or MultiPaper the overlay still said "First Discovery".
	// Fall back to any unlocked item if for some reason none have a
	// timestamp (e.g. hydrated by LoadFromStore which doesn't set
	// UnlockedAt — only sets Unlocked=true).
	var nameAch Achievement
	haveName := false
	for i := range a.Items {
		if !a.Items[i].Unlocked {
			continue
		}
		if !haveName || a.Items[i].UnlockedAt.After(nameAch.UnlockedAt) {
			nameAch = a.Items[i]
			haveName = true
		}
	}
	// If we still have no item (e.g. zero unlocked yet — shouldn't
	// happen since the overlay only fires when len(unlocked) > 0, but
	// be defensive), fall back to the first item rather than panic.
	if !haveName && len(a.Items) > 0 {
		nameAch = a.Items[0]
	}
	name := lipgloss.NewStyle().Bold(true).Foreground(lipgloss.Color("11")).Render(
		i18n.T(nameAch.Name),
	)
	desc := lipgloss.NewStyle().Foreground(lipgloss.Color("7")).Render(
		i18n.T(nameAch.Description),
	)
	progress := lipgloss.NewStyle().Foreground(lipgloss.Color("6")).Render(
		fmt.Sprintf("%d / %d", a.Unlocked, a.Total),
	)

	body := lipgloss.JoinVertical(lipgloss.Center,
		title,
		"",
		name,
		"",
		desc,
		"",
		progress,
		"",
		lipgloss.NewStyle().Foreground(lipgloss.Color("8")).Render(
			fmt.Sprintf("progress: %d/%d unlocked", a.Unlocked, a.Total),
		))

	boxStyle := lipgloss.NewStyle().
		Border(lipgloss.DoubleBorder()).
		BorderForeground(lipgloss.Color("3")).
		Padding(2, 4).
		Width(min(60, width-4))

	centered := lipgloss.Place(width, height, lipgloss.Center, lipgloss.Center, boxStyle.Render(body))
	return centered
}

// min returns the minimum of two ints.
func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}

// Check looks for new unlocks based on run state.
// Pass:
//   - discoveries int (total completed discoveries)
//   - lastQuality float (0.0..1.0 from last hypothesis)
//   - papersCount int (papers in last discovery)
//   - secondsTaken float
//   - langsUsed []string (distinct lang codes user has seen)
func (a *AchievementSystem) Check(discoveries int, lastQuality float64, papersCount int, secondsTaken float64, langsUsed []string) []Achievement {
	a.mu.Lock()
	defer a.mu.Unlock()
	justUnlocked := []Achievement{}
	for i := range a.Items {
		ach := &a.Items[i]
		if ach.Unlocked {
			continue
		}
		var unlock bool
		switch ach.Kind {
		case AchFirstDiscovery:
			unlock = discoveries >= 1
		case AchQualityS:
			unlock = lastQuality >= 0.8
		case AchMultiPaper:
			unlock = papersCount >= 3
		case AchTenDiscoveries:
			unlock = discoveries >= 10
		case AchSpeedster:
			unlock = secondsTaken > 0 && secondsTaken < 30
		case AchLinguist:
			unlock = len(langsUsed) >= 3
		case AchStreak:
			unlock = discoveries >= 5 // simplified: 5 in session
			// Sim achievements (TI-SIM-08) are checked by CheckSimAchievements,
			// not by this function (they need the feed, not aggregate counters).
		}
		if unlock {
			ach.Unlocked = true
			ach.UnlockedAt = time.Now()
			a.Unlocked++
			a.LastUnlock = ach.UnlockedAt
			justUnlocked = append(justUnlocked, *ach)
		}
	}
	return justUnlocked
}

// CheckSimAchievements walks the feed and unlocks sim-specific
// achievements per TI-SIM-08. Returns the list of newly-unlocked
// achievements (same shape as Check).
//
// Rules:
//
//	AchSimExplorer — 5+ different sim engines ran successfully in this session
//	AchSimSaver    — at least one CardSimulation with verdict "refutes_hypothesis"
//	AchSimChef     — 3+ CardSimulation with EngineStatus == "skipped" or "unavailable"
//	                 (i.e. fallback chain was invoked)
//	AchSimDelegate — at least one CardSimulation with EngineStatus == "delegated"
func (a *AchievementSystem) CheckSimAchievements(feed []Card) []Achievement {
	a.mu.Lock()
	defer a.mu.Unlock()
	engines := map[string]bool{}
	hasRefutes := false
	skippedCount := 0
	hasDelegated := false
	for _, c := range feed {
		if c.Kind != CardSimulation {
			continue
		}
		if c.Sim.EngineStatus == "success" || c.Sim.EngineStatus == "available" {
			engines[c.Sim.Engine] = true
		}
		if c.Sim.Verdict == "refutes_hypothesis" {
			hasRefutes = true
		}
		if c.Sim.EngineStatus == "skipped" || c.Sim.EngineStatus == "unavailable" {
			skippedCount++
		}
		if c.Sim.EngineStatus == "delegated" || c.Sim.EngineStatus == "delegated_to_cloud" {
			hasDelegated = true
		}
	}
	justUnlocked := []Achievement{}
	for i := range a.Items {
		ach := &a.Items[i]
		if ach.Unlocked {
			continue
		}
		var unlock bool
		switch ach.Kind {
		case AchSimExplorer:
			unlock = len(engines) >= 5
		case AchSimSaver:
			unlock = hasRefutes
		case AchSimChef:
			unlock = skippedCount >= 3
		case AchSimDelegate:
			unlock = hasDelegated
		}
		if unlock {
			ach.Unlocked = true
			ach.UnlockedAt = time.Now()
			a.Unlocked++
			a.LastUnlock = ach.UnlockedAt
			justUnlocked = append(justUnlocked, *ach)
		}
	}
	return justUnlocked
}

// renderTelemetry renders the bottom telemetry panel (Ctrl+T).
// Upgraded for v9.7 with tier + profile + per-lang % info.
func renderTelemetry(snap telemetry.Snapshot, width int, llmTier, colorProfile string) string {
	style := lipgloss.NewStyle().Width(width).Padding(0, 1).Foreground(lipgloss.Color("6"))
	dur := time.Since(snap.SessionStart).Round(time.Second)
	title := lipgloss.NewStyle().Bold(true).Foreground(lipgloss.Color("6")).Render("📊 Telemetry")
	modes := ""
	for k, v := range snap.ModeUseCount {
		modes += k + ":" + strconv.Itoa(v) + " "
	}
	// Lang usage with percentages
	totalLang := 0
	for _, v := range snap.LangUseCount {
		totalLang += v
	}
	langs := ""
	for _, k := range sortedKeysStringInt(snap.LangUseCount) {
		v := snap.LangUseCount[k]
		pct := 0.0
		if totalLang > 0 {
			pct = 100.0 * float64(v) / float64(totalLang)
		}
		langs += fmt.Sprintf("%s:%d(%.0f%%) ", k, v, pct)
	}
	stats := fmt.Sprintf(
		"disc=%d ok=%d fail=%d abort=%d api=%d err=%d cost=$%.3f longest=%.1fs",
		snap.Discoveries, snap.DiscoveriesOK, snap.DiscoveriesFail, snap.DiscoveriesAbort,
		snap.TotalAPICalls, snap.APIErrors, snap.TotalCost, snap.LongestRunSec,
	)
	tierStr := ""
	if llmTier != "" {
		tierStr = " tier=" + llmTier
	}
	profStr := ""
	if colorProfile != "" {
		profStr = " prof=" + colorProfile
	}
	usage := "modes: " + modes + " langs: " + langs
	uptime := fmt.Sprintf("uptime: %s", dur)
	return style.Render(title + "  " + stats + tierStr + profStr + "\n" + usage + "  " + uptime)
}

func sortedKeysStringInt(m map[string]int) []string {
	keys := make([]string, 0, len(m))
	for k := range m {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	return keys
}

// cycleLangName returns the next lang code, or "—" if no change.
func cycleLangName(current i18n.Lang) i18n.Lang {
	cycle := []i18n.Lang{i18n.LangEN, i18n.LangRU, i18n.LangZH, i18n.LangJA, i18n.LangDE, i18n.LangAR, i18n.LangHI}
	for i, l := range cycle {
		if l == current {
			return cycle[(i+1)%len(cycle)]
		}
	}
	return i18n.LangEN
}
