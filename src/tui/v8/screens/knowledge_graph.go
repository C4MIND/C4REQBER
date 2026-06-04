package screens

import (
	"fmt"
	"sort"
	"strings"

	"c4tui/internal"
	"c4tui/styles"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
)

// KnowledgeGraph shows term frequency from recent discoveries.
type KnowledgeGraph struct {
	width  int
	height int
	terms  []termFreq
	done   bool
}

type termFreq struct {
	word  string
	count int
}

// NewKnowledgeGraph creates a knowledge graph from the last 8 discoveries.
func NewKnowledgeGraph(store *internal.Store) KnowledgeGraph {
	if store == nil {
		return KnowledgeGraph{terms: []termFreq{}}
	}
	records := store.Recent(8)
	freq := make(map[string]int)
	for _, r := range records {
		for _, w := range tokenize(r.Topic) {
			if len(w) > 3 {
				freq[w]++
			}
		}
	}
	var terms []termFreq
	for w, c := range freq {
		terms = append(terms, termFreq{word: w, count: c})
	}
	sort.Slice(terms, func(i, j int) bool {
		if terms[i].count != terms[j].count {
			return terms[i].count > terms[j].count
		}
		return terms[i].word < terms[j].word
	})
	if len(terms) > 20 {
		terms = terms[:20]
	}
	return KnowledgeGraph{terms: terms}
}

func (k KnowledgeGraph) Title() string { return "Knowledge Graph" }
func (k KnowledgeGraph) Done() bool    { return k.done }

func (k KnowledgeGraph) Init() tea.Cmd { return nil }

func (k KnowledgeGraph) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		k.width = msg.Width
		k.height = msg.Height
		return k, nil
	case tea.KeyMsg:
		if msg.Type == tea.KeyEsc || msg.String() == "q" {
			k.done = true
			return k, nil
		}
	}
	return k, nil
}

func (k KnowledgeGraph) View() string {
	if k.width == 0 {
		return ""
	}

	title := lipgloss.NewStyle().Bold(true).Foreground(styles.ActiveTheme().Primary).Render("Knowledge Graph")
	sub := lipgloss.NewStyle().Foreground(styles.ActiveTheme().Dim).Render("Term frequency from last 8 discoveries")

	if len(k.terms) == 0 {
		content := lipgloss.JoinVertical(lipgloss.Center, title, "", sub, "", "Not enough data yet.")
		return k.centerBox(content)
	}

	maxCount := k.terms[0].count
	var bars []string
	for _, t := range k.terms {
		barLen := 0
		if maxCount > 0 {
			barLen = (t.count * 30) / maxCount
		}
		bar := strings.Repeat("█", barLen)
		label := lipgloss.NewStyle().Width(20).Render(t.word)
		count := lipgloss.NewStyle().Foreground(styles.ActiveTheme().Yellow).Render(fmt.Sprintf("%d", t.count))
		bars = append(bars, fmt.Sprintf("%s %s %s", label, lipgloss.NewStyle().Foreground(styles.ActiveTheme().Cyan).Render(bar), count))
	}

	content := lipgloss.JoinVertical(
		lipgloss.Left,
		title,
		sub,
		"",
		lipgloss.JoinVertical(lipgloss.Left, bars...),
		"",
		lipgloss.NewStyle().Foreground(styles.ActiveTheme().Dim).Render("Press Esc or Q to close"),
	)

	return k.centerBox(content)
}

func (k KnowledgeGraph) centerBox(content string) string {
	box := lipgloss.NewStyle().
		Width(min(70, k.width-4)).
		Padding(2).
		Border(lipgloss.RoundedBorder()).
		BorderForeground(styles.ActiveTheme().Border).
		Render(content)
	return lipgloss.Place(
		k.width, k.height,
		lipgloss.Center, lipgloss.Center,
		box,
		lipgloss.WithWhitespaceChars(" "),
	)
}

func tokenize(s string) []string {
	s = strings.ToLower(s)
	var words []string
	for _, w := range strings.FieldsFunc(s, func(r rune) bool {
		return r == ' ' || r == ',' || r == '.' || r == ':' || r == ';' || r == '!' || r == '?' || r == '(' || r == ')'
	}) {
		w = strings.TrimSpace(w)
		if w != "" && !isStopWord(w) {
			words = append(words, w)
		}
	}
	return words
}

var stopWords = map[string]bool{
	"the": true, "and": true, "for": true, "are": true, "but": true,
	"not": true, "you": true, "all": true, "can": true, "had": true,
	"her": true, "was": true, "one": true, "our": true, "out": true,
	"day": true, "get": true, "has": true, "him": true, "his": true,
	"how": true, "its": true, "may": true, "new": true, "now": true,
	"old": true, "see": true, "two": true, "who": true, "boy": true,
	"did": true, "she": true, "use": true, "way": true,
	"many": true, "oil": true, "sit": true, "set": true, "run": true,
	"eat": true, "far": true, "sea": true, "eye": true, "ago": true,
	"off": true, "too": true, "any": true, "say": true, "man": true,
	"try": true, "ask": true, "end": true, "why": true, "let": true,
	"put": true,
}

func isStopWord(w string) bool {
	return stopWords[w]
}
