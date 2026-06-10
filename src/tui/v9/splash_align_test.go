package tui

import (
	"strings"
	"testing"
)

func TestSplash_ContentWidthSplash_TrimsTrailing(t *testing.T) {
	// "abc   " has 3 visible chars, but lenRunes = 6.
	if got := contentWidthSplash("abc   "); got != 3 {
		t.Errorf("contentWidthSplash('abc   ') = %d, want 3", got)
	}
	if got := contentWidthSplash(""); got != 0 {
		t.Errorf("contentWidthSplash('') = %d, want 0", got)
	}
	if got := contentWidthSplash("   "); got != 0 {
		t.Errorf("contentWidthSplash('   ') = %d, want 0", got)
	}
	if got := contentWidthSplash("abcdef"); got != 6 {
		t.Errorf("contentWidthSplash('abcdef') = %d, want 6", got)
	}
}

func TestSplash_FindFirstLastNonBlank(t *testing.T) {
	if got := findFirstNonBlank("abc"); got != 0 {
		t.Errorf("findFirstNonBlank('abc') = %d, want 0", got)
	}
	if got := findFirstNonBlank("  abc"); got != 2 {
		t.Errorf("findFirstNonBlank('  abc') = %d, want 2", got)
	}
	if got := findFirstNonBlank("   "); got != -1 {
		t.Errorf("findFirstNonBlank('   ') = %d, want -1", got)
	}
	if got := findLastNonBlank("abc"); got != 2 {
		t.Errorf("findLastNonBlank('abc') = %d, want 2", got)
	}
	if got := findLastNonBlank("abc   "); got != 2 {
		t.Errorf("findLastNonBlank('abc   ') = %d, want 2", got)
	}
	if got := findLastNonBlank("   "); got != -1 {
		t.Errorf("findLastNonBlank('   ') = %d, want -1", got)
	}
}

func TestSplash_VisualCenterColumnSplash_AllWhitespace(t *testing.T) {
	lines := []string{"   ", "   ", "   "}
	if got := visualCenterColumnSplash(lines); got != 0 {
		t.Errorf("all whitespace: got %f, want 0", got)
	}
}

func TestSplash_VisualCenterColumnSplash_Symmetric(t *testing.T) {
	// A symmetric block of 5 chars centered in 9-wide line: center = 4.
	lines := []string{"    X    "}
	if got := visualCenterColumnSplash(lines); got != 4 {
		t.Errorf("symmetric: got %f, want 4", got)
	}
}

func TestSplash_VisualCenterColumnSplash_Weighted(t *testing.T) {
	// Two lines of different widths — wider line should dominate.
	// Line A: "  X  " (1 char at col 2, width 1, center 2)
	// Line B: "  YYYYY  " (5 chars at cols 2-6, width 5, center 4)
	// Weighted avg: (2*1 + 4*5) / (1+5) = 22/6 = 3.667
	lines := []string{"  X  ", "  YYYYY  "}
	got := visualCenterColumnSplash(lines)
	want := (2.0*1 + 4.0*5) / 6.0
	if got != want {
		t.Errorf("weighted: got %f, want %f", got, want)
	}
}

func TestSplash_BuildSplashFinalForm_AlignsCubeAndC4R(t *testing.T) {
	// v9.11.4: cube and C4R should have matching visual centers.
	// We can't easily render the full 50-row layout, but we can
	// assert that buildSplashFinalForm returns lines where the
	// cube block and the C4R block have aligned visual centers.
	out := buildSplashFinalForm(50, false)
	if len(out) == 0 {
		t.Fatal("buildSplashFinalForm returned no lines")
	}
	// Find cube block: first non-blank line that contains ".."
	// and C4R block: line containing "1111111111" with multiple "1"s.
	cubeStart, c4rStart := -1, -1
	for i, l := range out {
		if cubeStart < 0 && strings.Contains(l, "..") {
			cubeStart = i
		}
		if c4rStart < 0 && strings.Contains(l, "111111111111111111") {
			c4rStart = i
		}
	}
	if cubeStart < 0 {
		t.Fatal("could not find cube block")
	}
	if c4rStart < 0 {
		t.Fatal("could not find C4R block")
	}
	// Extract cube block (until empty line) and C4R block (from
	// c4rStart to end).
	cubeEnd := cubeStart
	for cubeEnd < len(out) && strings.TrimSpace(out[cubeEnd]) != "" {
		cubeEnd++
	}
	cubeBlock := out[cubeStart:cubeEnd]
	c4rBlock := out[c4rStart:]
	cubeCenter := visualCenterColumnSplash(cubeBlock)
	c4rCenter := visualCenterColumnSplash(c4rBlock)
	// v9.11.4: cube and C4R should align to within 1 column of each
	// other. Before the fix, they were off by 30+ columns.
	diff := cubeCenter - c4rCenter
	if diff < 0 {
		diff = -diff
	}
	if diff > 1.0 {
		t.Errorf("cube and C4R visual centers differ by %.1f cols (cube=%.1f, c4r=%.1f); should be within 1.0",
			diff, cubeCenter, c4rCenter)
	}
}
