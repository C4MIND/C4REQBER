package tui

import (
	"fmt"
	"strings"
	"time"

	tea "charm.land/bubbletea/v2"
	zone "github.com/lrstanley/bubblezone/v2"
)

// Update is the single entry point for all messages.
func (m *model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	var cmds []tea.Cmd

	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		m.width, m.height = msg.Width, msg.Height
		m.layout()
		m.refreshView()
		return m, nil

	case tea.BackgroundColorMsg:
		// could re-pick theme, but dark-only for v9.0
		return m, nil

	case tickMsg:
		m.tick++
		// re-render the feed (cost ticker, pulse animations)
		if m.running && m.cost > 0 {
			m.costTick = fmt.Sprintf("$%.4f", m.cost)
		}
		m.rain.Tick()
		m.burst.Tick()
		m.slide.Tick()
		m.typew.Tick(m.tick)
		m.sparks.Tick()
		if m.typew.Active() || m.slide.Active() {
			m.rebuildFeedContent()
		}
		m.refreshView()
		return m, m.tickCmd()

	case pollTickMsg:
		if m.running && m.jobID != "" {
			return m, pollCmd(m.apiURL, m.jobID)
		}
		return m, m.pollTickCmd()
		// Forward to textarea first (so typing works in input)
		var cmd tea.Cmd
		m.ta, cmd = m.ta.Update(msg)
		cmds = append(cmds, cmd)

		switch msg.String() {
		case "ctrl+c":
			return m, tea.Quit
		case "enter":
			val := strings.TrimSpace(m.ta.Value())
			if val == "" {
				m.toast = T("toast.empty")
				m.refreshView()
				return m, nil
			}
			m.ta.Reset()
			m.startDiscovery(val)
			m.refreshView()
			return m, tea.Batch(cmds...)
		case "esc":
			if m.running {
				m.running = false
				m.toast = T("toast.cancelled")
				m.refreshView()
			}
			return m, tea.Batch(cmds...)
		}
		m.sparks.Emit(2, 0, 3) // emit 3 sparks at input cursor on any key
		return m, tea.Batch(cmds...)

	case tea.MouseClickMsg:
		// bubblezone: zone.Get("…").InBounds(msg)
		_ = msg
		return m, nil

	case apiSubmitMsg:
		if msg.err != nil {
			m.appendCard(Card{Kind: CardError, Title: "Submit failed", Body: msg.err.Error(), Time: time.Now(), Status: "error"})
		} else {
			m.jobID = msg.jobID
			m.running = true
			m.startedAt = time.Now()
			m.appendCard(Card{Kind: CardPhase, Title: "Submitted", Body: "job " + msg.jobID, Time: time.Now(), Status: "running", Progress: 0.0})
		}
		m.refreshView()
		return m, nil

	case apiPollMsg:
		if msg.err != nil {
			m.appendCard(Card{Kind: CardError, Title: "Poll error", Body: msg.err.Error(), Time: time.Now(), Status: "error"})
		} else {
			m.appendCard(Card{Kind: CardPhase, Title: msg.phase, Body: fmt.Sprintf("progress %.0f%%", msg.progress*100), Time: time.Now(), Status: "running", Progress: msg.progress})
			if msg.completed {
				m.running = false
				m.jobID = ""
				m.cost = float64(m.tick) / 60.0 * 0.001
				m.toast = T("toast.complete")
				m.burst.Trigger(m.width, m.height, m.width/2, m.height/2)
				if msg.result != nil {
					if hyp, ok := msg.result["hypothesis"].(map[string]any); ok {
						hc := Card{Kind: CardHypothesis, Title: T("card.hypothesis.t"), Body: stringField(hyp, "text"), Meta: []string{"source: " + stringField(hyp, "source")}, Time: time.Now(), Status: "done"}
						m.appendCard(hc)
						m.typoTarget = hc
						m.typew.Set(stringField(hyp, "text"), m.tick)
					}
					if papers, ok := msg.result["papers"].([]any); ok {
						for i, p := range papers {
							if i >= 3 {
								break
							}
							pm, _ := p.(map[string]any)
							_ = i
							m.appendCard(Card{Kind: CardPaper, Title: stringField(pm, "title"), Body: fmt.Sprintf("%s · %s · citations %s", stringField(pm, "venue"), stringField(pm, "year"), stringField(pm, "citation_count")), Meta: []string{"doi: " + stringField(pm, "doi"), "source: " + stringField(pm, "source")}, Time: time.Now(), Status: "done"})
						}
					}
					if t, ok := msg.result["total_time_seconds"].(float64); ok {
						m.cost = t * 0.0001 // placeholder
					}
				}
				m.toast = "Discovery complete"
			}
		}
		m.refreshView()
		return m, nil

	case apiPapersMsg:
		if msg.err == nil {
			for i, pm := range msg.papers {
				if i >= 3 {
					break
				}
				_ = i
				m.appendCard(Card{Kind: CardPaper, Title: stringField(pm, "title"), Body: fmt.Sprintf("%s · %s · citations %s", stringField(pm, "venue"), stringField(pm, "year"), stringField(pm, "citation_count")), Meta: []string{"doi: " + stringField(pm, "doi"), "source: " + stringField(pm, "source")}, Time: time.Now(), Status: "done"})
			}
			m.refreshView()
		}
		return m, nil
	}

	// Forward non-handled messages to textarea
	var cmd tea.Cmd
	m.ta, cmd = m.ta.Update(msg)
	cmds = append(cmds, cmd)
	return m, tea.Batch(cmds...)
}

func (m *model) startDiscovery(query string) {
	// Append user query as a card
	m.appendCard(Card{Kind: CardEmpty, Title: "→ " + query, Body: "submitting…", Time: time.Now()})
	cmds := []tea.Cmd{submitCmd(m.apiURL, query, "")}
	_ = cmds
}

// stubs wired to actual API in phase 2

func stringField(m map[string]any, key string) string {
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

// helper — append to feed & auto-scroll
func (m *model) appendCard(c Card) {
	if c.Time.IsZero() {
		c.Time = time.Now()
	}
	m.feed = append(m.feed, c)
	m.rebuildFeedContent()
	m.slide.Trigger(m.tick)
	if m.follow {
		m.vp.GotoBottom()
	}
	_ = zone.Mark // keep import alive
}

func (m *model) rebuildFeedContent() {
	var b strings.Builder
	for _, card := range m.feed {
		b.WriteString(renderCard(card, m.width))
		b.WriteString("\n")
	}
	m.vp.SetContent(b.String())
}
