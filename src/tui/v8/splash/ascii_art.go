package splash

import (
	_ "embed"
	"math/rand"
	"strings"
)

//go:embed green_cube.txt
var greenCubeRaw string

// Pre-computed art slices to avoid re-parsing on every render frame.
var (
	greenCubeLines = splitLines(greenCubeRaw)
	bigC4RLines    = padToMaxWidth(splitLines(bigC4R))
	asciiC4RLines  = splitLines(asciiC4R)
)

// splitLines trims surrounding newlines and splits on "\n".
func splitLines(s string) []string {
	return strings.Split(strings.Trim(s, "\n"), "\n")
}

// bigC4R is a large block-letter C4R built from digit 1s.
const bigC4R = `
        11111111111111111111                11111        111111111111111111111
       1111111111111111111111             1111111        1111111111111111111111
       1111                             111111111        1111              1111
       1111                           111111 1111        1111              1111
       1111                         11111    1111        1111              1111
       1111                       11111      1111        1111111111111111111111
       1111                     111111111111111111111    11111111111111111111
       1111                     111111111111111111111    1111        11111
       1111                                  1111        1111          11111
       1111111111111111111111                1111        1111           111111
         11111111111111111111                1111        1111             11111
`

// asciiC4R is a stylized C4R logo using Unicode box-drawing and block chars.
const asciiC4R = `
        ┌──────────────┐
        │  ╔════════╗  │
        │  ║  C 4   ║  │
        │  ║   R    ║  │
        │  ╚════════╝  │
        │   ████████   │
        │   █ EXO  █   │
        │   ████████   │
        └──────────────┘
`

// AppVersion is displayed on the splash screen.
const AppVersion = "v8.1.0"

// scrambleChars are used during the morph transition.
// All chars are strictly width-1 to preserve alignment.
var scrambleChars = []rune("░▒▓█▄▀▌▐│─┌┐└┘@#%&*+=-~:.")

const formHeight = 50

// compactModeThreshold is the terminal height below which we show
// the compact asciiC4R instead of the big cube + bigC4R.
const compactModeThreshold = 30

// buildFinalForm composes the final art padded to h.
// In compact mode it shows asciiC4R; otherwise green cube + bigC4R.
func buildFinalForm(h int, compact bool) []string {
	if h <= 0 {
		h = formHeight
	}
	if compact {
		return padToHeight(asciiC4RLines, h)
	}
	lines := make([]string, 0, len(greenCubeLines)+1+len(bigC4RLines))
	lines = append(lines, greenCubeLines...)
	lines = append(lines, "") // spacer
	lines = append(lines, bigC4RLines...)

	return padToHeight(lines, h)
}

// buildForms returns morph forms: stripped ANSI → noise → C4R → final.
// In compact mode the C4R and final forms use asciiC4R.
func buildForms(h int, seedArt string, compact bool, rng *rand.Rand) [][]string {
	if h <= 0 {
		h = formHeight
	}
	final := buildFinalForm(h, compact)

	// Form 0: stripped ANSI art (original purple crystal)
	form0 := padToHeight(splitLines(seedArt), h)

	// Form 1: heavy noise derived from seed
	form1 := make([]string, len(form0))
	for i, line := range form0 {
		runes := []rune(line)
		for j := range runes {
			if runes[j] != ' ' && rng.Float64() < 0.7 {
				runes[j] = scrambleChars[rng.Intn(len(scrambleChars))]
			}
		}
		form1[i] = string(runes)
	}

	// Form 2: C4R block letters (compact or big)
	var c4r []string
	if compact {
		c4r = asciiC4RLines
	} else {
		c4r = bigC4RLines
	}
	form2 := padToHeight(c4r, h)

	return [][]string{form0, form1, form2, final}
}

// padToMaxWidth right-pads all lines with spaces so every line has the same
// visual width. This prevents per-line centering from breaking block shapes.
func padToMaxWidth(lines []string) []string {
	max := 0
	for _, l := range lines {
		if w := len([]rune(l)); w > max {
			max = w
		}
	}
	out := make([]string, len(lines))
	for i, l := range lines {
		if w := len([]rune(l)); w < max {
			l = l + strings.Repeat(" ", max-w)
		}
		out[i] = l
	}
	return out
}

// padToHeight pads content to height h with blank lines above it,
// truncating from the top if too tall so the bottom (C4R) is always
// preserved. Bottom-alignment eliminates unwanted gaps between art
// and text when View() pins content to the bottom of the screen.
func padToHeight(lines []string, h int) []string {
	if h <= 0 {
		return []string{}
	}
	if len(lines) >= h {
		// Truncate from the top — keep the bottom portion (C4R)
		start := len(lines) - h
		return lines[start:]
	}
	padTop := h - len(lines)
	res := make([]string, 0, h)
	for i := 0; i < padTop; i++ {
		res = append(res, "")
	}
	res = append(res, lines...)
	return res
}
