package tui

import (
	"context"
	"fmt"
	"strings"
	"time"

	tea "charm.land/bubbletea/v2"
	"charm.land/lipgloss/v2"

	"github.com/figuramax/c4reqber-tui-v9/api"
	"github.com/figuramax/c4reqber-tui-v9/cards"
	"github.com/figuramax/c4reqber-tui-v9/i18n"
)

type agendaGenerateMsg struct {
	resp   *api.AgendaGenerateResponse
	output string
	err    error
}

type agendaActionMsg struct {
	output string
	err    error
}

type agendaProgressMsg struct {
	progress *api.AgendaProgress
	output   string
	err      error
}

const agendaActionCount = 5 // generate, approve, reject, progress, run

func (m *model) agendaContextFromFeed() api.AgendaGenerateRequest {
	nodes := []string{}
	edges := [][]string{}
	recent := []map[string]interface{}{}
	seen := map[string]bool{}
	for i := len(m.feed) - 1; i >= 0 && len(recent) < 3; i-- {
		c := m.feed[i]
		if c.Kind != cards.KindHypothesis {
			continue
		}
		text := strings.TrimSpace(c.Title)
		if text == "" {
			continue
		}
		recent = append(recent, map[string]interface{}{
			"hypothesis": map[string]string{"text": text},
		})
		for _, w := range strings.Fields(strings.ToLower(text)) {
			w = strings.Trim(w, ".,;:!?\"'()[]")
			if len(w) < 4 || seen[w] {
				continue
			}
			seen[w] = true
			nodes = append(nodes, w)
			if len(nodes) > 8 {
				break
			}
		}
	}
	for i := 0; i+1 < len(nodes); i++ {
		edges = append(edges, []string{nodes[i], nodes[i+1]})
	}
	kg := map[string]interface{}{"nodes": nodes, "edges": edges}
	if len(nodes) == 0 {
		kg = map[string]interface{}{"nodes": []string{"research"}, "edges": [][]string{}}
	}
	return api.AgendaGenerateRequest{
		KnowledgeGraph: kg,
		RecentResults:  recent,
		NQuestions:     5,
	}
}

func agendaGenerateCmd(client *api.Client, req api.AgendaGenerateRequest) tea.Cmd {
	return func() tea.Msg {
		ctx, cancel := context.WithTimeout(context.Background(), 45*time.Second)
		defer cancel()
		resp, err := client.AgendaGenerate(ctx, req)
		if err != nil {
			return agendaGenerateMsg{err: err, output: err.Error()}
		}
		return agendaGenerateMsg{resp: resp}
	}
}

func agendaApproveCmd(client *api.Client, question, action string) tea.Cmd {
	return func() tea.Msg {
		ctx, cancel := context.WithTimeout(context.Background(), 15*time.Second)
		defer cancel()
		out, err := client.AgendaApprove(ctx, question, action, "")
		text := ""
		if out != nil {
			if msg, ok := out["message"].(string); ok {
				text = msg
			}
		}
		if err != nil {
			return agendaActionMsg{err: err, output: err.Error()}
		}
		return agendaActionMsg{output: text}
	}
}

func agendaProgressCmd(client *api.Client) tea.Cmd {
	return func() tea.Msg {
		ctx, cancel := context.WithTimeout(context.Background(), 15*time.Second)
		defer cancel()
		prog, err := client.AgendaProgress(ctx)
		if err != nil {
			return agendaProgressMsg{err: err, output: err.Error()}
		}
		return agendaProgressMsg{progress: prog}
	}
}

func selectedAgendaQuestion(m *model) string {
	if len(m.agendaQuestions) == 0 {
		return ""
	}
	if m.agendaQCursor < 0 || m.agendaQCursor >= len(m.agendaQuestions) {
		return m.agendaQuestions[0].Text
	}
	return m.agendaQuestions[m.agendaQCursor].Text
}

func openAgendaMenu(m *model) tea.Cmd {
	m.agendaVisible = true
	m.agendaLoading = true
	m.agendaOutput = ""
	m.agendaQuestions = nil
	m.agendaQCursor = 0
	m.agendaActionCursor = 0
	m.agendaFocusActions = true
	m.setToast("📋 " + i18n.T("agenda.title"))
	return agendaGenerateCmd(m.api, m.agendaContextFromFeed())
}

func (m *model) runAgendaAction(action int) tea.Cmd {
	switch action {
	case 0:
		m.agendaLoading = true
		m.agendaOutput = i18n.T("agenda.running")
		return agendaGenerateCmd(m.api, m.agendaContextFromFeed())
	case 1:
		q := selectedAgendaQuestion(m)
		if q == "" {
			m.agendaOutput = i18n.T("agenda.no_questions")
			return nil
		}
		m.agendaLoading = true
		return agendaApproveCmd(m.api, q, "approve")
	case 2:
		q := selectedAgendaQuestion(m)
		if q == "" {
			m.agendaOutput = i18n.T("agenda.no_questions")
			return nil
		}
		m.agendaLoading = true
		return agendaApproveCmd(m.api, q, "reject")
	case 3:
		m.agendaLoading = true
		return agendaProgressCmd(m.api)
	case 4:
		q := selectedAgendaQuestion(m)
		if q == "" {
			m.agendaOutput = i18n.T("agenda.no_questions")
			return nil
		}
		m.agendaVisible = false
		m.agendaLoading = false
		m.setToast("🔬 " + truncate(q, 50))
		return m.startDiscovery(q)
	default:
		return nil
	}
}

func agendaMenuEnter(m *model) tea.Cmd {
	if m.agendaFocusActions {
		return m.runAgendaAction(m.agendaActionCursor)
	}
	return nil
}

func truncateAgendaNav(m *model, up bool) {
	qCount := len(m.agendaQuestions)
	if up {
		if m.agendaFocusActions {
			if m.agendaActionCursor > 0 {
				m.agendaActionCursor--
			} else if qCount > 0 {
				m.agendaFocusActions = false
				m.agendaQCursor = qCount - 1
			}
		} else if m.agendaQCursor > 0 {
			m.agendaQCursor--
		}
		return
	}
	if !m.agendaFocusActions {
		if m.agendaQCursor < qCount-1 {
			m.agendaQCursor++
		} else {
			m.agendaFocusActions = true
			m.agendaActionCursor = 0
		}
		return
	}
	if m.agendaActionCursor < agendaActionCount-1 {
		m.agendaActionCursor++
	}
}

func RenderAgendaMenu(
	questions []api.AgendaQuestion,
	qCursor, actionCursor int,
	focusActions bool,
	output string,
	loading bool,
	width, height int,
) string {
	if width < 40 {
		width = 80
	}
	if height < 12 {
		height = 24
	}
	titleStyle := lipgloss.NewStyle().Bold(true).Foreground(lipgloss.Color("3"))
	labelStyle := lipgloss.NewStyle().Foreground(lipgloss.Color("7"))
	cursorStyle := lipgloss.NewStyle().Foreground(lipgloss.Color("3")).Bold(true)
	dimStyle := lipgloss.NewStyle().Foreground(lipgloss.Color("8"))
	boxStyle := lipgloss.NewStyle().
		Border(lipgloss.RoundedBorder()).
		BorderForeground(lipgloss.Color("3")).
		Padding(1, 2).
		Width(min(78, width-4))

	var body strings.Builder
	body.WriteString(titleStyle.Render("📋  "+i18n.T("agenda.title")) + "\n\n")
	body.WriteString(dimStyle.Render(i18n.T("agenda.questions")) + "\n")
	if len(questions) == 0 {
		body.WriteString("  " + dimStyle.Render(i18n.T("agenda.no_questions")) + "\n")
	} else {
		window := 6
		start := 0
		if qCursor >= window {
			start = qCursor - window + 1
		}
		end := start + window
		if end > len(questions) {
			end = len(questions)
		}
		for i := start; i < end; i++ {
			q := questions[i]
			marker := "  "
			line := fmt.Sprintf("%s  prio=%.2f", truncate(q.Text, 52), q.PriorityScore)
			if i == qCursor && !focusActions {
				marker = cursorStyle.Render("▶ ")
				line = cursorStyle.Render(line)
			} else {
				line = labelStyle.Render(line)
			}
			body.WriteString(marker + line + "\n")
		}
		if len(questions) > window {
			body.WriteString(dimStyle.Render(fmt.Sprintf("  (%d/%d)", qCursor+1, len(questions))) + "\n")
		}
	}
	body.WriteString("\n" + dimStyle.Render(i18n.T("agenda.actions")) + "\n")
	actions := []string{
		"agenda.action.generate",
		"agenda.action.approve",
		"agenda.action.reject",
		"agenda.action.progress",
		"agenda.action.run",
	}
	for i, act := range actions {
		marker := "  "
		line := labelStyle.Render(i18n.T(act))
		if focusActions && i == actionCursor {
			marker = cursorStyle.Render("▶ ")
			line = cursorStyle.Render(i18n.T(act))
		}
		body.WriteString(marker + line + "\n")
	}
	if loading {
		body.WriteString("\n" + dimStyle.Render(i18n.T("agenda.running")) + "\n")
	} else if output != "" {
		body.WriteString("\n" + dimStyle.Render(truncate(output, 360)) + "\n")
	}
	body.WriteString("\n" + dimStyle.Render(i18n.T("agenda.hint")))
	return lipgloss.Place(width, height, lipgloss.Center, lipgloss.Center, boxStyle.Render(body.String()))
}
