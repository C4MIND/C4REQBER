package tui

import (
	"context"
	"fmt"
	"strings"
	"time"

	"os/exec"
	"runtime"

	tea "charm.land/bubbletea/v2"
	zone "github.com/lrstanley/bubblezone/v2"

	"github.com/figuramax/c4reqber-tui-v9/cards"
	"github.com/figuramax/c4reqber-tui-v9/capsim"
	"github.com/figuramax/c4reqber-tui-v9/i18n"
)

// Update is the single entry point for all messages.
func (m *model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	var cmds []tea.Cmd

	// Any non-tick message is user activity — touch the dream state to defer idle.
	if _, isTick := msg.(tickMsg); !isTick {
		if m.dream != nil {
			m.dream.Touch()
		}
	}

	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		m.width, m.height = msg.Width, msg.Height
		m.layout()
		m.rebuildFeedContent()
		return m, nil

	case tea.BackgroundColorMsg:
		return m, nil

	case tickMsg:
		m.tick++
		if m.running && m.cost > 0 {
			m.cost = float64(m.tick) / 60.0 * 0.001
		}
		// v9.11.9: auto-clear toast after ~1.5s (96 ticks at 16ms).
		if m.toast != "" && m.toastTick > 0 && m.tick-m.toastTick > 96 {
			m.toast = ""
		}
		m.burst.Tick()
		m.slide.Tick()
		m.typew.Tick(m.tick)
		if m.dream != nil {
			m.dream.Tick()
		}
		// Achievement overlay auto-dismiss (v9.10)
		if m.showAchievementOverlay && !m.achievements.OverlayActive() {
			m.showAchievementOverlay = false
		}
		if m.typew.Active() || m.slide.Active() {
			m.rebuildFeedContent()
		}
		return m, m.tickCmd()

	case pollTickMsg:
		// Legacy polling — superseded by SSE (see sseEventMsg below).
		// Kept for fallback if SSE endpoint unavailable.
		if m.running && m.jobID != "" {
			return m, pollCmd(m.api, m.jobID)
		}
		return m, m.pollTickCmd()

	case sseEventMsg:
		// SSE event from /v8/discover/stream/{job_id}
		if m.sseEvents == nil {
			m.sseEvents = msg.events
			m.sseCancel = msg.cancel
		}
		status, phase, progress, result, completed := extractResultFromSSEData(msg.event.Data)
		// Map to apiPollMsg so we can reuse the render path
		if status != "" || phase != "" {
			// v9.12.1: dedup phase cards — skip if phase/progress unchanged
			if phase != m.lastPhase || (abs(progress-m.lastProgress) > 0.01) {
				m.lastPhase = phase
				m.lastProgress = progress
				m.appendCard(Card{Kind: CardPhase, Title: phase, Body: fmt.Sprintf("progress %.0f%%", progress*100), Time: time.Now(), Status: "running", Progress: progress})
			}
		}
		if completed {
			m.running = false
			m.jobID = ""
			m.setToast(i18n.T("toast.complete"))
			m.burst.Trigger(m.width, m.height, m.width/2, m.height/2)
			if result != nil {
				if hyp, ok := result["hypothesis"].(map[string]any); ok {
					hc := Card{Kind: CardHypothesis, Title: i18n.T("card.hypothesis.t"), Body: fieldString(hyp, "text"), Meta: []cards.MetaKV{{Key: "source", Value: fieldString(hyp, "source")}}, Time: time.Now(), Status: "done"}
					m.appendCard(hc)
					m.typew.Set(fieldString(hyp, "text"), m.tick)
					if novelty, ok := hyp["novelty_score"].(float64); ok {
						m.lastQuality = novelty
					}
				}
				if papers, ok := result["papers"].([]any); ok {
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
		// Continue streaming
		if m.sseEvents != nil {
			return m, sseContinueCmd(m.sseEvents, m.sseCancel)
		}
		return m, nil

	case sseClosedMsg:
		// SSE stream ended; fall back to polling for any final result
		m.sseEvents = nil
		if m.running && m.jobID != "" {
			return m, pollCmd(m.api, m.jobID)
		}
		return m, nil

	case sseErrorMsg:
		m.sseEvents = nil
		// SSE failed; fall back to polling
		if m.running && m.jobID != "" {
			return m, pollCmd(m.api, m.jobID)
		}
		return m, nil

	case tea.KeyPressMsg:
		var cmd tea.Cmd
		m.ta, cmd = m.ta.Update(msg)
		cmds = append(cmds, cmd)

		keyStr := msg.String()
		km := m.keymap
		switch {

		case km.Matches(ActQuit, keyStr):
			if m.saveHistory && m.tel != nil {
				saveTelemetryHistory(m.tel, m.Config())
			}
			return m, tea.Quit
		case km.Matches(ActRun, keyStr):
			// Wizard: Enter advances / finishes
			if m.wizard != nil && m.wizard.Active() {
				m.wizard.Next()
				if m.wizard.Step() >= 3 {
					m.wizard.Done()
					m.MarkFirstRunDone()
				}
				return m, nil
			}
			val := strings.TrimSpace(m.ta.Value())
			if val == "" {
				m.setToast(i18n.T("toast.empty"))
				return m, nil
			}
			m.ta.Reset()
			cmd = m.startDiscovery(val)
			return m, cmd
		case km.Matches(ActCancel, keyStr), km.Matches(ActEscape, keyStr):
			if m.showCapabilities {
				m.showCapabilities = false
				return m, nil
			}
			if m.wizard != nil && m.wizard.Active() {
				m.wizard.Done()
				m.MarkFirstRunDone()
				return m, nil
			}
			if m.running {
				m.running = false
				m.jobID = ""
				if m.sseCancel != nil {
					m.sseCancel()
					m.sseCancel = nil
				}
				m.sseEvents = nil
				m.setToast(i18n.T("toast.cancelled"))
				if m.tel != nil {
					m.tel.IncAbort()
				}
			}
			return m, nil
		case km.Matches(ActCycleMode, keyStr):
			// Cycle mode: DISCOVER → FLASH → TURBO → TURBOFACTORY → DISCOVER
			switch m.mode {
			case ModeDiscover:
				m.mode = ModeFlash
			case ModeFlash:
				m.mode = ModeTurbo
			case ModeTurbo:
				m.mode = ModeTurboFactory
			default:
				m.mode = ModeDiscover
			}
			modeName := string(m.mode)
			if l := i18n.T("mode." + strings.ToLower(string(m.mode))); l != "mode."+strings.ToLower(string(m.mode)) {
				modeName = l
			}
			m.setToast(i18n.T("keymap.cycle_mode") + ": " + modeName)
			if m.tel != nil {
				m.tel.IncMode(string(m.mode))
			}
			return m, nil
		case km.Matches(ActNewTab, keyStr):
			m.showTelemetry = !m.showTelemetry
			if m.showTelemetry {
				m.setToast("📊 telemetry ON (" + km.Label(ActNewTab) + " to hide)")
			} else {
				m.setToast("📊 telemetry OFF")
			}
			return m, nil
		case km.Matches(ActHelp, keyStr):
			m.showHelp = !m.showHelp
			if m.showHelp {
				m.setToast(i18n.T("help.shown"))
			} else {
				m.setToast(i18n.T("help.hidden"))
			}
			return m, nil
		case km.Matches(ActStatusBar, keyStr):
			// v9.13 (§3.3): toggle the 1-line status bar.
			m.showStatusBar = !m.showStatusBar
			if m.showStatusBar {
				m.setToast("📊 status bar ON")
			} else {
				m.setToast("📊 status bar OFF")
			}
			return m, nil
		case km.Matches(ActCapabilities, keyStr):
			// v9.13 (TI-SIM-02): open capabilities overlay.
			// Always re-fetch (or use cache). Esc to close.
			m.showCapabilities = !m.showCapabilities
			if m.showCapabilities {
				m.capsimLoading = true
				m.setToast("⏚ " + i18n.T("sim.capabilities.title"))
				return m, capsimCmd(m.capsimClient, false)
			}
			return m, nil
		case km.Matches(ActReauth, keyStr):
			// Re-authenticate (best-effort, with 10s timeout)
			ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
			defer cancel()
			err := m.api.Login(ctx, "kilo-v9@test.com", "test12345")
			if err != nil {
				m.setToast("🔑 re-auth failed: " + err.Error())
			} else {
				m.setToast("🔑 re-auth OK (" + km.Label(ActReauth) + ")")
			}
			return m, nil
		case km.Matches(ActSearch, keyStr):
			// Search mode (placeholder: shows search bar)
			m.setToast("🔍 search: " + strings.TrimSpace(m.ta.Value()))
			return m, nil
		case km.Matches(ActCopy, keyStr):
			// Copy focused card (or last if none focused) as markdown.
			if c := m.focusedCard(); c != nil {
				md := cardToMarkdown(*c)
				_ = copyToClipboard(md)
				m.setToast("📋 copied: " + truncate(c.Title, 30))
			}
			return m, nil
		case km.Matches(ActInstallHint, keyStr):
			// v9.13 (TI-SIM-06): on a CardSimulation with status=unavailable,
			// show the install hint. On any other card, no-op (toast hint).
			if c := m.focusedCard(); c != nil && c.Kind == CardSimulation && c.Sim.InstallHint != "" {
				m.setToast("ⓘ install: " + c.Sim.InstallHint)
			} else if c != nil && c.Kind == CardSimulation {
				m.setToast("ⓘ engine " + c.Sim.Engine + " is available; nothing to install")
			} else {
				m.setToast("ⓘ install hint only works on simulation cards")
			}
			return m, nil
		case km.Matches(ActSelectFallback, keyStr):
			// v9.13 (TI-SIM-06): on a CardSimulation with status=skipped/failed,
			// show the fallback chain. For now, toast it; full picker comes in
			// a follow-up commit. Records a telemetry event.
			if c := m.focusedCard(); c != nil && c.Kind == CardSimulation {
				chain := ""
				for _, t := range c.Sim.PatternsTried {
					chain += t.Engine + "(" + t.Status + ") → "
				}
				if chain == "" {
					chain = "(no chain recorded)"
				} else {
					chain = chain[:len(chain)-3] // trim trailing →
				}
				m.setToast("↪ fallback chain: " + chain)
			} else {
				m.setToast("↪ fallback only works on simulation cards")
			}
			return m, nil
		case km.Matches(ActOpenPlot, keyStr):
			// v9.13 (TI-SIM-06): on a CardSimulation with image evidence,
			// open the plot URL in the default browser.
			if c := m.focusedCard(); c != nil && c.Kind == CardSimulation {
				if c.Sim.Evidence.Type == "image" && c.Sim.Evidence.ImageURL != "" {
					_ = openURL(c.Sim.Evidence.ImageURL)
					m.setToast("🖼 opened plot: " + truncate(c.Sim.Evidence.ImageURL, 40))
				} else {
					m.setToast("🖼 this sim has no plot (evidence type: " + c.Sim.Evidence.Type + ")")
				}
			} else {
				m.setToast("🖼 open plot only works on simulation cards")
			}
			return m, nil
		case km.Matches(ActJump, keyStr):
			// Copy last card as JSON
			if len(m.feed) > 0 {
				last := m.feed[len(m.feed)-1]
				_ = copyToClipboard(fmt.Sprintf(`{"title":%q,"body":%q,"time":%q}`,
					last.Title, last.Body, last.Time.Format(time.RFC3339)))
				m.setToast("📋 copied as JSON")
			}
			return m, nil
		case km.Matches(ActTier, keyStr):
			m.llmTier = CycleLLMTier(m.llmTier)
			if m.tel != nil {
				// Tier tracking is in-model; snapshot picks it up on save
			}
			m.setToast("🧠 LLM " + m.llmTier.FormatTierBadge() + " (" + km.Label(ActTier) + ")")
			m.PersistSettings()
			return m, nil
		case km.Matches(ActSettings, keyStr):
			// v9.10: toggle settings menu
			m.settingsVisible = !m.settingsVisible
			if m.settingsVisible {
				m.setToast("⚙  settings (↑/↓ to move, " + km.Label(ActSettings) + " to close)")
			} else {
				m.setToast("settings closed")
			}
			return m, nil
		case km.Matches(ActUp, keyStr):
			if m.settingsVisible {
				if m.settingsCursor > 0 {
					m.settingsCursor--
				}
				return m, nil
			}
			// Scroll feed up
			m.vp.ScrollUp(1)
			m.rebuildFeedContent()
			return m, nil
		case km.Matches(ActDown, keyStr):
			if m.settingsVisible {
				rows := m.CurrentSettings()
				if m.settingsCursor < len(rows)-1 {
					m.settingsCursor++
				}
				return m, nil
			}
			// Scroll feed down
			m.vp.ScrollDown(1)
			m.rebuildFeedContent()
			return m, nil
		case km.Matches(ActFocusPrev, keyStr):
			// v9.13: navigate card focus up.
			if len(m.feed) > 0 {
				if m.focusedCardIdx < 0 {
					m.focusedCardIdx = len(m.feed) - 1
				} else if m.focusedCardIdx > 0 {
					m.focusedCardIdx--
				}
				m.follow = false
				m.setToast("focused: " + truncate(m.feed[m.focusedCardIdx].Title, 40))
			}
			return m, nil
		case km.Matches(ActFocusNext, keyStr):
			if len(m.feed) > 0 {
				if m.focusedCardIdx < 0 {
					m.focusedCardIdx = 0
				} else if m.focusedCardIdx < len(m.feed)-1 {
					m.focusedCardIdx++
				}
				m.follow = false
				m.setToast("focused: " + truncate(m.feed[m.focusedCardIdx].Title, 40))
			}
			return m, nil
		case km.Matches(ActFocusFirst, keyStr):
			if len(m.feed) > 0 {
				m.focusedCardIdx = 0
				m.follow = false
				m.setToast("focused: first")
			}
			return m, nil
		case km.Matches(ActFocusLast, keyStr):
			if len(m.feed) > 0 {
				m.focusedCardIdx = len(m.feed) - 1
				m.follow = true
				m.setToast("focused: last (follow on)")
			}
			return m, nil
		case km.Matches(ActColorProfile, keyStr), km.Matches(ActProfileMac, keyStr):
			// Cycle color profile (default → hc → prot → deut → trit → mono → default)
			switch m.colorProfile {
			case ProfileDefault:
				m.colorProfile = ProfileHighContrast
			case ProfileHighContrast:
				m.colorProfile = ProfileProtanopia
			case ProfileProtanopia:
				m.colorProfile = ProfileDeuteranopia
			case ProfileDeuteranopia:
				m.colorProfile = ProfileTritanopia
			case ProfileTritanopia:
				m.colorProfile = ProfileMonochrome
			default:
				m.colorProfile = ProfileDefault
			}
			m.setToast("🎨 " + m.colorProfile.String())
			m.PersistSettings()
			return m, nil
		case km.Matches(ActLang, keyStr):
			// Cycle language (right-to-left: EN→RU→ZH→JA→DE→AR→HI)
			next := cycleLangName(i18n.GetLang())
			i18n.SetLang(next)
			m.updateLangSeen()
			if m.tel != nil {
				m.tel.IncLang(string(next))
			}
			if m.store != nil {
				m.store.AddLangSeen(string(next))
				if err := m.store.Save(); err != nil {
					m.setToast("⚠ save: " + err.Error())
				}
			}
			m.setToast(i18n.T("lang.name") + ": " + string(next))
			m.PersistSettings()
			return m, nil
		}

	case tea.MouseClickMsg:
		// Mouse click on a card → find the card whose zone contains the click
		if msg.Button != tea.MouseLeft {
			return m, nil
		}
		// Check zones for the last 32 cards (we don't track every zone; just most recent)
		start := 0
		if len(m.zoneIDs) > 32 {
			start = len(m.zoneIDs) - 32
		}
		for _, zid := range m.zoneIDs[start:] {
			z := zone.Get(zid)
			if z != nil && z.InBounds(msg) {
				// Find the corresponding card and show its title
				for _, c := range m.feed {
					if fmt.Sprintf("card-%d", c.Time.UnixNano()) == zid {
						m.setToast("selected: " + c.Title)
						if len(m.toast) > 60 {
							m.toast = m.toast[:60] + "…"
						}
						return m, nil
					}
				}
			}
		}
		return m, nil

	case tea.MouseWheelMsg:
		// v9.10: mouse wheel scrolls feed by 3 lines
		if msg.Button == tea.MouseWheelUp {
			m.vp.ScrollUp(3)
		} else if msg.Button == tea.MouseWheelDown {
			m.vp.ScrollDown(3)
		}
		m.rebuildFeedContent()
		return m, nil

	case apiSubmitMsg:
		if msg.err != nil {
			m.appendCard(Card{Kind: CardError, Title: i18n.T("toast.submit_failed"), Body: msg.err.Error(), Time: time.Now(), Status: "error"})
			m.running = false
		} else {
			m.jobID = msg.jobID
			m.running = true
			m.startedAt = time.Now()
			m.appendCard(Card{Kind: CardPhase, Title: "Submitted", Body: "job " + msg.jobID, Time: time.Now(), Status: "running", Progress: 0.0})
			// Prefer SSE; fall back to polling if SSE fails
			return m, tea.Batch(sseCmd(m.api, msg.jobID), m.pollTickCmd())
		}
		return m, nil

	case apiPollMsg:
		if msg.err != nil {
			m.appendCard(Card{Kind: CardError, Title: "Poll error", Body: msg.err.Error(), Time: time.Now(), Status: "error"})
			m.running = false
			m.jobID = ""
		} else {
			// v9.12.1: dedup phase cards — skip if phase/progress unchanged
			if msg.phase != m.lastPhase || (abs(msg.progress-m.lastProgress) > 0.01) {
				m.lastPhase = msg.phase
				m.lastProgress = msg.progress
				m.appendCard(Card{Kind: CardPhase, Title: msg.phase, Body: fmt.Sprintf("progress %.0f%%", msg.progress*100), Time: time.Now(), Status: "running", Progress: msg.progress})
			}
			if msg.completed {
				m.running = false
				m.jobID = ""
				m.setToast(i18n.T("toast.complete"))
				m.burst.Trigger(m.width, m.height, m.width/2, m.height/2)
				if msg.result != nil {
					if hyp, ok := msg.result["hypothesis"].(map[string]any); ok {
						hc := Card{Kind: CardHypothesis, Title: i18n.T("card.hypothesis.t"), Body: fieldString(hyp, "text"), Meta: []cards.MetaKV{{Key: "source", Value: fieldString(hyp, "source")}}, Time: time.Now(), Status: "done"}
						m.appendCard(hc)
						m.typew.Set(fieldString(hyp, "text"), m.tick)
					}
					if papers, ok := msg.result["papers"].([]any); ok {
						for i, p := range papers {
							if i >= 3 {
								break
							}
							pm, _ := p.(map[string]any)
							m.appendCard(Card{Kind: CardPaper, Title: fieldString(pm, "title"), Body: fmt.Sprintf("%s · %s · citations %s", fieldString(pm, "venue"), fieldString(pm, "year"), fieldString(pm, "citation_count")), Meta: []cards.MetaKV{{Key: "doi", Value: fieldString(pm, "doi")}, {Key: "source", Value: fieldString(pm, "source")}}, Time: time.Now(), Status: "done"})
						}
					}
				}
			}
		}
		return m, nil

	case apiPapersMsg:
		if msg.err == nil {
			for i, pm := range msg.papers {
				if i >= 3 {
					break
				}
				m.appendCard(Card{Kind: CardPaper, Title: fieldString(pm, "title"), Body: fmt.Sprintf("%s · %s · citations %s", fieldString(pm, "venue"), fieldString(pm, "year"), fieldString(pm, "citation_count")), Meta: []cards.MetaKV{{Key: "doi", Value: fieldString(pm, "doi")}, {Key: "source", Value: fieldString(pm, "source")}}, Time: time.Now(), Status: "done"})
			}
		}
		return m, nil

	case flashResultMsg:
		if msg.err != nil {
			m.appendCard(Card{Kind: CardError, Title: "Flash error", Body: msg.err.Error(), Time: time.Now(), Status: "error"})
			m.running = false
		} else {
			m.running = false
			m.setToast(i18n.T("toast.complete"))
			m.burst.Trigger(m.width, m.height, m.width/2, m.height/2)
			if hyp, ok := msg.result["hypothesis"].(map[string]any); ok {
				hc := Card{Kind: CardHypothesis, Title: i18n.T("card.hypothesis.t"), Body: fieldString(hyp, "text"), Time: time.Now(), Status: "done"}
				m.appendCard(hc)
				m.typew.Set(fieldString(hyp, "text"), m.tick)
			}
			m.completedDisc++
			m.checkAchievements()
		}
		return m, nil

	case multiResultMsg:
		if msg.err != nil {
			m.appendCard(Card{Kind: CardError, Title: "Multi error", Body: msg.err.Error(), Time: time.Now(), Status: "error"})
			m.running = false
		} else {
			m.running = false
			m.setToast(i18n.T("toast.complete"))
			m.burst.Trigger(m.width, m.height, m.width/2, m.height/2)
			m.completedDisc++
			m.checkAchievements()
			// Render each ranked hypothesis as a card
			if ranked, ok := msg.result["ranked_hypotheses"].([]any); ok {
				for i, h := range ranked {
					if i >= 3 {
						break
					}
					hm, _ := h.(map[string]any)
					text := fieldString(hm, "text")
					if text == "" {
						text = fieldString(hm, "source") + " hypothesis"
					}
					score := fieldString(hm, "score")
					title := fmt.Sprintf("%s #%d (%s)", i18n.T("card.hypothesis.t"), i+1, score)
					m.appendCard(Card{Kind: CardHypothesis, Title: title, Body: text, Meta: []cards.MetaKV{{Key: "source", Value: fieldString(hm, "source")}}, Time: time.Now(), Status: "done"})
				}
			}
		}
		return m, nil

	case capsimMsg:
		m.capsimLoading = false
		m.capsimReport = msg.report
		if msg.err != nil {
			// Backend unreachable — overlay still renders, but with a hint.
			m.setToast("⏚ capabilities: backend unreachable (using last known)")
			return m, nil
		}
		// D-03 in action: surface missing engines to the feed as first-class
		// CardSimulation entries with status=unavailable + install hint.
		// User can press 'i' on any of them to see the conda line.
		summary := capSummaryCard(msg.report)
		m.appendCard(summary)
		for _, c := range capUnavailableCards(msg.report, 6) {
			m.appendCard(c)
			m.simCountThisRun++
		}
		m.setToast("⏚ capabilities loaded (" + capsim.ShortSummary(msg.report) + ")")
		return m, nil
	}

	m.sparks.Emit(2, 0, 3)

	var cmd tea.Cmd
	m.ta, cmd = m.ta.Update(msg)
	cmds = append(cmds, cmd)
	return m, tea.Batch(cmds...)
}

// setToast records a notification message and marks the tick for
// auto-clear after ~1.5 seconds (96 ticks at 16ms).
func (m *model) setToast(msg string) {
	m.toast = msg
	m.toastTick = m.tick
}

func (m *model) startDiscovery(query string) tea.Cmd {
	m.appendCard(Card{Kind: CardEmpty, Title: "→ " + query, Body: "submitting via " + string(m.mode) + "…", Time: time.Now()})
	tier := m.llmTier.String()
	m.running = true
	var cmd tea.Cmd
	switch m.mode {
	case ModeFlash:
		cmd = flashCmd(m.api, query)
	case ModeTurbo, ModeTurboFactory:
		cmd = submitCmd(m.api, query, "science", tier)
	default:
		cmd = submitCmd(m.api, query, "science", tier)
	}
	return cmd
}

// appendCard helper.
func (m *model) appendCard(c Card) {
	if c.Time.IsZero() {
		c.Time = time.Now()
	}
	m.feed = append(m.feed, c)
	m.rebuildFeedContent()
	m.slide.Trigger()
	if m.follow {
		m.vp.GotoBottom()
	}
	// Track zone ID for mouse click routing
	zoneID := fmt.Sprintf("card-%d", c.Time.UnixNano())
	m.zoneIDs = append(m.zoneIDs, zoneID)
}

// checkAchievements evaluates unlocks and appends achievement cards.
func (m *model) checkAchievements() {
	langs := m.snapshotLangsSeen()
	seconds := time.Since(m.startedAt).Seconds()
	if m.startedAt.IsZero() {
		seconds = 0
	}
	unlocked := m.achievements.Check(m.completedDisc, m.lastQuality, m.lastPapersCount, seconds, langs)
	for _, a := range unlocked {
		m.appendCard(Card{
			Kind:   CardPhase,
			Title:  "🏆 " + i18n.T(a.Name),
			Body:   i18n.T(a.Description) + "  " + a.UnlockedAt.Format("15:04:05"),
			Time:   a.UnlockedAt,
			Status: "done",
		})
		// Persist to disk + telemetry
		if m.store != nil {
			m.store.AddAchievement(int(a.Kind))
			m.store.AddLangSeen(string(i18n.GetLang()))
			m.store.IncrementDiscovery()
			if err := m.store.Save(); err != nil {
				m.setToast("⚠ save: " + err.Error())
			}
		}
		if m.tel != nil {
			m.tel.IncDiscoveryResult(true, seconds)
		}
		// Trigger fullscreen achievement overlay (v9.10)
		if len(unlocked) > 0 {
			m.showAchievementOverlay = true
			m.achievements.ShowOverlay(i18n.T(a.Name), 2*time.Second)
		}
	}
}

// updateLangSeen records the current lang code in model.langsSeen.
func (m *model) updateLangSeen() {
	m.addLangSeen(string(i18n.GetLang()))
}

func (m *model) rebuildFeedContent() {
	var b strings.Builder
	// v9.11.7: when the feed is empty OR contains only CardEmpty
	// placeholders, render the dashboard widgets instead. Without
	// this, the viewport is 45 lines tall but content is just 2-3
	// lines, producing a black void below the placeholder.
	if m.feedIsEmpty() {
		b.WriteString(m.renderEmptyWidgets())
	} else {
		for _, card := range m.feed {
			b.WriteString(renderCard(card, m.width))
			b.WriteString("\n")
		}
	}
	m.vp.SetContent(b.String())
}

// feedIsEmpty reports whether the feed has no real content — i.e.
// it has zero cards, or only CardEmpty placeholder cards.
func (m *model) feedIsEmpty() bool {
	if len(m.feed) == 0 {
		return true
	}
	for _, c := range m.feed {
		if c.Kind != CardEmpty {
			return false
		}
	}
	return true
}

// fieldString — moved from stringField to avoid clash with i18n.T signature
func fieldString(m map[string]any, key string) string {
	if m == nil {
		return ""
	}
	v, ok := m[key]
	if !ok || v == nil {
		return ""
	}
	if s, ok := v.(string); ok {
		return s
	}
	return fmt.Sprintf("%v", v)
}

// copyToClipboard copies text to OS clipboard. Best-effort: pbcopy (macOS),
// xclip (Linux), clip (Windows). Returns nil on success.
func copyToClipboard(text string) error {
	var cmd *exec.Cmd
	switch runtime.GOOS {
	case "darwin":
		cmd = exec.Command("pbcopy")
	case "linux":
		cmd = exec.Command("xclip", "-selection", "clipboard")
	case "windows":
		cmd = exec.Command("clip")
	default:
		return fmt.Errorf("clipboard not supported on %s", runtime.GOOS)
	}
	cmd.Stdin = strings.NewReader(text)
	return cmd.Run()
}

// abs returns the absolute value of a float64. Used by phase-card dedup.
func abs(x float64) float64 {
	if x < 0 {
		return -x
	}
	return x
}
