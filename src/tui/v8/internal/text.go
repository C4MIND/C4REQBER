package internal

import (
	"encoding/json"
	"fmt"
	"strconv"
	"strings"

	"github.com/mattn/go-runewidth"
)

// ToFloat64 converts a value from map[string]any (json.Number, float64, int, string) to float64.
func ToFloat64(v any) (float64, bool) {
	switch n := v.(type) {
	case float64:
		return n, true
	case float32:
		return float64(n), true
	case int:
		return float64(n), true
	case int8:
		return float64(n), true
	case int16:
		return float64(n), true
	case int32:
		return float64(n), true
	case int64:
		return float64(n), true
	case uint:
		return float64(n), true
	case uint8:
		return float64(n), true
	case uint16:
		return float64(n), true
	case uint32:
		return float64(n), true
	case uint64:
		return float64(n), true
	case json.Number:
		f, err := n.Float64()
		return f, err == nil
	case string:
		f, err := strconv.ParseFloat(n, 64)
		return f, err == nil
	case nil:
		return 0, false
	default:
		// Try fmt.Sscanf as last resort
		var f float64
		if _, err := fmt.Sscanf(fmt.Sprint(n), "%f", &f); err == nil {
			return f, true
		}
		return 0, false
	}
}

// TruncateRunes truncates a string to max visible width, adding "..." if truncated.
// CJK characters and emoji are counted at their displayed width.
func TruncateRunes(s string, max int) string {
	if max <= 3 {
		return s
	}
	if runewidth.StringWidth(s) <= max {
		return s
	}
	var w int
	var out []rune
	for _, r := range s {
		rw := runewidth.RuneWidth(r)
		if w+rw > max-3 {
			break
		}
		w += rw
		out = append(out, r)
	}
	return string(out) + "..."
}

// WrapRunes wraps text at max visible width per line.
// CJK characters and emoji are counted at their displayed width.
func WrapRunes(s string, width int) string {
	if width <= 0 {
		return s
	}
	var lines []string
	var current []rune
	currentW := 0

	for _, r := range s {
		if r == '\n' {
			lines = append(lines, string(current))
			current = nil
			currentW = 0
			continue
		}
		rw := runewidth.RuneWidth(r)
		if r == ' ' && currentW >= width {
			lines = append(lines, string(current))
			current = nil
			currentW = 0
			continue
		}
		if currentW+rw > width {
			lines = append(lines, string(current))
			current = []rune{r}
			currentW = rw
			continue
		}
		current = append(current, r)
		currentW += rw
	}
	if len(current) > 0 {
		lines = append(lines, string(current))
	}
	return strings.Join(lines, "\n")
}
