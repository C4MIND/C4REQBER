package tui

import (
	"fmt"
	"strings"
	"time"

	tea "charm.land/bubbletea/v2"
	zone "github.com/lrstanley/bubblezone/v2"

	"github.com/figuramax/c4reqber-tui-v9/i18n"
)

// Update is the single entry point for all messages.
func (m *model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	var cmds []tea.Cmd

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
		m.rain.Tick()
		m.burst.Tick()
		m.slide.Tick()
		m.typew.Tick(m.tick)
		m.sparks.Tick()
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
		if m.sseCancel != nil {
			// don't replace — we'll continue streaming the existing connection
		}
		status, phase, progress, result, completed := extractResultFromSSEData(msg.event.Data)
		// Map to apiPollMsg so we can reuse the render path
		if status != "" || phase != "" {
			m.appendCard(Card{Kind: CardPhase, Title: phase, Body: fmt.Sprintf("progress %.0f%%", progress*100), Time: time.Now(), Status: "running", Progress: progress})
		}
		if completed {
			m.running = false
			m.jobID = ""
			m.toast = i18n.T("toast.complete")
			m.burst.Trigger(m.width, m.height, m.width/2, m.height/2)
			if result != nil {
				if hyp, ok := result["hypothesis"].(map[string]any); ok {
					hc := Card{Kind: CardHypothesis, Title: i18n.T("card.hypothesis.t"), Body: fieldString(hyp, "text"), Meta: []string{"source: " + fieldString(hyp, "source")}, Time: time.Now(), Status: "done"}
					m.appendCard(hc)
					m.typew.Set(fieldString(hyp, "text"), m.tick)
				}
				if papers, ok := result["papers"].([]any); ok {
					for i, p := range papers {
						if i >= 3 {
							break
						}
						pm, _ := p.(map[string]any)
						m.appendCard(Card{Kind: CardPaper, Title: fieldString(pm, "title"), Body: fmt.Sprintf("%s · %s · citations %s", fieldString(pm, "venue"), fieldString(pm, "year"), fieldString(pm, "citation_count")), Meta: []string{"doi: " + fieldString(pm, "doi"), "source: " + fieldString(pm, "source")}, Time: time.Now(), Status: "done"})
					}
				}
			}
		}
		// Continue streaming
		if m.sseEvents != nil && msg.cancel != nil {
			return m, sseContinueCmd(m.sseEvents, msg.cancel)
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

		switch msg.String() {
		case "ctrl+c":
			return m, tea.Quit
		case "enter":
			val := strings.TrimSpace(m.ta.Value())
			if val == "" {
				m.toast = i18n.T("toast.empty")
				return m, nil
			}
			m.ta.Reset()
			m.startDiscovery(val)
			return m, nil
		case "esc":
			if m.running {
				m.running = false
				m.toast = i18n.T("toast.cancelled")
			}
			return m, nil
		case "tab":
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
			m.toast = "Mode: " + string(m.mode)
			return m, nil
		}
		m.sparks.Emit(2, 0, 3)
		return m, nil

	case tea.MouseClickMsg:
		return m, nil

	case apiSubmitMsg:
		if msg.err != nil {
			m.appendCard(Card{Kind: CardError, Title: i18n.T("toast.submit_failed"), Body: msg.err.Error(), Time: time.Now(), Status: "error"})
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
		} else {
			m.appendCard(Card{Kind: CardPhase, Title: msg.phase, Body: fmt.Sprintf("progress %.0f%%", msg.progress*100), Time: time.Now(), Status: "running", Progress: msg.progress})
			if msg.completed {
				m.running = false
				m.jobID = ""
				m.toast = i18n.T("toast.complete")
				m.burst.Trigger(m.width, m.height, m.width/2, m.height/2)
				if msg.result != nil {
					if hyp, ok := msg.result["hypothesis"].(map[string]any); ok {
						hc := Card{Kind: CardHypothesis, Title: i18n.T("card.hypothesis.t"), Body: fieldString(hyp, "text"), Meta: []string{"source: " + fieldString(hyp, "source")}, Time: time.Now(), Status: "done"}
						m.appendCard(hc)
						m.typew.Set(fieldString(hyp, "text"), m.tick)
					}
					if papers, ok := msg.result["papers"].([]any); ok {
						for i, p := range papers {
							if i >= 3 {
								break
							}
							pm, _ := p.(map[string]any)
							m.appendCard(Card{Kind: CardPaper, Title: fieldString(pm, "title"), Body: fmt.Sprintf("%s · %s · citations %s", fieldString(pm, "venue"), fieldString(pm, "year"), fieldString(pm, "citation_count")), Meta: []string{"doi: " + fieldString(pm, "doi"), "source: " + fieldString(pm, "source")}, Time: time.Now(), Status: "done"})
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
				m.appendCard(Card{Kind: CardPaper, Title: fieldString(pm, "title"), Body: fmt.Sprintf("%s · %s · citations %s", fieldString(pm, "venue"), fieldString(pm, "year"), fieldString(pm, "citation_count")), Meta: []string{"doi: " + fieldString(pm, "doi"), "source: " + fieldString(pm, "source")}, Time: time.Now(), Status: "done"})
			}
		}
		return m, nil

	case flashResultMsg:
		if msg.err != nil {
			m.appendCard(Card{Kind: CardError, Title: "Flash error", Body: msg.err.Error(), Time: time.Now(), Status: "error"})
		} else {
			m.running = false
			m.toast = i18n.T("toast.complete")
			m.burst.Trigger(m.width, m.height, m.width/2, m.height/2)
			if hyp, ok := msg.result["hypothesis"].(map[string]any); ok {
				hc := Card{Kind: CardHypothesis, Title: i18n.T("card.hypothesis.t"), Body: fieldString(hyp, "text"), Time: time.Now(), Status: "done"}
				m.appendCard(hc)
				m.typew.Set(fieldString(hyp, "text"), m.tick)
			}
		}
		return m, nil

	case multiResultMsg:
		if msg.err != nil {
			m.appendCard(Card{Kind: CardError, Title: "Multi error", Body: msg.err.Error(), Time: time.Now(), Status: "error"})
		} else {
			m.running = false
			m.toast = i18n.T("toast.complete")
			m.burst.Trigger(m.width, m.height, m.width/2, m.height/2)
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
					m.appendCard(Card{Kind: CardHypothesis, Title: title, Body: text, Meta: []string{"source: " + fieldString(hm, "source")}, Time: time.Now(), Status: "done"})
				}
			}
		}
		return m, nil
	}

	var cmd tea.Cmd
	m.ta, cmd = m.ta.Update(msg)
	cmds = append(cmds, cmd)
	return m, tea.Batch(cmds...)
}

func (m *model) startDiscovery(query string) {
	m.appendCard(Card{Kind: CardEmpty, Title: "→ " + query, Body: "submitting via " + string(m.mode) + "…", Time: time.Now()})
	switch m.mode {
	case ModeFlash:
		// Flash: sync, fast
		_ = flashCmd(m.api, query)
	case ModeTurbo, ModeTurboFactory:
		// For v9.0 these still go through one-click (we don't have separate endpoints)
		_ = submitCmd(m.api, query, "science")
	default:
		_ = submitCmd(m.api, query, "science")
	}
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
	_ = zone.Mark
}

func (m *model) rebuildFeedContent() {
	var b strings.Builder
	for _, card := range m.feed {
		b.WriteString(renderCard(card, m.width))
		b.WriteString("\n")
	}
	m.vp.SetContent(b.String())
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
