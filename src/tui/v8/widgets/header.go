package widgets

import (
	"fmt"
	"net"
	"os"
	"time"

	"c4tui/config"
	"c4tui/styles"
	"github.com/charmbracelet/bubbles/spinner"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
)

// Header shows branding, API status, discovery count, clock, LLM status, and research ticker.
type Header struct {
	Discoveries    int
	Online         bool
	Loading        bool
	Clock          string
	Spinner        spinner.Model
	HealthCheck    func() bool
	Flag           string
	ThemeName      string
	C4Label        string
	Language       string
	LLMStatus      string
	DiscoveryPulse string // temporary "+1" indicator
	TimeEmoji      string // cached to avoid time.Now() syscall every frame
	cfg            config.Config

	// Research ticker state
	researchIdx   int
	researchPhase int // 0 = discovery, 1 = open problem
}

// researchDiscoveries — recent breakthroughs from science & engineering.
var researchDiscoveries = []string{
	"Quantum error suppression via cat codes (Nature 2024)",
	"Room-temperature superconductor LK-99 partial replication (arXiv)",
	"CRISPR-based in vivo gene editing Phase III success",
	"JWST detects earliest galaxy merger at z~14",
	"AlphaFold3 predicts protein-DNA-RNA complexes",
	"Solid-state battery with 1000+ cycles (Toyota/Tesla)",
	"Fusion energy net gain repeated at NIF (LLNL)",
	"Brain-computer interface enables speech decoding (Stanford)",
	"Self-healing concrete using bacterial spores (Delft)",
	"Photonic chip achieves petaflops at milliwatts (MIT)",
}

// openProblems — unsolved scientific & engineering challenges.
var openProblems = []string{
	"P vs NP — Clay Millennium Prize Problem",
	"Dark matter direct detection (LZ/XENON limits)",
	"Fusion energy net-gain sustainability >1 hour",
	"General AI alignment & interpretability",
	"Carbon capture at <$30/tonne industrial scale",
	"Room-temperature ambient-pressure superconductor",
	"Cancer vaccine with >90% efficacy across types",
	"Reversible cryopreservation of whole organs",
	"Dyson swarm construction feasibility & economics",
	"Quantum gravity unification (string/loop wars)",
}

// NewHeader creates a styled header.
func NewHeader(cfg config.Config) Header {
	s := spinner.New()
	s.Spinner = spinner.Points
	return Header{
		Spinner:   s,
		C4Label:   "F⟨1,1,0⟩",
		Language:  "EN",
		Flag:      "🇬🇧",
		LLMStatus: "...",
		cfg:       cfg,
	}
}

// Init returns tick commands for clock, ticker, and health check.
func (h Header) Init() tea.Cmd {
	return tea.Batch(
		h.Spinner.Tick,
		clockTickCmd(),
		tickerTickCmd(),
		h.runHealthCheck(),
		checkLLMCmd(),
	)
}

// Update handles time ticks, ticker rotation, and async health results.
func (h Header) Update(msg tea.Msg) (Header, tea.Cmd) {
	switch msg := msg.(type) {
	case clockTickMsg:
		// Use 15:04 format because tick interval is 5s — seconds would be stale.
		h.Clock = time.Now().Format("15:04")
		h.TimeEmoji = timeEmoji()
		return h, tea.Batch(clockTickCmd(), h.runHealthCheck(), checkLLMCmd())
	case healthResultMsg:
		h.Online = msg.ok
		return h, nil
	case pulseClearMsg:
		h.DiscoveryPulse = ""
		return h, nil
	case tickerTickMsg:
		// Alternate between discoveries and open problems every 5s
		h.researchPhase = 1 - h.researchPhase
		if h.researchPhase == 0 {
			h.researchIdx = (h.researchIdx + 1) % len(researchDiscoveries)
		} else {
			h.researchIdx = (h.researchIdx + 1) % len(openProblems)
		}
		return h, tickerTickCmd()
	case llmStatusMsg:
		h.LLMStatus = msg.status
		return h, nil
	default:
		var cmd tea.Cmd
		h.Spinner, cmd = h.Spinner.Update(msg)
		return h, cmd
	}
}

// runHealthCheck returns a command that checks health asynchronously.
func (h Header) runHealthCheck() tea.Cmd {
	if h.HealthCheck == nil {
		return nil
	}
	check := h.HealthCheck
	return func() tea.Msg {
		return healthResultMsg{ok: check()}
	}
}

var (
	headerCachedVersion uint64
	headerDim           lipgloss.Style
	headerYellow        lipgloss.Style
)

func syncHeaderStyles() {
	v := styles.ThemeVersion()
	if headerCachedVersion == v {
		return
	}
	headerCachedVersion = v
	headerDim = lipgloss.NewStyle().Foreground(styles.ActiveTheme().Dim)
	headerYellow = lipgloss.NewStyle().Foreground(styles.ActiveTheme().Yellow)
}

// View renders the header bar (2 lines, v7 parity).
func (h Header) View(width int) string {
	syncHeaderStyles()

	// Core status dot
	coreDot := styles.Success().Render("●")
	if h.Loading {
		coreDot = h.Spinner.View()
	}

	// API status
	apiStatus := styles.Success().Render("+ online")
	if !h.Online {
		apiStatus = styles.Error().Render("_ offline")
	}

	// Build responsive line 1 — hide less critical elements as width shrinks
	parts := []string{}
	parts = append(parts, styles.Title().Render("* C4REQBER v8 ")+coreDot)

	if width >= 40 {
		parts = append(parts, headerDim.Render(fmt.Sprintf("* %s", h.C4Label)))
	}
	if width >= 50 {
		langBadge := headerYellow.Render(h.Flag + " " + h.Language)
		parts = append(parts, langBadge)
	}
	if width >= 70 {
		llmDisplay := headerDim.Render("LLM: " + h.LLMStatus)
		parts = append(parts, llmDisplay)
	}
	if width >= 60 {
		parts = append(parts, headerDim.Render("API:")+apiStatus)
	}
	if width >= 55 {
		parts = append(parts, headerDim.Render(fmt.Sprintf("💎 %d%s", h.Discoveries, h.DiscoveryPulse)))
	}
	if width >= 45 {
		parts = append(parts, timeEmoji()+" "+h.Clock)
	}

	line1Left := lipgloss.JoinHorizontal(lipgloss.Top, parts...)
	// Insert spacing between header elements so they don't bleed together
	var spaced []string
	for i, p := range parts {
		spaced = append(spaced, p)
		if i < len(parts)-1 {
			spaced = append(spaced, "  ")
		}
	}
	line1Left = lipgloss.JoinHorizontal(lipgloss.Top, spaced...)

	// Line 2: research ticker (discoveries ↔ open problems)
	line2 := h.renderResearchTicker()

	return lipgloss.NewStyle().Width(width).Render(
		line1Left + "\n" + line2,
	)
}

// renderResearchTicker shows rotating discoveries (🔬) and open problems (❓).
func (h Header) renderResearchTicker() string {
	if h.researchPhase == 0 {
		return styles.ResearchSuccessStyle().Render("🔬 " + researchDiscoveries[h.researchIdx%len(researchDiscoveries)])
	}
	return styles.ResearchProblemStyle().Render("❓ " + openProblems[h.researchIdx%len(openProblems)])
}

// SetDiscoveryPulse triggers a temporary "+1" indicator.
func (h *Header) SetDiscoveryPulse() {
	h.DiscoveryPulse = styles.DiscoveryPulseStyle().Render("+1")
}

// Message types
type clockTickMsg struct{}
type healthResultMsg struct{ ok bool }
type pulseClearMsg struct{}
type tickerTickMsg struct{}
type llmStatusMsg struct{ status string }

// PulseClearCmd returns a command that clears the discovery pulse after 2s.
func PulseClearCmd() tea.Cmd {
	return tea.Tick(2*time.Second, func(t time.Time) tea.Msg {
		return pulseClearMsg{}
	})
}

func timeEmoji() string {
	hour := time.Now().Hour()
	switch {
	case hour >= 5 && hour < 12:
		return "🌅"
	case hour >= 12 && hour < 17:
		return "☀️"
	case hour >= 17 && hour < 21:
		return "🌇"
	default:
		return "🌙"
	}
}

func clockTickCmd() tea.Cmd {
	return tea.Tick(5*time.Second, func(t time.Time) tea.Msg {
		return clockTickMsg{}
	})
}

func tickerTickCmd() tea.Cmd {
	return tea.Tick(5*time.Second, func(t time.Time) tea.Msg {
		return tickerTickMsg{}
	})
}

func checkLLMCmd() tea.Cmd {
	return func() tea.Msg {
		statuses := []string{}
		theme := styles.ActiveTheme()

		// ollama — non-blocking env check
		if os.Getenv("OLLAMA_HOST") != "" {
			statuses = append(statuses, lipgloss.NewStyle().Foreground(theme.Green).Render("ollama"))
		} else {
			statuses = append(statuses, lipgloss.NewStyle().Foreground(theme.Dim).Render("ollama"))
		}

		// lmstudio — check with timeout in background to avoid blocking the event loop
		lmstudioOnline := make(chan bool, 1)
		go func() {
			conn, err := net.DialTimeout("tcp", "127.0.0.1:1234", 300*time.Millisecond)
			if err == nil {
				conn.Close()
				lmstudioOnline <- true
			} else {
				lmstudioOnline <- false
			}
		}()
		select {
		case online := <-lmstudioOnline:
			if online {
				statuses = append(statuses, lipgloss.NewStyle().Foreground(theme.Green).Render("lmstudio"))
			} else {
				statuses = append(statuses, lipgloss.NewStyle().Foreground(theme.Dim).Render("lmstudio"))
			}
		case <-time.After(400 * time.Millisecond):
			statuses = append(statuses, lipgloss.NewStyle().Foreground(theme.Dim).Render("lmstudio"))
		}

		// mlx — check env or dim
		if os.Getenv("MLX_MODEL") != "" || os.Getenv("MLX_PYTHON_PATH") != "" {
			statuses = append(statuses, lipgloss.NewStyle().Foreground(theme.Green).Render("mlx"))
		} else {
			statuses = append(statuses, lipgloss.NewStyle().Foreground(theme.Dim).Render("mlx"))
		}

		return llmStatusMsg{status: lipgloss.JoinHorizontal(lipgloss.Left, statuses...)}
	}
}
