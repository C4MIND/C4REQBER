// Package tui implements TUI v9 "The Cockpit" — single-screen feed-driven discovery UI.
package tui

import (
	"time"

	"charm.land/bubbles/v2/textarea"
	"charm.land/bubbles/v2/viewport"
	tea "charm.land/bubbletea/v2"

	"github.com/figuramax/c4reqber-tui-v9/api"
	"github.com/figuramax/c4reqber-tui-v9/effects"
	"github.com/figuramax/c4reqber-tui-v9/i18n"
	"github.com/figuramax/c4reqber-tui-v9/persist"
	"github.com/figuramax/c4reqber-tui-v9/telemetry"
)

// Card kinds.
type CardKind int

const (
	CardEmpty CardKind = iota
	CardPhase
	CardHypothesis
	CardPaper
	CardCode
	CardError
)

// Card is one row in the feed.
type Card struct {
	Kind     CardKind
	Title    string
	Body     string
	Meta     []string
	Actions  []string
	Time     time.Time
	Progress float64
	Status   string
}

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

	mode      Mode
	cost      float64
	running   bool
	jobID     string
	startedAt time.Time

	feed   []Card
	vp     viewport.Model
	follow bool

	ta    textarea.Model
	focus bool
	err   error
	toast string

	tick int

	// game-feel effects
	rain   *effects.Rain
	burst  *effects.Burst
	slide  *effects.SlideIn
	typew  *effects.Typewriter
	sparks *effects.Sparkles

	// SSE stream state
	sseEvents <-chan api.SSEEvent
	sseCancel func()

	// Mouse click zones (tracked for clickable cards)
	zoneIDs []string

	// Achievements + meta
	achievements     *AchievementSystem
	completedDisc    int
	langsSeen        map[string]bool
	lastQuality      float64
	lastPapersCount int

	// Persisted state (achievements, langs seen) and in-session telemetry
	store *persist.Store
	tel   *telemetry.Telemetry

	// showTelemetry toggles the bottom telemetry panel (Ctrl+T)
	showTelemetry bool

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
		event api.SSEEvent
		cancel func()
	}
	sseErrorMsg struct {
		err error
	}
	sseClosedMsg struct{}
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

// NewAppFresh creates a model without loading any persisted state (test-friendly).
// Use this in tests that need a clean slate.
func NewAppFresh(apiURL string) *model {
	cfg := DefaultConfig()
	if apiURL == "" {
		apiURL = cfg.APIURL
	}
	zoneId := 0
	_ = zoneId
	ta := textarea.New()
	ta.Placeholder = i18n.T("placeholder")
	ta.ShowLineNumbers = false
	ta.CharLimit = 0
	ta.SetWidth(80)
	ta.SetHeight(3)
	vp := viewport.New()
	m := &model{
		apiURL:       apiURL,
		api:          api.New(apiURL),
		mode:         ModeDiscover,
		ta:           ta,
		vp:           vp,
		focus:        true,
		follow:       true,
		rain:         effects.NewRain(),
		burst:        effects.NewBurst(),
		slide:        effects.NewSlideIn(),
		typew:        effects.NewTypewriter(),
		sparks:       effects.NewSparkles(),
		achievements: NewAchievements(),
		langsSeen:    map[string]bool{},
		tel:          telemetry.New(),
		dream:        NewDreamState(),
		llmTier:      TierC2,
		colorProfile: ProfileDefault,
		wizard:       NewWizardState(),
	}
	m.langsSeen[string(i18n.GetLang())] = true
	m.appendCard(Card{Kind: CardEmpty, Title: i18n.T("empty.title"), Body: i18n.T("empty.hint"), Time: time.Now()})
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
		apiURL:       apiURL,
		api:          api.New(apiURL),
		mode:         ModeDiscover,
		ta:           ta,
		vp:           vp,
		focus:        true,
		follow:       true,
		rain:         effects.NewRain(),
		burst:        effects.NewBurst(),
		slide:        effects.NewSlideIn(),
		typew:        effects.NewTypewriter(),
		sparks:       effects.NewSparkles(),
		achievements: NewAchievements(),
		langsSeen:    map[string]bool{},
		tel:          telemetry.New(),
		dream:        NewDreamState(),
		saveHistory:  true,
		llmTier:      TierC2,
		colorProfile: ProfileDefault,
		wizard:       NewWizardState(),
	}
	// Load persisted state (achievements, langs). If store fails, fall back gracefully.
	store, storeErr := persist.New(persist.DefaultPath())
	if storeErr == nil {
		m.store = store
		// Repopulate langsSeen from disk
		snap := store.Snapshot()
		for _, l := range snap.LangsSeen {
			m.langsSeen[l] = true
		}
	}
	m.langsSeen[string(i18n.GetLang())] = true
	// Apply persisted settings (tier/profile/lang)
	if m.store != nil {
		m.ApplySettings(m.store.GetSettings())
		// First-run wizard
		if m.store.IsFirstRun() {
			m.wizard.Show()
		}
	}
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

// MarkFirstRunDone marks the first-run wizard as completed in the persist store.
func (m *model) MarkFirstRunDone() {
	if m.store != nil {
		m.store.MarkFirstRunDone()
		_ = m.store.Save()
	}
}

// (no helpers needed — tests use persist.New directly)
