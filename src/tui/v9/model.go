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
		apiURL: apiURL,
		api:    api.New(apiURL),
		mode:   ModeDiscover,
		ta:     ta,
		vp:     vp,
		focus:  true,
		follow: true,
		rain:   effects.NewRain(),
		burst:  effects.NewBurst(),
		slide:  effects.NewSlideIn(),
		typew:  effects.NewTypewriter(),
		sparks: effects.NewSparkles(),
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
