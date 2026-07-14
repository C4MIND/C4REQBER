// Package commands — command palette types and matching (model-agnostic).
package commands

import (
	"sort"
	"strings"
	"unicode"
)

// Command is a single palette entry. The Run function is a closure
// passed at registration time (in the root tui package, which has
// access to the model and Bubble Tea types).
type Command struct {
	ID       string
	Title    string
	Aliases  []string
	Category string
	Key      string
	Icon     string
	// Run is the closure invoked when the user picks this command.
	// Returns nil for a no-op.
	Run func() any
}

// Registry holds all palette commands.
type Registry struct {
	cmds []Command
}

// NewRegistry creates an empty registry.
func NewRegistry() *Registry { return &Registry{} }

// Register adds a command.
func (r *Registry) Register(c Command) { r.cmds = append(r.cmds, c) }

// All returns the registered commands.
func (r *Registry) All() []Command { return r.cmds }

// MatchResult is one scored match for the user's query.
type MatchResult struct {
	Cmd   Command
	Score int
}

// Match returns commands that fuzzy-match the query, sorted by score
// descending. Empty query returns all commands (sorted by Category then Title).
func (r *Registry) Match(query string) []MatchResult {
	if query == "" {
		all := make([]MatchResult, len(r.cmds))
		for i, c := range r.cmds {
			all[i] = MatchResult{Cmd: c, Score: 0}
		}
		sort.SliceStable(all, func(i, j int) bool {
			if all[i].Cmd.Category != all[j].Cmd.Category {
				return all[i].Cmd.Category < all[j].Cmd.Category
			}
			return all[i].Cmd.Title < all[j].Cmd.Title
		})
		return all
	}
	q := strings.ToLower(strings.TrimSpace(query))
	if q == "" {
		return nil
	}
	scored := make([]MatchResult, 0, len(r.cmds))
	for _, c := range r.cmds {
		s := scoreCommand(q, c)
		if s > 0 {
			scored = append(scored, MatchResult{Cmd: c, Score: s})
		}
	}
	sort.SliceStable(scored, func(i, j int) bool {
		return scored[i].Score > scored[j].Score
	})
	if len(scored) > 20 {
		scored = scored[:20]
	}
	return scored
}

// scoreCommand computes a match score for one command against the query.
func scoreCommand(q string, c Command) int {
	best := 0
	if s := fuzzyScore(q, c.ID); s > best {
		best = s
	}
	if s := fuzzyScore(q, strings.ToLower(c.Title)); s > best {
		best = s
	}
	for _, a := range c.Aliases {
		if s := fuzzyScore(q, strings.ToLower(a)); s > best {
			best = s
		}
	}
	return best
}

// fuzzyScore: subsequence-with-boundary-bonus. 0 if q is not a
// subsequence of s.
func fuzzyScore(q, s string) int {
	if q == "" {
		return 0
	}
	qi, si := 0, 0
	matched := 0
	prefixMatch := strings.HasPrefix(s, q)
	for qi < len(q) && si < len(s) {
		if q[qi] == s[si] {
			qi++
			matched++
		}
		si++
	}
	if qi < len(q) {
		return 0
	}
	score := matched
	if prefixMatch {
		score += 10
	}
	score -= len(s) - matched
	return score
}

// FuzzyMatch exposes the scorer for testing.
func FuzzyMatch(q, s string) int { return fuzzyScore(q, s) }

// IsBoundary reports whether position i in s is a word boundary
// (transition between alphanum and a separator). Exposed for tests.
func IsBoundary(s string, i int) bool {
	if i == 0 {
		return true
	}
	prev := rune(s[i-1])
	cur := rune(s[i])
	return (unicode.IsLetter(prev) || unicode.IsDigit(prev)) &&
		(cur == ' ' || cur == '-' || cur == '_' || cur == '.')
}
