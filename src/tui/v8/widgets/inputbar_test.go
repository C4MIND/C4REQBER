package widgets

import (
	"testing"

	"c4tui/config"
)

func TestContainsWord(t *testing.T) {
	tests := []struct {
		s    string
		subs []string
		want bool
	}{
		{"explain this concept", []string{"explain"}, true},
		{"what is gravity", []string{"what is"}, true},
		{"paradigm shift", []string{"paradigm"}, true},
		{"apparition ghost", []string{"paradigm"}, false}, // substring but not whole word
		{"redefine value", []string{"define"}, false},     // substring but not whole word
		{"define", []string{"define"}, true},              // exact match
		{"please define", []string{"define"}, true},       // word at end
		{"define please", []string{"define"}, true},       // word at start
		{"no match here", []string{"explain", "define"}, false},
	}

	for _, tt := range tests {
		got := containsWord(tt.s, tt.subs...)
		if got != tt.want {
			t.Errorf("containsWord(%q, %v) = %v, want %v", tt.s, tt.subs, got, tt.want)
		}
	}
}

func TestAnalyzeSuggest(t *testing.T) {
	cfg := config.Default()
	ib := NewInputBar(cfg)

	cases := []struct {
		input string
		want  string
	}{
		{"", ""},
		{"explain gravity", "flash"},
		{"paradigm shift in physics", "turbo"},
		{"problem1, problem2, problem3", "turbofactory"},
		{"research quantum computing", "discover"},
	}

	for _, c := range cases {
		ib.TextArea.SetValue(c.input)
		ib.AnalyzeSuggest()
		if ib.SuggestedMode != c.want {
			t.Errorf("AnalyzeSuggest(%q) = %q, want %q", c.input, ib.SuggestedMode, c.want)
		}
	}
}
