package main

import (
	"context"
	"strconv"
	"strings"
	"time"

	"c4tui/backend"
	"c4tui/internal"
	"c4tui/screens"
	"c4tui/styles"
	"c4tui/widgets"
	tea "github.com/charmbracelet/bubbletea"
)

// Update handles all messages.
func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	// Route messages to active overlay first.
	if m.Overlay != nil {
		// Backend messages must ALWAYS reach the main model, even when overlay is open.
		// Animation ticks (spinner, time) must ALSO reach widgets so they don't freeze.
		switch msg.(type) {
		case backend.C4NavigateMsg, backend.DiscoverMsg, backend.FlashMsg,
			backend.TurboMsg, backend.TurboFactoryMsg, backend.SearchMsg,
			backend.VerifyMsg, backend.PhaseMsg, backend.JobCompleteMsg,
			backend.JobFailedMsg,
			backend.SSEStartedMsg, backend.SSEEventMsg, backend.SSEErrorMsg,
			pollTickMsg,
			tea.WindowSizeMsg:
			// fall through to main model routing below
		default:
			newOverlay, cmd := m.Overlay.Update(msg)
			if overlay, ok := newOverlay.(screens.Model); ok {
				m.Overlay = overlay
				if m.Overlay.Done() {
					m.Overlay = nil
					m.Screen = screens.ScreenNone
				}
			}
			return m, cmd
		}
	}

	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		m.Width = msg.Width
		m.Height = msg.Height

		l := m.computeLayout()
		m.C4Grid.SetSize(l.leftW, l.c4H)
		if l.showCube && l.mascotH > 0 {
			m.Mascot.SetSize(l.leftW, l.mascotH)
		} else {
			m.Mascot.SetSize(l.leftW, 0)
		}
		m.InputBar.SetSize(l.midW, l.inputH)
		m.Pipeline.SetSize(l.midW, l.pipeH)
		m.Result.SetSize(l.rightW, l.bodyH)
		m.Chat.SetSize(m.Width, l.chatH)

		var cmd tea.Cmd
		if m.Overlay != nil {
			var newOverlay tea.Model
			newOverlay, cmd = m.Overlay.Update(msg)
			if overlay, ok := newOverlay.(screens.Model); ok {
				m.Overlay = overlay
				if m.Overlay.Done() {
					m.Overlay = nil
					m.Screen = screens.ScreenNone
				}
			}
		}
		return m, cmd

	case shutdownMsg:
		// Graceful shutdown on SIGINT — flush session data before exit.
		if m.Store != nil {
			_ = m.Store.Flush()
		}
		return m, tea.Quit

	case widgets.C4PulseTickMsg:
		newGrid, gridCmd := m.C4Grid.Update(msg)
		m.C4Grid = newGrid
		return m, gridCmd

	case tea.KeyMsg:
		return m.handleKey(msg)

	case tea.MouseMsg:
		return m.handleMouse(msg)

	case backend.C4NavigateMsg:
		return m.handleC4NavigateMsg(msg)

	case backend.DiscoverMsg:
		return m.handleDiscoverMsg(msg)

	case backend.FlashMsg:
		return m.handleFlashMsg(msg)

	case backend.TurboMsg:
		return m.handleTurboMsg(msg)

	case backend.TurboFactoryMsg:
		return m.handleTurboFactoryMsg(msg)

	case backend.SearchMsg:
		return m.handleSearchMsg(msg)

	case backend.VerifyMsg:
		return m.handleVerifyMsg(msg)

	case backend.PhaseMsg:
		return m.handlePhaseMsg(msg)

	case backend.JobCompleteMsg:
		return m.handleJobCompleteMsg(msg)

	case backend.JobFailedMsg:
		return m.handleJobFailedMsg(msg)

	case backend.SSEStartedMsg:
		m.SSEActive = true
		m.SSEEvents = msg.Events
		m.SSEErrCh = msg.ErrCh
		m.Chat.Add("[pipeline] SSE stream connected")
		return m, backend.SSEPollCmd(msg.Events, msg.ErrCh)

	case backend.SSEEventMsg:
		// Convert SSE event to appropriate message and re-route
		sseMsg := backend.SSEEventToMsg(msg.Event)
		if sseMsg == nil {
			// Unknown event type — keep polling SSE
			return m, backend.SSEPollCmd(m.SSEEvents, m.SSEErrCh)
		}
		// Re-dispatch the converted message through Update
		newM, cmd := m.Update(sseMsg)
		if m2, ok := newM.(model); ok {
			m = m2
		}
		// If pipeline still running and we got a phase msg, continue SSE polling
		if m.Pipeline.Running && m.SSEActive {
			if _, isPhase := sseMsg.(backend.PhaseMsg); isPhase {
				return m, tea.Batch(cmd, backend.SSEPollCmd(m.SSEEvents, m.SSEErrCh))
			}
		}
		return m, cmd

	case backend.SSEErrorMsg:
		m.SSEActive = false
		if msg.Err != nil {
			m.Chat.Add("[warn] SSE error: " + msg.Err.Error() + "; falling back to polling")
		} else {
			m.Chat.Add("[warn] SSE disconnected, falling back to polling")
		}
		return m, m.pollTick()

	case pollTickMsg:
		return m.handlePollTick()
	case helpTipTickMsg:
		m.Help.RotateTip()
		return m, m.helpTipTick()

	case screens.ExportResultMsg:
		if msg.Err != nil {
			m.Chat.Add("[err] Export failed: " + msg.Err.Error())
		} else {
			m.Chat.Add("[export] Saved to " + msg.Path)
		}
		m.Overlay = nil
		m.Screen = screens.ScreenNone
		return m, nil

	case screens.PaletteMsg:
		m.Overlay = nil
		m.Screen = screens.ScreenNone
		return m.handlePaletteAction(msg.Action)
	}

	// Delegate to sub-widgets
	var cmd tea.Cmd
	cmds := []tea.Cmd{}

	m.Header, cmd = m.Header.Update(msg)
	cmds = append(cmds, cmd)
	m.InputBar, cmd = m.InputBar.Update(msg)
	cmds = append(cmds, cmd)
	m.Chat, cmd = m.Chat.Update(msg)
	cmds = append(cmds, cmd)
	m.Mascot, cmd = m.Mascot.Update(msg)
	cmds = append(cmds, cmd)
	m.Result, cmd = m.Result.Update(msg)
	cmds = append(cmds, cmd)
	m.Pipeline, cmd = m.Pipeline.Update(msg)
	cmds = append(cmds, cmd)

	return m, tea.Batch(cmds...)
}

func (m model) handleKey(msg tea.KeyMsg) (tea.Model, tea.Cmd) {
	switch msg.String() {
	case "ctrl+c":
		if m.CancelCtx != nil {
			m.CancelCtx()
		}
		return m, tea.Quit
	case "q":
		// Only quit on bare 'q' if textarea is empty (not typing)
		if m.InputBar.TextArea.Value() == "" {
			if m.CancelCtx != nil {
				m.CancelCtx()
			}
			return m, tea.Quit
		}
		// Otherwise let it pass to textarea
		var cmd tea.Cmd
		m.InputBar, cmd = m.InputBar.Update(msg)
		return m, cmd
	case "esc":
		if m.Pipeline.Running && m.CancelCtx != nil {
			m.CancelCtx()
			m.CancelCtx = nil
			m.PipelineCtx = nil
			m.Pipeline.Stop()
			m.Chat.Add("[warn] Pipeline cancelled")
			m.showToast("◼ Pipeline cancelled", "warn")
			m.Mascot.SetEmotion(widgets.EmotionIdle)
			return m, nil
		}
	case "f2":
		m.Chat.Expanded = !m.Chat.Expanded
		return m, nil
	case "?":
		// Only open help on bare '?' if not typing in textarea
		if m.InputBar.TextArea.Value() == "" {
			m.Screen = screens.ScreenHelp
			return openOverlay(m, screens.NewHelp())
		}
		// Let '?' pass through to textarea
		var cmd tea.Cmd
		m.InputBar, cmd = m.InputBar.Update(msg)
		return m, cmd
	case "tab":
		// Tab accepts mode suggestion if one is pending
		if m.InputBar.SuggestedMode != "" && m.InputBar.SuggestedMode != m.InputBar.Mode {
			m.InputBar.SetMode(m.InputBar.SuggestedMode)
			return m, nil
		}
		// Only route Tab to C4Grid when textarea is empty (not actively typing)
		if m.InputBar.TextArea.Value() == "" {
			newGrid, gridCmd := m.C4Grid.Update(msg)
			m.C4Grid = newGrid
			return m, gridCmd
		}
		// Let Tab pass through to textarea for indentation
		var cmd tea.Cmd
		m.InputBar, cmd = m.InputBar.Update(msg)
		return m, cmd
	case "up", "down":
		// History navigation when at top/bottom of textarea
		ta := m.InputBar.TextArea
		if msg.String() == "up" && ta.Line() == 0 {
			newBar, _ := m.InputBar.Update(widgets.HistoryUpMsg{})
			m.InputBar = newBar
			return m, nil
		}
		if msg.String() == "down" && ta.Line() >= ta.LineCount()-1 {
			newBar, _ := m.InputBar.Update(widgets.HistoryDownMsg{})
			m.InputBar = newBar
			return m, nil
		}
		// Otherwise pass to textarea for cursor movement
		var cmd tea.Cmd
		m.InputBar, cmd = m.InputBar.Update(msg)
		return m, cmd
	case "left", "right", "shift+up", "shift+down":
		// Only route arrows to C4Grid when textarea is empty (not actively typing)
		if m.InputBar.TextArea.Value() == "" {
			newGrid, gridCmd := m.C4Grid.Update(msg)
			m.C4Grid = newGrid
			return m, gridCmd
		}
		// Let arrow keys pass through to textarea for cursor movement
		var cmd tea.Cmd
		m.InputBar, cmd = m.InputBar.Update(msg)
		return m, cmd
	case "ctrl+enter":
		return m.startPipeline(m.InputBar.Mode)
	case "ctrl+f":
		m.InputBar.SetMode("flash")
		m.showToast("⚡ Flash mode", "info")
		return m, nil
	case "ctrl+d":
		m.InputBar.SetMode("discover")
		m.showToast("🔍 Discover mode", "info")
		return m, nil
	case "shift+d":
		m.Screen = screens.ScreenDashboard
		return openOverlay(m, screens.NewDashboard(m.Store))
	case "ctrl+t":
		m.InputBar.SetMode("turbo")
		m.showToast("🔬 Turbo mode", "info")
		return m, nil
	case "ctrl+shift+t":
		m.InputBar.SetMode("turbofactory")
		m.showToast("📦 TurboFactory mode", "info")
		return m.startTurboFactory()
	case "ctrl+s":
		m.InputBar.SetMode("search")
		m.showToast("🔎 Search mode", "info")
		return m, nil
	case "ctrl+v":
		m.InputBar.SetMode("verify")
		m.showToast("✓ Verify mode", "info")
		return m, nil
	case "shift+e":
		m.Screen = screens.ScreenExport
		return openOverlay(m, screens.NewExportPicker(m.LastResult))
	case "shift+p":
		m.Screen = screens.ScreenPalette
		return openOverlay(m, screens.NewPalette())
	case "shift+l":
		m.Language = internal.NextLanguage(m.Language)
		internal.ActiveLanguage = m.Language
		m.Header.Flag = internal.LanguageFlags[m.Language]
		m.Chat.Add("[lang] " + internal.LanguageNames[m.Language])
		m.showToast("Language: "+internal.LanguageNames[m.Language], "info")
		return m, nil
	case "shift+h":
		t := styles.CycleTheme()
		m.Header.ThemeName = t.Name
		m.Pipeline.SetThemeColors()
		m.Chat.Add("[theme] Switched to " + t.Name)
		m.showToast("Theme: "+t.Name, "info")
		return m, nil
	case "shift+o":
		m.Screen = screens.ScreenDissertation
		return openOverlay(m, screens.NewDissertation(m.LastResult))
	case "shift+y":
		m.Screen = screens.ScreenHistory
		return openOverlay(m, screens.NewHistoryTable(m.Store))
	case "shift+k":
		m.Screen = screens.ScreenKnowledgeGraph
		return openOverlay(m, screens.NewKnowledgeGraph(m.Store))
	case "ctrl+m":
		m.Screen = screens.ScreenMatrixRain
		return openOverlay(m, screens.NewMatrixRain())
	case "shift+x":
		m.Screen = screens.ScreenDiagnostic
		return openOverlay(m, screens.NewDiagnostic(m.Backend))
	case "shift+b":
		m.Screen = screens.ScreenBibliography
		return openOverlay(m, screens.NewBibliography(m.LastResult))
	case "ctrl+r":
		m.Screen = screens.ScreenTRIZ
		return openOverlay(m, screens.NewTRIZ())
	case "shift+v":
		m.Screen = screens.ScreenProvider
		return openOverlay(m, screens.NewProvider())
	case "shift+c":
		m.Screen = screens.ScreenCache
		return openOverlay(m, screens.NewCacheInspector())
	case "shift+n":
		m.Screen = screens.ScreenSocial
		topic := ""
		if m.LastResult != nil {
			if p, ok := m.LastResult["problem"].(string); ok {
				topic = p
			}
		}
		quality := "unknown"
		if m.LastResult != nil {
			if q, ok := m.LastResult["quality"].(string); ok {
				quality = q
			}
		}
		return openOverlay(m, screens.NewSocialSharing(topic, quality))
	case "shift+g":
		m.Screen = screens.ScreenGPU
		return openOverlay(m, screens.NewGPUMonitor())
	case "shift+i":
		m.Screen = screens.ScreenPackages
		return openOverlay(m, screens.NewPackageInstaller())
	case "shift+a":
		m.Screen = screens.ScreenAgenda
		return openOverlay(m, screens.NewAgenda())
	}
	// TextArea handles everything else
	var cmd tea.Cmd
	m.InputBar, cmd = m.InputBar.Update(msg)
	m.InputBar.AnalyzeSuggest()
	m.lastTyping = time.Now()
	if m.InputBar.TextArea.Value() != "" && m.Mascot.Emotion == widgets.EmotionIdle {
		m.Mascot.SetEmotion(widgets.EmotionThinking)
	}
	return m, cmd
}

func (m model) handleMouse(msg tea.MouseMsg) (tea.Model, tea.Cmd) {
	if msg.Action != tea.MouseActionPress || msg.Button != tea.MouseButtonLeft {
		return m, nil
	}
	l := m.computeLayout()

	// Mode buttons are in the middle/right column depending on layout mode.
	// In 3-col they are in mid; in 2-col they are in right; in 1-col they are full-width.
	var inputX0, inputX1, inputY0 int
	if l.veryNarrow {
		inputX0 = 0
		inputX1 = l.width
		inputY0 = l.headerH + l.sepH + l.c4H
	} else if l.narrow {
		inputX0 = l.leftW
		inputX1 = l.width
		inputY0 = l.headerH + l.sepH
	} else {
		inputX0 = l.leftW
		inputX1 = inputX0 + l.midW
		inputY0 = l.headerH + l.sepH
	}
	if msg.X >= inputX0 && msg.X < inputX1 && msg.Y >= inputY0 {
		mode := m.InputBar.ClickAt(msg.X-inputX0, msg.Y-inputY0)
		if mode != "" {
			m.InputBar.SetMode(mode)
			m.showToast("Mode: "+mode, "info")
			return m, nil
		}
	}

	// C4Grid is in the left column; clicking anywhere in it advances state.
	c4Y1 := l.headerH + l.sepH + l.c4H
	if msg.X < l.leftW && msg.Y >= l.headerH+l.sepH && msg.Y < c4Y1 {
		m.C4Grid.Click()
		return m, nil
	}

	// Help bar click: toggle help overlay
	helpY0 := l.headerH + l.sepH + l.bodyH
	helpY1 := helpY0 + l.helpH
	if l.helpH == 0 {
		helpY1 = helpY0 + 1 // collapsed help is 1 line
	}
	if msg.Y >= helpY0 && msg.Y < helpY1 {
		m.Help.Toggle()
		return m, nil
	}

	// Chat bar click: toggle chat expand/collapse
	chatY0 := helpY1
	chatY1 := chatY0 + l.chatH
	if msg.Y >= chatY0 && msg.Y < chatY1 {
		m.Chat.Expanded = !m.Chat.Expanded
		return m, nil
	}

	return m, nil
}

// ---------------------------------------------------------------------------
// Pipeline lifecycle
// ---------------------------------------------------------------------------

func (m model) showToast(msg, kind string) {
	m.Toast.Show(msg, kind)
}

func (m model) startPipeline(mode string) (tea.Model, tea.Cmd) {
	if m.Pipeline.Running {
		m.Chat.Add("[warn] Pipeline already running")
		return m, nil
	}
	topic := internal.Input(m.InputBar.TextArea.Value())
	if topic == "" {
		m.Chat.Add("[warn] Enter a problem first")
		return m, nil
	}
	if len(topic) > m.Cfg.Layout.MaxInputLen {
		m.Chat.Add("[warn] Input too long (max " + strconv.Itoa(m.Cfg.Layout.MaxInputLen) + ")")
		return m, nil
	}

	if err := m.Store.SetLastInput(topic); err != nil {
		m.Chat.Add("[warn] Failed to save input: " + err.Error())
	}
	m.lastTopic = topic
	m.PipelineMode = mode
	m.Pipeline.Start()
	m.Mascot.SetPipelineState(true, 0)
	m.Mascot.SetEmotion(widgets.EmotionThinking)
	m.Chat.Add("[pipeline] Starting " + mode + " mode...")
	m.showToast("▶ Running "+mode+" mode...", "info")

	// Create a cancellable context for the entire pipeline lifecycle.
	m.PipelineCtx, m.CancelCtx = context.WithCancel(context.Background())

	// First, navigate C4 to visualise the cognitive path.
	return m, tea.Batch(
		backend.C4NavigateCmd(m.PipelineCtx, m.Backend, topic),
		m.pollTick(),
	)
}

func (m model) pollTick() tea.Cmd {
	if m.pollTimer != nil {
		m.pollTimer.Stop()
	}
	m.pollTimer = time.NewTimer(m.Cfg.API.PollInterval)
	return func() tea.Msg {
		<-m.pollTimer.C
		return pollTickMsg{}
	}
}

// pollTickMsg triggers the next poll if a job is running.
type pollTickMsg struct{}
type helpTipTickMsg struct{}

func (m model) helpTipTick() tea.Cmd {
	return tea.Tick(8*time.Second, func(_ time.Time) tea.Msg {
		return helpTipTickMsg{}
	})
}

func (m model) handlePollTick() (tea.Model, tea.Cmd) {
	if !m.Pipeline.Running || m.JobID == "" || m.PipelineCtx == nil || m.SSEActive {
		return m, nil
	}
	return m, tea.Batch(
		backend.PollJobCmd(m.PipelineCtx, m.Backend, m.JobID),
		m.pollTick(),
	)
}

// ---------------------------------------------------------------------------
// Message handlers
// ---------------------------------------------------------------------------

func (m model) handleC4NavigateMsg(msg backend.C4NavigateMsg) (tea.Model, tea.Cmd) {
	if msg.Err != nil {
		m.Chat.Add("[warn] C4 navigation failed: " + msg.Err.Error())
		// Continue with pipeline anyway
	} else if msg.Resp != nil {
		m.C4Grid.SetPath(msg.Resp.Path)
		m.Chat.Add("[c4] Path: " + msg.Resp.Start + " -> " + msg.Resp.End)
	}

	// Now start the actual backend job using the captured topic.
	if m.PipelineCtx == nil {
		m.Chat.Add("[err] Pipeline cancelled before job start")
		m.Pipeline.Stop()
		return m, nil
	}
	var cmd tea.Cmd
	switch m.PipelineMode {
	case "flash":
		cmd = backend.FlashCmd(m.PipelineCtx, m.Backend, m.lastTopic, "science")
	case "turbo":
		cmd = backend.TurboCmd(m.PipelineCtx, m.Backend, m.lastTopic, "science")
	case "turbofactory":
		// TurboFactory bypasses C4 navigation; this case is a safety net.
		cmd = backend.TurboFactoryCmd(m.PipelineCtx, m.Backend, []string{m.lastTopic}, "science")
	case "search":
		cmd = backend.SearchCmd(m.PipelineCtx, m.Backend, m.lastTopic)
	case "verify":
		cmd = backend.VerifyCmd(m.PipelineCtx, m.Backend, m.lastTopic, "hoare")
	default:
		cmd = backend.DiscoverCmd(m.PipelineCtx, m.Backend, m.lastTopic, "science")
	}
	return m, cmd
}

func (m model) handleDiscoverMsg(msg backend.DiscoverMsg) (tea.Model, tea.Cmd) {
	if msg.Err != nil {
		m.Chat.Add("[err] Backend: " + msg.Err.Error())
		m.Mascot.SetEmotion(widgets.EmotionSurprised)
		if m.CancelCtx != nil {
			m.CancelCtx()
		}
		m.CancelCtx = nil
		m.PipelineCtx = nil
		m.Pipeline.Stop()
		return m, nil
	}
	m.JobID = msg.JobID
	m.Chat.Add("[pipeline] Job " + msg.JobID + " queued")
	if m.PipelineCtx == nil {
		m.Chat.Add("[err] Pipeline cancelled before SSE subscription")
		m.Pipeline.Stop()
		return m, nil
	}
	return m, tea.Batch(
		m.pollTick(),
		backend.SSESubscribeCmd(m.PipelineCtx, m.Backend, m.JobID),
	)
}

func (m model) handleFlashMsg(msg backend.FlashMsg) (tea.Model, tea.Cmd) {
	if msg.Err != nil {
		m.Chat.Add("[err] Backend: " + msg.Err.Error())
		m.Mascot.SetEmotion(widgets.EmotionSurprised)
		if m.CancelCtx != nil {
			m.CancelCtx()
		}
		m.CancelCtx = nil
		m.PipelineCtx = nil
		m.Pipeline.Stop()
		return m, nil
	}
	m.JobID = msg.JobID
	m.Chat.Add("[pipeline] Flash job " + msg.JobID + " queued")
	return m, tea.Batch(
		m.pollTick(),
		backend.SSESubscribeCmd(m.PipelineCtx, m.Backend, m.JobID),
	)
}

func (m model) handleSearchMsg(msg backend.SearchMsg) (tea.Model, tea.Cmd) {
	if m.CancelCtx != nil {
		m.CancelCtx()
	}
	m.CancelCtx = nil
	m.PipelineCtx = nil
	m.Pipeline.Stop()
	m.Mascot.SetPipelineState(false, -1)
	if msg.Err != nil {
		m.Chat.Add("[err] Search: " + msg.Err.Error())
		m.Mascot.SetEmotion(widgets.EmotionSurprised)
		return m, nil
	}
	m.Result.SetSearchResults(msg.Resp)
	m.Mascot.SetEmotion(widgets.EmotionHappy)
	m.Chat.Add("[search] Found " + strconv.Itoa(msg.Resp.Total) + " results")
	return m, nil
}

func (m model) handleVerifyMsg(msg backend.VerifyMsg) (tea.Model, tea.Cmd) {
	if m.CancelCtx != nil {
		m.CancelCtx()
	}
	m.CancelCtx = nil
	m.PipelineCtx = nil
	m.Pipeline.Stop()
	m.Mascot.SetPipelineState(false, -1)
	if msg.Err != nil {
		m.Chat.Add("[err] Verify: " + msg.Err.Error())
		m.Mascot.SetEmotion(widgets.EmotionSurprised)
		return m, nil
	}
	m.Result.SetVerifyResult(msg.Resp)
	status := "FAIL"
	if msg.Resp.Verified {
		status = "PASS"
	}
	m.Mascot.SetEmotion(widgets.EmotionHappy)
	m.Chat.Add("[verify] " + status + " (" + msg.Resp.Method + ")")
	return m, nil
}

func (m model) handlePhaseMsg(msg backend.PhaseMsg) (tea.Model, tea.Cmd) {
	if !m.Pipeline.Running {
		return m, nil
	}
	m.Pipeline.SetPhaseName(msg.Phase, msg.Status, msg.Progress)
	phaseIdx := widgets.PhaseIndex(msg.Phase)
	m.Mascot.SetPipelineState(true, phaseIdx)
	m.Chat.Add("[phase] " + msg.Phase + " " + msg.Status)
	return m, nil
}

func (m model) handleJobCompleteMsg(msg backend.JobCompleteMsg) (tea.Model, tea.Cmd) {
	if m.JobID == "" && !m.Pipeline.Running {
		return m, nil
	}
	if m.CancelCtx != nil {
		m.CancelCtx()
	}
	m.JobID = ""
	m.CancelCtx = nil
	m.PipelineCtx = nil
	m.SSEActive = false
	m.Pipeline.Stop()
	m.Mascot.SetPipelineState(false, -1)
	m.Mascot.OnDiscovery()
	m.Mascot.SetEmotion(widgets.EmotionHappy)
	m.Discoveries = m.Mascot.Stats.Discoveries
	m.Header.Discoveries = m.Discoveries
	m.Header.SetDiscoveryPulse()
	m.LastResult = msg.Result

	m.Result.SetJobResult(msg.Result)
	quality := "unknown"
	if q, ok := msg.Result["quality"].(string); ok {
		quality = q
	}
	if len(msg.Errors) > 0 {
		m.Chat.Add("[warn] Completed with " + strconv.Itoa(len(msg.Errors)) + " error(s)")
		for _, err := range msg.Errors {
			m.Chat.Add("  • " + err)
		}
	}
	m.Chat.Add("[pipeline] Finished! Quality: " + quality)
	m.showToast("✓ Complete! Quality: "+quality, "success")

	// Persist to session store.
	record := internal.SessionRecord{
		Topic:     internal.Input(m.InputBar.TextArea.Value()),
		Mode:      m.InputBar.Mode,
		Quality:   quality,
		Papers:    m.Result.Papers,
		Hyps:      m.Result.Hypotheses,
		Timestamp: time.Now(),
	}
	if err := m.Store.Add(record); err != nil {
		m.Chat.Add("[warn] Failed to save session: " + err.Error())
	}

	// Trigger jump animation on S-rank and fireworks on high quality.
	qs := qualityScore(quality)
	if qs >= 90 {
		m.Mascot.Jump()
	}
	if qs >= 80 && m.Overlay == nil {
		m.Screen = screens.ScreenFireworks
		return openOverlay(m, screens.NewFireworks())
	}
	return m, widgets.PulseClearCmd()
}

// qualityScore maps a quality grade to a numeric score (0-100).
func qualityScore(q string) int {
	switch {
	case strings.HasPrefix(q, "S"):
		return 95
	case strings.HasPrefix(q, "A+"):
		return 90
	case strings.HasPrefix(q, "A"):
		return 85
	case strings.HasPrefix(q, "B+"):
		return 78
	case strings.HasPrefix(q, "B"):
		return 72
	case strings.HasPrefix(q, "C+"):
		return 65
	case strings.HasPrefix(q, "C"):
		return 60
	default:
		if n, err := strconv.Atoi(q); err == nil {
			return n
		}
		return 0
	}
}

func (m model) handleJobFailedMsg(msg backend.JobFailedMsg) (tea.Model, tea.Cmd) {
	if m.JobID == "" && !m.Pipeline.Running {
		return m, nil
	}
	if m.CancelCtx != nil {
		m.CancelCtx()
	}
	m.JobID = ""
	m.CancelCtx = nil
	m.PipelineCtx = nil
	m.SSEActive = false
	m.Pipeline.Stop()
	m.Mascot.SetPipelineState(false, -1)
	m.Mascot.SetEmotion(widgets.EmotionSurprised)
	if len(msg.Errors) == 0 {
		m.Chat.Add("[err] Pipeline failed (no details provided)")
	}
	for _, err := range msg.Errors {
		m.Chat.Add("[err] " + err)
	}
	return m, nil
}

func (m model) handleTurboMsg(msg backend.TurboMsg) (tea.Model, tea.Cmd) {
	if msg.Err != nil {
		m.Chat.Add("[err] Backend: " + msg.Err.Error())
		m.Mascot.SetEmotion(widgets.EmotionSurprised)
		if m.CancelCtx != nil {
			m.CancelCtx()
		}
		m.CancelCtx = nil
		m.PipelineCtx = nil
		m.Pipeline.Stop()
		return m, nil
	}
	m.JobID = msg.JobID
	m.Chat.Add("[pipeline] Turbo job " + msg.JobID + " queued")
	return m, tea.Batch(
		m.pollTick(),
		backend.SSESubscribeCmd(m.PipelineCtx, m.Backend, m.JobID),
	)
}

func (m model) handleTurboFactoryMsg(msg backend.TurboFactoryMsg) (tea.Model, tea.Cmd) {
	if m.CancelCtx != nil {
		m.CancelCtx()
	}
	m.CancelCtx = nil
	m.PipelineCtx = nil
	m.Pipeline.Stop()
	m.Mascot.SetPipelineState(false, -1)
	if msg.Err != nil {
		m.Chat.Add("[err] TurboFactory: " + msg.Err.Error())
		m.Mascot.SetEmotion(widgets.EmotionSurprised)
		return m, nil
	}
	m.Mascot.SetEmotion(widgets.EmotionHappy)
	m.Chat.Add("[pipeline] TurboFactory launched " + strconv.Itoa(len(msg.JobIDs)) + " jobs")
	return m, nil
}

func (m model) startTurboFactory() (tea.Model, tea.Cmd) {
	if m.Pipeline.Running {
		m.Chat.Add("[warn] Pipeline already running")
		return m, nil
	}
	raw := m.InputBar.TextArea.Value()
	if raw == "" {
		m.Chat.Add("[warn] Enter comma-separated problems")
		return m, nil
	}
	var problems []string
	for _, p := range strings.Split(raw, ",") {
		p = strings.TrimSpace(p)
		if p != "" {
			problems = append(problems, p)
		}
	}
	if len(problems) == 0 {
		m.Chat.Add("[warn] No valid problems found")
		return m, nil
	}
	m.Pipeline.Start()
	m.Mascot.SetPipelineState(true, 0)
	m.Mascot.SetEmotion(widgets.EmotionThinking)
	m.Chat.Add("[pipeline] Starting TurboFactory with " + strconv.Itoa(len(problems)) + " problems...")
	m.PipelineCtx, m.CancelCtx = context.WithCancel(context.Background())
	return m, backend.TurboFactoryCmd(m.PipelineCtx, m.Backend, problems, "science")
}

func openOverlay(m model, s screens.Model) (model, tea.Cmd) {
	m.Overlay = s
	cmds := []tea.Cmd{s.Init()}
	newOverlay, cmd := s.Update(tea.WindowSizeMsg{Width: m.Width, Height: m.Height})
	if overlay, ok := newOverlay.(screens.Model); ok {
		m.Overlay = overlay
	}
	cmds = append(cmds, cmd)
	return m, tea.Batch(cmds...)
}

func (m model) handlePaletteAction(action screens.PaletteAction) (tea.Model, tea.Cmd) {
	switch action {
	case screens.ActionDashboard:
		m.Screen = screens.ScreenDashboard
		return openOverlay(m, screens.NewDashboard(m.Store))
	case screens.ActionExport:
		m.Screen = screens.ScreenExport
		return openOverlay(m, screens.NewExportPicker(m.LastResult))
	case screens.ActionDissertation:
		m.Screen = screens.ScreenDissertation
		return openOverlay(m, screens.NewDissertation(m.LastResult))
	case screens.ActionKnowledgeGraph:
		m.Screen = screens.ScreenKnowledgeGraph
		return openOverlay(m, screens.NewKnowledgeGraph(m.Store))
	case screens.ActionHistory:
		m.Screen = screens.ScreenHistory
		return openOverlay(m, screens.NewHistoryTable(m.Store))
	case screens.ActionMatrixRain:
		m.Screen = screens.ScreenMatrixRain
		return openOverlay(m, screens.NewMatrixRain())
	case screens.ActionDiagnostic:
		m.Screen = screens.ScreenDiagnostic
		return openOverlay(m, screens.NewDiagnostic(m.Backend))
	case screens.ActionBibliography:
		m.Screen = screens.ScreenBibliography
		return openOverlay(m, screens.NewBibliography(m.LastResult))
	case screens.ActionTRIZ:
		m.Screen = screens.ScreenTRIZ
		return openOverlay(m, screens.NewTRIZ())
	case screens.ActionProvider:
		m.Screen = screens.ScreenProvider
		return openOverlay(m, screens.NewProvider())
	case screens.ActionCache:
		m.Screen = screens.ScreenCache
		return openOverlay(m, screens.NewCacheInspector())
	case screens.ActionSocial:
		m.Screen = screens.ScreenSocial
		topic := ""
		if m.LastResult != nil {
			if p, ok := m.LastResult["problem"].(string); ok {
				topic = p
			}
		}
		quality := "unknown"
		if m.LastResult != nil {
			if q, ok := m.LastResult["quality"].(string); ok {
				quality = q
			}
		}
		return openOverlay(m, screens.NewSocialSharing(topic, quality))
	case screens.ActionGPU:
		m.Screen = screens.ScreenGPU
		return openOverlay(m, screens.NewGPUMonitor())
	case screens.ActionPackages:
		m.Screen = screens.ScreenPackages
		return openOverlay(m, screens.NewPackageInstaller())
	case screens.ActionAgenda:
		m.Screen = screens.ScreenAgenda
		return openOverlay(m, screens.NewAgenda())
	case screens.ActionCycleTheme:
		t := styles.CycleTheme()
		m.Header.ThemeName = t.Name
		m.Pipeline.SetThemeColors()
		m.Chat.Add("[theme] Switched to " + t.Name)
		m.showToast("Theme: "+t.Name, "info")
		return m, nil
	case screens.ActionCycleLanguage:
		m.Language = internal.NextLanguage(m.Language)
		internal.ActiveLanguage = m.Language
		m.Header.Flag = internal.LanguageFlags[m.Language]
		m.Chat.Add("[lang] " + internal.LanguageNames[m.Language])
		m.showToast("Language: "+internal.LanguageNames[m.Language], "info")
		return m, nil
	case screens.ActionHelp:
		m.Screen = screens.ScreenHelp
		return openOverlay(m, screens.NewHelp())
	case screens.ActionToggleChat:
		m.Chat.Expanded = !m.Chat.Expanded
		return m, nil
	case screens.ActionToggleHelpWidget:
		m.Help.Toggle()
		return m, nil
	case screens.ActionQuit:
		return m, tea.Quit
	}
	return m, nil
}
