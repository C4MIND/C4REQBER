package widgets

import (
	"fmt"
	"math/rand"
	"strings"
	"time"

	"c4tui/config"
	"c4tui/internal"
	"c4tui/styles"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
	"github.com/mattn/go-runewidth"
)

var (
	mascotCachedVersion uint64
	mascotDim           lipgloss.Style
	mascotDimItalic     lipgloss.Style
	mascotYellow        lipgloss.Style

)

func syncMascotStyles() {
	v := styles.ThemeVersion()
	if mascotCachedVersion == v {
		return
	}
	mascotCachedVersion = v
	mascotDim = lipgloss.NewStyle().Foreground(styles.ActiveTheme().Dim)
	mascotDimItalic = lipgloss.NewStyle().Foreground(styles.ActiveTheme().Dim).Italic(true)
	mascotYellow = lipgloss.NewStyle().Foreground(styles.ActiveTheme().Yellow)

}

// Emotion states for the companion cube.
type Emotion string

const (
	EmotionIdle      Emotion = "idle"
	EmotionThinking  Emotion = "thinking"
	EmotionHappy     Emotion = "happy"
	EmotionSurprised Emotion = "surprised"
	EmotionError     Emotion = "error"
)

// ---------------------------------------------------------------------------
// 3-frame ASCII cube (matching the landing-site mascot)
// ---------------------------------------------------------------------------

var cubeFrames = [3][6]string{
	0: {
		"   ┌─────────┐",
		"  ╱         ╱│",
		" ┌─────────┐ │",
		" │  C4R    │ │",
		" │  ███     ╱",
		" └─────────┘  ",
	},
	1: {
		"   ┌─────────┐",
		"  ╱ ∿∿∿∿∿∿∿ ╱│",
		" ┌─────────┐ │",
		" │  C4R    │ │",
		" │  ◈◈◈     ╱",
		" └─────────┘  ",
	},
	2: {
		"   ┌─────────┐",
		"  ╱ ▓▓▓▓▓▓▓ ╱│",
		" ┌─────────┐ │",
		" │  C4R    │ │",
		" │  ███     ╱",
		" └─────────┘  ",
	},
}

// ---------------------------------------------------------------------------
// Theme-aware cube palette
// ---------------------------------------------------------------------------

// cubeThemePalette returns (frameColor, accentColor, c4rColor) for the active theme.
func cubeThemePalette() (lipgloss.Color, lipgloss.Color, lipgloss.Color) {
	t := styles.ActiveTheme()
	switch t.Name {
	case "matrix":
		return lipgloss.Color(t.Green), lipgloss.Color(t.Success), lipgloss.Color(t.Highlight)
	case "paper":
		return lipgloss.Color(t.Primary), lipgloss.Color(t.Orange), lipgloss.Color(t.Success)
	default: // dark
		return lipgloss.Color(t.Cyan), lipgloss.Color(t.Yellow), lipgloss.Color(t.Success)
	}
}

// ---------------------------------------------------------------------------
// CubeMascot — friendly ASCII companion cube
// ---------------------------------------------------------------------------

// CubeMascot is the site-style companion cube for the TUI.
type CubeMascot struct {
	Emotion    Emotion
	FrameIdx   int // 0-2 for the 3 cube frames
	Stats      internal.MascotMemory
	Musing     string
	lastMusing time.Time
	emotionSet time.Time
	lastHappy  time.Time
	cfg        config.Config
	width      int
	height     int
	// Pipeline linkage
	PipelineRunning bool
	CurrentPhase    int // 0-6, -1 if none
	// Jump animation (triggered on S-rank discovery)
	Jumping   bool
	jumpStart time.Time
}

// IdleTickMsg triggers cube animation frame.
type IdleTickMsg struct{}

// NewMascot creates a new companion cube mascot with persistent memory.
func NewMascot(cfg config.Config) CubeMascot {
	return CubeMascot{
		Emotion:      EmotionIdle,
		Stats:        internal.LoadMascotMemory(),
		Musing:       cubeMusings[rand.Intn(len(cubeMusings))],
		lastMusing:   time.Now(),
		cfg:          cfg,
		CurrentPhase: -1,
	}
}

var cubeMusings = []string{
	"Ready when you are.",
	"What shall we discover today?",
	"The best ideas start with a question.",
	"Trust the process. Verify everything.",
	"Sources are the foundation of rigor.",
	"Every paper is a stepping stone.",
	"Think. Simulate. Prove. Discover.",
	"Curiosity is the prime operator.",
	"Navigate the lattice wisely.",
	"Discovery favors the prepared mind.",
	"What gap will you bridge today?",
	"From framing to synthesis — the path matters.",
	"A hypothesis is a bridge to truth.",
	"Knowledge is a graph, not a list.",
	"Your research companion awaits.",
	"Patterns emerge from careful observation.",
	"The cube grows with every discovery.",
	"Ready to explore the unknown?",
	"Let's turn questions into insights.",
	"Research is a journey, not a destination.",
	"What problem caught your eye?",
	"I am here to help you think deeper.",
	"The lattice never stops expanding.",
	"Build on what came before.",
	"Clarity emerges from structure.",
}

// SetEmotion changes the cube's emotional state.
func (m *CubeMascot) SetEmotion(e Emotion) {
	if m.Emotion == e {
		return
	}
	m.Emotion = e
	m.emotionSet = time.Now()
	if e == EmotionHappy {
		m.lastHappy = time.Now()
	}
}

// OnDiscovery increments stats and triggers happy state.
func (m *CubeMascot) OnDiscovery() {
	m.Stats.OnDiscovery()
	m.SetEmotion(EmotionHappy)
}

// Jump triggers a rapid frame-flip animation (S-rank celebration).
func (m *CubeMascot) Jump() {
	m.Jumping = true
	m.jumpStart = time.Now()
}

// SetPipelineState links mascot to current pipeline phase.
func (m *CubeMascot) SetPipelineState(running bool, phase int) {
	m.PipelineRunning = running
	m.CurrentPhase = phase
}

// Update handles animation ticks and emotion timeouts.
func (m CubeMascot) Update(msg tea.Msg) (CubeMascot, tea.Cmd) {
	switch msg.(type) {
	case IdleTickMsg:
		// Handle jump animation first
		if m.Jumping {
			elapsed := time.Since(m.jumpStart)
			if elapsed < 1_200*time.Millisecond {
				// Rapid flip: 0→1→2→1→0 over 1.2s at 200ms intervals
				step := int(elapsed / (200 * time.Millisecond))
				switch step {
				case 0, 4:
					m.FrameIdx = 0
				case 1, 3:
					m.FrameIdx = 1
				case 2:
					m.FrameIdx = 2
				}
				return m, tea.Tick(200*time.Millisecond, func(_ time.Time) tea.Msg { return IdleTickMsg{} })
			}
			m.Jumping = false
		}

		// Advance frame based on emotion
		switch m.Emotion {
		case EmotionThinking:
			// Fast blink between frame 0 and 1
			m.FrameIdx = (m.FrameIdx + 1) % 2
		case EmotionHappy:
			m.FrameIdx = 0 // steady happy frame
		case EmotionSurprised:
			m.FrameIdx = 2 // filled frame
		case EmotionError:
			m.FrameIdx = 0 // steady error frame
		default:
			// Idle: slow cycle through all 3 frames
			m.FrameIdx = (m.FrameIdx + 1) % 3
		}

		// Rotate musing every 15s
		if time.Since(m.lastMusing) > 15*time.Second {
			m.Musing = cubeMusings[rand.Intn(len(cubeMusings))]
			m.lastMusing = time.Now()
		}

		// Emotion timeouts
		if m.Emotion == EmotionHappy && time.Since(m.lastHappy) > 10*time.Second {
			m.Emotion = EmotionIdle
		}
		if m.Emotion == EmotionSurprised && time.Since(m.emotionSet) > 5*time.Second {
			m.Emotion = EmotionIdle
		}
		if m.Emotion == EmotionError && time.Since(m.emotionSet) > 8*time.Second {
			m.Emotion = EmotionIdle
		}
		if m.Emotion == EmotionThinking && time.Since(m.emotionSet) > 30*time.Second {
			m.Emotion = EmotionIdle
		}

		return m, tea.Tick(2*time.Second, func(_ time.Time) tea.Msg { return IdleTickMsg{} })
	}
	return m, nil
}

// Init starts the cube tick loop.
func (m CubeMascot) Init() tea.Cmd {
	return tea.Tick(2*time.Second, func(_ time.Time) tea.Msg { return IdleTickMsg{} })
}

// ---------------------------------------------------------------------------
// ASCII Art Engine
// ---------------------------------------------------------------------------

// buildCube renders the current ASCII cube frame.
func (m CubeMascot) buildCube() [6]string {
	frame := cubeFrames[m.FrameIdx]
	var lines [6]string
	for i := 0; i < 6; i++ {
		lines[i] = frame[i]
	}
	return lines
}

// View renders the cube + stats + musing + pipeline pulse.
func (m CubeMascot) View(width int) string {
	w := m.width
	if w == 0 {
		w = width
	}
	syncMascotStyles()

	cubeLines := m.buildCube()

	// Theme-aware palette
	frameColor, accentColor, c4rColor := cubeThemePalette()

	// Emotion overrides
	switch m.Emotion {
	case EmotionThinking:
		frameColor = lipgloss.Color(styles.ActiveTheme().Yellow)
		accentColor = lipgloss.Color(styles.ActiveTheme().Orange)
	case EmotionHappy:
		frameColor = lipgloss.Color(styles.ActiveTheme().Success)
		accentColor = lipgloss.Color(styles.ActiveTheme().Success)
	case EmotionSurprised:
		frameColor = lipgloss.Color(styles.ActiveTheme().Orange)
		accentColor = lipgloss.Color(styles.ActiveTheme().Red)
	case EmotionError:
		frameColor = lipgloss.Color(styles.ActiveTheme().Red)
		accentColor = lipgloss.Color(styles.ActiveTheme().Red)
	}

	// Jump override: gold glow
	if m.Jumping {
		frameColor = lipgloss.Color(styles.ActiveTheme().Yellow)
		accentColor = lipgloss.Color(styles.ActiveTheme().Orange)
		c4rColor = lipgloss.Color(styles.ActiveTheme().Yellow)
	}

	frameStyle := lipgloss.NewStyle().Foreground(frameColor)
	accentStyle := lipgloss.NewStyle().Foreground(accentColor).Bold(true)
	c4rStyle := lipgloss.NewStyle().Foreground(c4rColor).Bold(true)

	coloredLines := make([]string, 0, len(cubeLines))
	for _, line := range cubeLines {
		styled := make([]string, 0, len([]rune(line)))
		for _, ch := range line {
			s := string(ch)
			switch ch {
			case '█', '▓':
				styled = append(styled, accentStyle.Render(s))
			case '∿', '◈':
				styled = append(styled, frameStyle.Render(s))
			case '┌', '┐', '└', '┘', '─', '│', '╱':
				styled = append(styled, frameStyle.Render(s))
			case 'C', '4', 'R':
				styled = append(styled, c4rStyle.Render(s))
			default:
				styled = append(styled, mascotDim.Render(s))
			}
		}
		coloredLines = append(coloredLines, strings.Join(styled, ""))
	}

	cubeBlock := strings.Join(coloredLines, "\n")

	// Pipeline pulse (shows when pipeline running)
	var pulse string
	if m.PipelineRunning {
		pulseSymbols := []string{"─", "═", "─", "═"}
		p := pulseSymbols[m.FrameIdx%4]
		pulseLine := mascotYellow.Render(p + p + p + p + p)
		pulse = "\n" + mascotDim.Render(" running ") + pulseLine
	}

	// Title
	title := lipgloss.NewStyle().Bold(true).Foreground(frameColor).Render(internal.T("mascot.title"))

	// Personality based on stats
	personality := m.Stats.Personality()
	personaLine := mascotDimItalic.Render(personality)

	// Stats bars
	stats := lipgloss.JoinVertical(lipgloss.Left,
		m.statBar(internal.T("mascot.stat.energy"), m.Stats.Energy, lipgloss.Color(styles.ActiveTheme().Cyan)),
		m.statBar(internal.T("mascot.stat.bond"), m.Stats.Bond, lipgloss.Color(styles.ActiveTheme().Yellow)),
		m.statBar(internal.T("mascot.stat.insight"), m.Stats.Curiosity, lipgloss.Color(styles.ActiveTheme().Purple)),
	)

	// Musing
	musing := mascotDimItalic.Render(m.Musing)

	// Compose left side (cube + pulse) with right side (stats)
	cubeWithPulse := cubeBlock + pulse
	body := lipgloss.JoinHorizontal(lipgloss.Top, cubeWithPulse, "  ", stats)

	content := lipgloss.JoinVertical(lipgloss.Left,
		title,
		"",
		body,
		"",
		personaLine,
		musing,
	)

	h := m.height
	if h == 0 {
		h = m.cfg.Layout.MascotHeight
	}
	return styles.Panel(w, h).Render(content)
}

func (m CubeMascot) statBar(label string, val int, color lipgloss.Color) string {
	barLen := 10
	filled := val * barLen / 100
	if filled < 0 {
		filled = 0
	}
	if filled > barLen {
		filled = barLen
	}
	empty := barLen - filled
	bar := lipgloss.NewStyle().Foreground(color).Render(strings.Repeat("█", filled)) +
		lipgloss.NewStyle().Foreground(lipgloss.Color(styles.ActiveTheme().Dim)).Render(strings.Repeat("░", empty))
	// Pad label to 7 visible columns using runewidth for CJK/emoji safety
	labelW := runewidth.StringWidth(label)
	pad := ""
	if labelW < 7 {
		pad = strings.Repeat(" ", 7-labelW)
	}
	return label + pad + " " + bar + " " + fmt.Sprintf("%d%%", val)
}

// SetSize updates panel dimensions.
func (m *CubeMascot) SetSize(width, height int) {
	m.width = width
	m.height = height
}
