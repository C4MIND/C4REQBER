// Package tui implements TUI v9 "The Cockpit" — single-screen feed-driven discovery UI.
package tui

import (
	"fmt"
	"strings"
	"sync"
	"time"

	"charm.land/bubbles/v2/textarea"
	"charm.land/bubbles/v2/viewport"
	tea "charm.land/bubbletea/v2"

	"github.com/figuramax/c4reqber-tui-v9/api"
	"github.com/figuramax/c4reqber-tui-v9/cards"
	"github.com/figuramax/c4reqber-tui-v9/capsim"
	"github.com/figuramax/c4reqber-tui-v9/effects"
	"github.com/figuramax/c4reqber-tui-v9/i18n"
	"github.com/figuramax/c4reqber-tui-v9/persist"
	"github.com/figuramax/c4reqber-tui-v9/telemetry"
)

// CardKind is a thin alias preserving the legacy names used in view.go and
// update.go. New code should prefer cards.Kind.
type CardKind = cards.Kind
type CardState = cards.State

const (
	CardEmpty      = cards.KindEmpty
	CardPhase      = cards.KindPhase
	CardHypothesis = cards.KindHypothesis
	CardPaper      = cards.KindPaper
	CardCode       = cards.KindCode
	CardError      = cards.KindError
	CardSimulation = cards.KindSimulation
)

// Card is a type alias preserving the legacy field names used in view.go
// and update.go. New code should prefer the cards.Card struct directly;
// this alias exists only to avoid touching every render branch in one go.
type Card = cards.Card

// Mode — what kind of discovery.
type Mode string

const (
	ModeDiscover     Mode = "DISCOVER"
	ModeFlash        Mode = "FLASH"
	ModeTurbo        Mode = "TURBO"
	ModeTurboFactory Mode = "TURBOFACTORY"
)

// model is the top-level state.
type model struct {
	apiURL string
	api    *api.Client
	width  int
	height int

	// keymap resolves semantic actions to platform-appropriate key labels
	// (e.g. Cmd+L on macOS vs Ctrl+L on Linux/Windows). Built once at
	// startup; read-only thereafter.
	keymap *KeyMap

	mode      Mode
	cost      float64
	running   bool
	jobID     string
	startedAt time.Time

	feed   []Card
	vp     viewport.Model
	follow bool

	// v9.13: focused card index in feed. -1 means "follow last".
	// j/k navigate, Enter expands, actions target this card.
	focusedCardIdx int

	ta        textarea.Model
	focus     bool
	toast     string
	toastTick int // tick when toast was last set (for auto-clear ~1.5s)

	// v9.12.1: dedup phase cards — only append when phase/progress changes.
	lastPhase    string
	lastProgress float64

	tick int

	// game-feel effects
	rain   *effects.Rain
	burst  *effects.Burst
	slide  *effects.SlideIn
	typew  *effects.Typewriter
	sparks *effects.Sparkles
	verdictPulse *effects.VerdictPulse // v9.13: pulses on sim verdicts (§12.5)

	// SSE stream state
	sseEvents <-chan api.SSEEvent
	sseCancel func()

	// Mouse click zones (tracked for clickable cards)
	zoneIDs []string

	// Achievements + meta
	achievements    *AchievementSystem
	completedDisc   int
	langsSeen       map[string]bool
	langsMu         sync.RWMutex // guards langsSeen for concurrent View/Update
	lastQuality     float64
	lastPapersCount int

	// Persisted state (achievements, langs seen) and in-session telemetry
	store *persist.Store
	tel   *telemetry.Telemetry

	// Cached footer values to avoid re-rendering noise on every frame.
	// v9.11.3: View() runs at 60fps, but time.Now() in the footer
	// caused the timestamp to flicker every second, which looked like
	// a blinking/broken display. We cache it and refresh only when
	// the wall-clock second changes.
	lastFooterSecond  int    // last second (0-59) rendered in footer
	cachedFooterClock string // formatted "15:04:05" for that second

	// showTelemetry toggles the bottom telemetry panel (Ctrl+T)
	showTelemetry bool

	// basePanelH caches the base-layout panel height (computed in layout()).
	basePanelH int

	// showHelp toggles the fullscreen keymap help overlay (?)
	showHelp bool

	// dream is the ambient idle mode (activates after 5min of no activity)
	dream *DreamState

	// saveHistory controls whether telemetry history is persisted on shutdown
	saveHistory bool

	// llmTier is the LLM depth tier (C1/C2/C3) — switchable via Ctrl+Y
	llmTier LLMTier

	// colorProfile is the active color profile (default/high-contrast/dalt)
	colorProfile ColorProfile

	// wizard is the first-run wizard (nil if not active)
	wizard *WizardState

	// settingsVisible toggles the in-app settings menu UI (Ctrl+,)
	settingsVisible bool
	// settingsCursor tracks the currently highlighted row in settings menu
	settingsCursor int

	// showAchievementOverlay shows the fullscreen unlock animation
	showAchievementOverlay bool

	// v9.13 (TI-SIM-02): capabilities overlay
	capsimClient    *capsim.Client
	capsimReport    *capsim.Report
	showCapabilities bool
	capsimLoading   bool

	// v9.13 (TI-SIM-07): sim settings — preference, cost limit, session spend.
	// simPreference: "auto" | "cpu_only" | "off" — controls whether sims run
	// simCostLimit: USD per discovery; over → emit CardSimulation with budget_exceeded
	// simSpendThisSession: running total from cost_update events (placeholder
	//   until backend B-07 ships; today just a counter)
	simPreference     string
	simCostLimit      float64
	simSpendThisSession float64

	// v9.13 (§3.3): status bar — 1-line context strip with conn/follow/sim.
	// showStatusBar: user toggle (Ctrl+B, default true at T2+).
	// connState: live state of SSE/polling pipeline (§8.2).
	// simCountThisRun: number of CardSimulation cards added in current run.
	showStatusBar   bool
	connState       ConnectionState
	simCountThisRun int

	// v9.13 (§15): debug overlay
	showDebug bool

	// v9.13 (§11): theme — pre-built lipgloss styles for the active profile.
	// Rebuilt whenever the user cycles the profile (Ctrl+Shift+P).
	theme *Theme

	// v9.13 (§16.2): command palette
	paletteActive    bool
	paletteQuery     string
	paletteFocused   int
	paletteMatches   []MatchResult
	paletteRegistry  *Registry

	// v9.13 (§10): persistence — feed store and input history.
	feedStore     *persist.FeedStore
	inputHistory  *persist.InputHistory
}

// message types for bubbletea
type (
	apiSubmitMsg struct {
		jobID string
		err   error
	}
	apiPollMsg struct {
		status    string
		phase     string
		progress  float64
		result    map[string]any
		err       error
		completed bool
	}
	apiPapersMsg struct {
		papers []map[string]any
		err    error
	}
	apiHypothesisMsg struct {
		hyp map[string]any
		err error
	}
	sseEventMsg struct {
		event  api.SSEEvent
		events <-chan api.SSEEvent
		cancel func()
	}
	sseErrorMsg struct {
		err error
	}
	sseClosedMsg   struct{}
	flashResultMsg struct {
		result map[string]any
		err    error
	}
	multiResultMsg struct {
		result map[string]any
		err    error
	}
	tickMsg     time.Time
	pollTickMsg time.Time
)

func (p pollTickMsg) String() string { return "poll-tick" }

var _ tea.Model = (*model)(nil)

// NewAppWithStore creates a model with a custom persist.Store (used by tests).
func NewAppWithStore(apiURL string, store *persist.Store) *model {
	m := NewApp(apiURL)
	// Override the real store with the test store and re-apply settings
	m.store = store
	if store != nil {
		m.ApplySettings(store.GetSettings())
	}
	return m
}

// NewApp exports the constructor for cmd/c4tui-v9.
func NewApp(apiURL string) *model {
	ta := textarea.New()
	ta.Placeholder = i18n.T("placeholder")
	ta.Prompt = "❯ "
	ta.SetWidth(80)
	ta.SetHeight(3)
	ta.Focus()

	vp := viewport.New(viewport.WithWidth(80), viewport.WithHeight(20))
	vp.MouseWheelEnabled = true

	m := &model{
		apiURL:        apiURL,
		api:           api.New(apiURL),
		keymap:        NewKeyMap(DetectPlatform()),
		mode:          ModeDiscover,
		focusedCardIdx: -1, // -1 = follow last; avoids "focusing" the empty card at startup
		ta:            ta,
		vp:            vp,
		focus:         true,
		follow:        true,
		rain:          effects.NewRain(),
		burst:         effects.NewBurst(),
		slide:         effects.NewSlideIn(),
		typew:         effects.NewTypewriter(),
		sparks:        effects.NewSparkles(),
		verdictPulse:  effects.NewVerdictPulse(),
		theme:         NewTheme(ProfileDefault),
		paletteRegistry: buildRegistry(),
		achievements:  NewAchievements(),
		langsSeen:     map[string]bool{},
		tel:           telemetry.New(),
		dream:         NewDreamState(),
		saveHistory:   true,
		llmTier:       TierC2,
		colorProfile:  ProfileDefault,
		wizard:        NewWizardState(),
		capsimClient:        capsim.NewClient(apiURL),
		feedStore:           initFeedStore(),
		inputHistory:        initInputHistory(),
		simPreference:       "auto",
		simCostLimit:        5.00,
		showStatusBar:        true,
	}
	// Load persisted state (achievements, langs). If store fails, fall back gracefully.
	store, storeErr := persist.New(persist.DefaultPath())
	if storeErr == nil {
		m.store = store
		// Repopulate langsSeen from disk
		m.replaceLangsSeen(store.Snapshot().LangsSeen)
		// v9.13.x: hydrate AchievementSystem from store so previously
		// unlocked achievements don't get re-unlocked (which created
		// duplicate cards in the feed across sessions).
		m.achievements.LoadFromStore(store)
	}
	m.addLangSeen(string(i18n.GetLang()))
	// Apply persisted settings (tier/profile/lang)
	if m.store != nil {
		m.ApplySettings(m.store.GetSettings())
		// First-run wizard
		if m.store.IsFirstRun() {
			m.wizard.Show()
		}
	}
	// v9.13 (B-05): restore last N cards from feed.jsonl FIRST, before the
	// initial Empty placeholder. This avoids double-appending the placeholder.
	restoredCount := 0
	if m.feedStore != nil {
		entries, _ := m.feedStore.LoadRecent(50)
		// Reverse to chronological order (LoadRecent returns most-recent-first)
		for i, j := 0, len(entries)-1; i < j; i, j = i+1, j-1 {
			entries[i], entries[j] = entries[j], entries[i]
		}
		for _, e := range entries {
			m.feed = append(m.feed, Card{
				Kind:     CardKind(e.Kind),
				Title:    e.Title,
				Body:     e.Body,
				Time:     e.Time,
				Status:   e.Status,
				Bookmark: e.Bookmark,
				Sim: cards.SimFields{
					Engine:       e.SimEngine,
					EngineStatus: e.SimStatus,
					Verdict:      e.SimVerdict,
					CostUSD:      e.SimCostUSD,
					InstallHint:  e.SimInstallHint,
					HypothesisID: cards.ID(e.SimHypothesisID),
				},
			})
			restoredCount++
		}
	}
	// Bind the palette command closures unconditionally. This MUST run on
	// every NewApp path — previously it was nested inside the showPlaceholder
	// branch, so any returning user (cards restored from feed.jsonl) or an
	// active first-run wizard left every palette command with Run==nil, making
	// the whole command palette a silent no-op.
	m.bindRegistry()
	// Only append the empty placeholder if there are no restored cards
	// AND the existing first-run wizard isn't going to take over the screen.
	showPlaceholder := restoredCount == 0
	if m.wizard != nil && m.wizard.Active() {
		showPlaceholder = false
	}
	if showPlaceholder {
		m.appendCard(Card{Kind: CardEmpty, Title: i18n.T("empty.title"), Body: i18n.T("empty.hint"), Time: time.Now()})
	}
	if restoredCount > 0 {
		m.setToast(fmt.Sprintf("restored %d cards from last session", restoredCount))
	}
	return m
}

// NewAppFresh creates a model without loading any persisted state (test-friendly).
// Use this in tests that need a clean slate.
func NewAppFresh(apiURL string) *model {
	cfg := DefaultConfig()
	if apiURL == "" {
		apiURL = cfg.APIURL
	}
	ta := textarea.New()
	ta.Placeholder = i18n.T("placeholder")
	ta.ShowLineNumbers = false
	ta.CharLimit = 0
	ta.SetWidth(80)
	ta.SetHeight(3)
	vp := viewport.New()
	m := &model{
		apiURL:        apiURL,
		api:           api.New(apiURL),
		keymap:        NewKeyMap(DetectPlatform()),
		mode:          ModeDiscover,
		focusedCardIdx: -1, // -1 = follow last; avoids "focusing" the empty card at startup
		ta:            ta,
		vp:            vp,
		focus:         true,
		follow:        true,
		rain:          effects.NewRain(),
		burst:         effects.NewBurst(),
		slide:         effects.NewSlideIn(),
		typew:         effects.NewTypewriter(),
		sparks:        effects.NewSparkles(),
		verdictPulse:  effects.NewVerdictPulse(),
		theme:         NewTheme(ProfileDefault),
		paletteRegistry: buildRegistry(),
		achievements:  NewAchievements(),
		langsSeen:     map[string]bool{},
		tel:           telemetry.New(),
		dream:         NewDreamState(),
		saveHistory:   true, // match NewApp; was missing here, drifted from production
		llmTier:       TierC2,
		colorProfile:  ProfileDefault,
		wizard:        NewWizardState(),
		capsimClient:        capsim.NewClient(apiURL),
		feedStore:           initFeedStore(),
		inputHistory:        initInputHistory(),
		simPreference:       "auto",
		simCostLimit:        5.00,
		showStatusBar:       true,
	}
	// Deliberately hermetic: NewAppFresh does NOT open persist.DefaultPath()
	// (the $HOME-scoped store). Reading it would apply the developer's saved
	// language/tier/profile and re-trigger the first-run wizard, leaking real
	// local state into tests (e.g. a saved lang=ru overriding SetLang(EN), or
	// the wizard overlay hiding the empty feed). Tests that need a backing
	// store inject one via NewAppWithStore instead. m.store stays nil here.
	//
	// feedStore/inputHistory are still set (via initFeedStore/initInputHistory
	// which read $HOME) so persistence-path tests work — they always
	// `t.Setenv("HOME", tmp)` first, so writes go to the temp dir, not the
	// developer's real ~/.c4reqber.
	m.addLangSeen(string(i18n.GetLang()))
	m.bindRegistry()
	m.appendCard(Card{Kind: CardEmpty, Title: i18n.T("empty.title"), Body: i18n.T("empty.hint"), Time: time.Now()})
	return m
}

func (m *model) Init() tea.Cmd {
	return tea.Batch(tea.RequestBackgroundColor, m.tickCmd(), m.pollTickCmd())
}

func (m *model) tickCmd() tea.Cmd {
	return tea.Tick(time.Millisecond*16, func(t time.Time) tea.Msg { return tickMsg(t) })
}

func (m *model) pollTickCmd() tea.Cmd {
	return tea.Tick(time.Second*2, func(t time.Time) tea.Msg { return pollTickMsg(t) })
}

// T shortcut re-exports i18n.T.
func T(key string) string { return i18n.T(key) }

// SetLang shortcut re-exports i18n.SetLang.
func SetLang(l i18n.Lang) { i18n.SetLang(l) }

// Tel returns the telemetry handle (used by main to save history on exit).
func (m *model) Tel() *telemetry.Telemetry { return m.tel }

// Config returns the live config snapshot.
func (m *model) Config() Config {
	return Config{
		APIURL:      m.apiURL,
		Lang:        i18n.GetLang(),
		DreamIdle:   m.dream.idleSeconds,
		SaveHistory: true,
	}
}

// initFeedStore creates a FeedStore or returns nil if HOME is unset/invalid.
// Tests can use this safely — it never panics.
func initFeedStore() *persist.FeedStore {
	f, err := persist.NewFeedStore(50)
	if err != nil {
		return nil
	}
	return f
}

// initInputHistory creates an InputHistory or returns nil on error.
func initInputHistory() *persist.InputHistory {
	h, err := persist.NewInputHistory(200)
	if err != nil {
		return nil
	}
	return h
}

// ApplySettings applies persisted settings to the model (called after persist load).
func (m *model) ApplySettings(s persist.Settings) {
	if s.LLMTier != "" {
		if t, ok := TierFromString(s.LLMTier); ok {
			m.llmTier = t
		}
	}
	if s.ColorProfile != "" {
		if p, ok := ProfileFromString(s.ColorProfile); ok {
			m.colorProfile = p
		}
	}
	if s.Lang != "" {
		i18n.SetLang(i18n.Lang(s.Lang))
	}
}

// PersistSettings saves current model settings to the persist store.
func (m *model) PersistSettings() {
	if m.store == nil {
		return
	}
	m.store.SetSettings(persist.Settings{
		LLMTier:      m.llmTier.String(),
		ColorProfile: m.colorProfile.String(),
		Lang:         string(i18n.GetLang()),
	})
	_ = m.store.Save()
}

// ApplySimCost accumulates a cost update from a backend cost_update event.
// Called by the SSE event handler when the backend sends real cost data
// (BE-SIM-10). Until the backend emits those events, this is unused and
// the header cost stays at 0.
func (m *model) ApplySimCost(usd float64) {
	if usd < 0 {
		return
	}
	m.simSpendThisSession += usd
}

// MarkFirstRunDone marks the first-run wizard as completed in the persist store.
func (m *model) MarkFirstRunDone() {
	if m.store != nil {
		m.store.MarkFirstRunDone()
		_ = m.store.Save()
	}
}

// (no helpers needed — tests use persist.New directly)

// handlePhaseEvent updates phase progress from a typed phase_progress/phase_change event.
func (m *model) handlePhaseEvent(te api.TypedEvent) {
	phase := te.Phase
	progress := te.Progress
	if phase != m.lastPhase || (abs(progress-m.lastProgress) > 0.01) {
		m.lastPhase = phase
		m.lastProgress = progress
		body := fmt.Sprintf("progress %.0f%%", progress*100)
		if te.Substep != "" {
			body = te.Substep + " · " + body
		}
		m.appendCard(Card{Kind: CardPhase, Title: phase, Body: body, Time: time.Now(), Status: "running", Progress: progress})
	}
}

// handleSimEvent creates a CardSimulation from a typed sim_* event.
// Back-link to hypothesis: if the event has HypothesisID, try to find
// the most recent CardHypothesis and link the sim to it.
func (m *model) handleSimEvent(te api.TypedEvent) {
	// Default domain: infer from engine or pattern
	domain := simDomainForEngine(te.Engine)
	// Find hypothesis to link to
	hypID := cards.ID(0)
	if te.HypothesisID != "" {
		// Try parse as numeric ID
		var id uint64
		if _, err := fmt.Sscanf(te.HypothesisID, "%d", &id); err == nil {
			hypID = cards.ID(id)
		}
	}
	if hypID == 0 {
		// Fall back: link to most recent hypothesis
		for i := len(m.feed) - 1; i >= 0; i-- {
			if m.feed[i].Kind == CardHypothesis {
				hypID = m.feed[i].ID
				break
			}
		}
	}
	c := Card{
		ID:    cards.NextID(),
		Kind:  CardSimulation,
		Title: te.Engine + " · " + te.Pattern,
		Body:  simBody(te),
		Time:  time.Now(),
		Status: func() string {
			switch te.Type {
			case api.EventSimFinished:
				if te.EngineStatus == "success" || te.EngineStatus == "" {
					return "done"
				}
				return "error"
			case api.EventSimSkipped:
				return "skipped"
			case api.EventSimBudgetExceeded:
				return "error"
			}
			return "running"
		}(),
		Sim: cards.SimFields{
			Engine:       te.Engine,
			EngineStatus: simStatusString(te),
			Domain:       domain,
			Pattern:      te.Pattern,
			Verdict:      te.Verdict,
			CostUSD:      te.CostUSD,
			BackendHost:  te.BackendHost,
			ElapsedMS:    te.ElapsedMS,
			HypothesisID: hypID,
			InstallHint:  te.InstallHint,
			PatternsTried: []cards.PatternTry{
				{Engine: te.Engine, Status: simStatusString(te), Reason: te.Reason, ElapsedMS: te.ElapsedMS},
			},
		},
	}
	if te.Type == api.EventSimFinished && te.Verdict != "" {
		// Capture evidence briefly
		c.Sim.Evidence = cards.SimEvidence{
			Type:    "verdict",
			Caption: te.Verdict,
		}
	}
	m.appendCard(c)
	m.simCountThisRun++
	// v9.13: trigger the verdict pulse (visual highlight for the user)
	if m.verdictPulse != nil && te.Type == api.EventSimFinished && c.Sim.Verdict != "" {
		m.verdictPulse.Trigger(c.Sim.Verdict)
	}
}

// simStatusString maps a typed sim event to the CardSimulation status enum.
func simStatusString(te api.TypedEvent) string {
	switch te.Type {
	case api.EventSimStarted:
		if te.EngineStatus != "" {
			return te.EngineStatus
		}
		return "running"
	case api.EventSimFinished:
		if te.EngineStatus == "error" {
			return "error"
		}
		return "success"
	case api.EventSimSkipped:
		return "skipped"
	case api.EventSimBudgetExceeded:
		return "budget_exceeded"
	}
	return te.EngineStatus
}

// simBody returns a one-line description of the sim event.
func simBody(te api.TypedEvent) string {
	switch te.Type {
	case api.EventSimStarted:
		return fmt.Sprintf("starting %s on %s", te.Pattern, te.Engine)
	case api.EventSimFinished:
		if te.Verdict != "" {
			return fmt.Sprintf("verdict: %s · %dms · $%.4f", te.Verdict, te.ElapsedMS, te.CostUSD)
		}
		return fmt.Sprintf("finished · %dms · $%.4f", te.ElapsedMS, te.CostUSD)
	case api.EventSimSkipped:
		body := fmt.Sprintf("skipped: %s", te.Reason)
		if te.InstallHint != "" {
			body += " — try: " + te.InstallHint
		}
		return body
	case api.EventSimBudgetExceeded:
		return fmt.Sprintf("budget exceeded ($%.4f > limit $%.2f)", te.CostUSD, 5.0)
	}
	return string(te.Type)
}

// simDomainForEngine maps an engine name to a high-level domain. Used
// when the backend event doesn't carry an explicit domain field.
func simDomainForEngine(engine string) string {
	switch engine {
	case "vina", "boolnet", "cobra", "slim", "neuron", "brian2", "jaxley", "tellurium", "copasi":
		return "biology"
	case "openmm":
		return "biology" // openmm can be biology or chemistry; default to biology
	case "pyscf", "psi4", "quantum_espresso", "schr":
		return "chemistry"
	case "newton", "jaxsim", "mujoco", "pybullet", "torchsim":
		return "physics"
	case "gromacs", "lammps", "mdanalysis", "jax_md":
		return "chemistry"
	case "fenicsx", "openfoam", "taichi", "jax_lab", "modelingtoolkit", "diffeqpy":
		return "materials"
	case "xarray", "wrf":
		return "climate"
	case "mesa", "simpy":
		return "economics"
	case "rebound", "amuse":
		return "astrophysics"
	}
	return "general"
}

// teardownStream cancels the live SSE stream's context and clears the model's
// stream references. Safe to call when no stream is active. Centralizing the
// cancel+nil bookkeeping here keeps the completion / failure / closed / error /
// cancel paths from leaking the api.Stream reader goroutine + HTTP connection.
func (m *model) teardownStream() {
	if m.sseCancel != nil {
		m.sseCancel()
		m.sseCancel = nil
	}
	m.sseEvents = nil
}

// handleCompleteEvent handles a typed 'complete' event — final results.
func (m *model) handleCompleteEvent(te api.TypedEvent) {
	m.running = false
	m.jobID = ""
	m.setToast(i18n.T("toast.complete"))
	m.burst.Trigger(m.width, m.height, m.width/2, m.height/2)
	if te.Result != nil {
		if hyp, ok := te.Result["hypothesis"].(map[string]any); ok {
			hc := Card{Kind: CardHypothesis, Title: i18n.T("card.hypothesis.t"), Body: fieldString(hyp, "text"), Meta: []cards.MetaKV{{Key: "source", Value: fieldString(hyp, "source")}}, Time: time.Now(), Status: "done"}
			m.appendCard(hc)
			m.typew.Set(fieldString(hyp, "text"), m.tick)
			if novelty, ok := hyp["novelty_score"].(float64); ok {
				m.lastQuality = novelty
			}
		}
		if papers, ok := te.Result["papers"].([]any); ok {
			m.lastPapersCount = len(papers)
			for i, p := range papers {
				if i >= 3 {
					break
				}
				pm, _ := p.(map[string]any)
				m.appendCard(Card{Kind: CardPaper, Title: fieldString(pm, "title"), Body: fmt.Sprintf("%s · %s · citations %s", fieldString(pm, "venue"), fieldString(pm, "year"), fieldString(pm, "citation_count")), Meta: []cards.MetaKV{{Key: "doi", Value: fieldString(pm, "doi")}, {Key: "source", Value: fieldString(pm, "source")}}, Time: time.Now(), Status: "done"})
			}
		}
		m.completedDisc++
		m.checkAchievements()
	}
}

// handleFailedEvent handles a typed 'failed' or 'cancelled' event.
func (m *model) handleFailedEvent(te api.TypedEvent) {
	m.running = false
	m.jobID = ""
	body := "cancelled"
	if len(te.Errors) > 0 {
		body = strings.Join(te.Errors, "; ")
	} else if te.Status != "" {
		body = te.Status
	}
	m.appendCard(Card{Kind: CardError, Title: "Discovery " + string(te.Type), Body: body, Time: time.Now(), Status: "error"})
}

// handleLegacyPhase is the safety-net path for old v8.12 events that
// don't have a 'type' field. Extracts the phase/progress tuple and
// dispatches to the same code path as handlePhaseEvent.
func (m *model) handleLegacyPhase(status, phase string, progress float64, result map[string]any, completed bool) {
	if status != "" || phase != "" {
		if phase != m.lastPhase || (abs(progress-m.lastProgress) > 0.01) {
			m.lastPhase = phase
			m.lastProgress = progress
			m.appendCard(Card{Kind: CardPhase, Title: phase, Body: fmt.Sprintf("progress %.0f%%", progress*100), Time: time.Now(), Status: "running", Progress: progress})
		}
	}
	if completed {
		m.handleCompleteEvent(api.TypedEvent{Result: result, Status: status})
	}
}

// verdictChipsForCard returns the verdict chip string for a CardHypothesis,
// or empty string if no sims link to it. Convenience wrapper around
// verdictChips(m, c.ID).
func (m *model) verdictChipsForCard(c Card) string {
	if c.Kind != CardHypothesis {
		return ""
	}
	return verdictChips(m, c.ID)
}

// focusedCard returns the card the user has navigated to with j/k.
// If no card is focused (idx < 0 or feed empty), returns the last card.
func (m *model) focusedCard() *Card {
	if len(m.feed) == 0 {
		return nil
	}
	idx := m.focusedCardIdx
	if idx < 0 || idx >= len(m.feed) {
		idx = len(m.feed) - 1
	}
	return &m.feed[idx]
}

// clampFocus ensures m.focusedCardIdx is in [0, len(feed)-1] after a mutation.
func (m *model) clampFocus() {
	if len(m.feed) == 0 {
		m.focusedCardIdx = -1
		return
	}
	if m.focusedCardIdx < 0 {
		m.focusedCardIdx = len(m.feed) - 1
	}
	if m.focusedCardIdx >= len(m.feed) {
		m.focusedCardIdx = len(m.feed) - 1
	}
}
