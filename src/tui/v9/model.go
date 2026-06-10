package tui

import (
	"time"

	"charm.land/bubbles/v2/textarea"
	"charm.land/bubbles/v2/viewport"
	tea "charm.land/bubbletea/v2"
)

// Card kinds — append-only, displayed bottom-up in feed.
type CardKind int

const (
	CardEmpty CardKind = iota
	CardPhase
	CardHypothesis
	CardPaper
	CardCode
	CardError
)

// Card is one row in the feed. Each card has a fixed visual layout per Kind.
type Card struct {
	Kind     CardKind
	Title    string
	Body     string
	Meta     []string // provenance, source, status
	Actions  []string // e.g. ["[o] Open", "[y] Copy"]
	Time     time.Time
	Progress float64 // 0.0..1.0, only for CardPhase
	Status   string  // "running" | "done" | "error"
}

// Mode — what kind of discovery.
type Mode string

const (
	ModeDiscover Mode = "DISCOVER"
	ModeFlash    Mode = "FLASH"
)

// model is the top-level state.
type model struct {
	apiURL string
	width  int
	height int

	mode      Mode
	cost      float64
	costTick  string
	running   bool
	jobID     string
	startedAt time.Time

	feed   []Card
	vp     viewport.Model
	follow bool // auto-scroll to bottom

	ta     textarea.Model
	focus  bool
	err    error
	toast  string

	tick int // 60Hz counter for animations

	// game-feel effects
	rain    *Rain
	burst   *Burst
	slide   *SlideIn
	typew   *Typewriter
	sparks  *Sparkles

	// typewriter buffer
	typoTarget Card
}

// message types
type (
	apiHealthMsg struct{ csrf string }
	apiAuthMsg   struct {
		token string
		err   error
	}
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
	tickMsg time.Time
)

// satisfies tea.Model
var _ tea.Model = (*model)(nil)

// NewApp exported constructor for cmd/c4tui-v9.
func NewApp(apiURL string) *model {
	ta := textarea.New()
	ta.Placeholder = "design a CRISPR guide RNA with minimal off-targets in T-cells…"
	ta.Prompt = "❯ "
	ta.SetWidth(80)
	ta.SetHeight(3)
	ta.Focus()

	vp := viewport.New(viewport.WithWidth(80), viewport.WithHeight(20))
	vp.MouseWheelEnabled = true

	m := &model{
		apiURL: apiURL,
		mode:   ModeDiscover,
		ta:     ta,
		vp:     vp,
		focus:  true,
		follow: true,
		rain:   NewRain(),
		burst:  NewBurst(),
		slide:  NewSlideIn(),
		typew:  NewTypewriter(),
		sparks: NewSparkles(),
	}
	m.appendCard(Card{Kind: CardEmpty, Title: T("empty.title"), Body: T("empty.hint"), Time: time.Now()})
	return m
}

func (m *model) Init() tea.Cmd {
	return tea.Batch(tea.RequestBackgroundColor, m.tickCmd(), m.pollTickCmd())
}

func (m *model) tickCmd() tea.Cmd {
	return tea.Tick(time.Millisecond*16, func(t time.Time) tea.Msg { return tickMsg(t) })
}

// pollTickCmd fires every 2s while a job is running.
func (m *model) pollTickCmd() tea.Cmd {
	return tea.Tick(time.Second*2, func(t time.Time) tea.Msg { return pollTickMsg(t) })
}

type pollTickMsg time.Time

func (p pollTickMsg) String() string { return "poll-tick" }
