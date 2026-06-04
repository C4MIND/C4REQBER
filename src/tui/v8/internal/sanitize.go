package internal

import (
	"regexp"
	"strings"
	"unicode"

	"golang.org/x/text/unicode/norm"
)

var htmlRe = regexp.MustCompile(`<[^>]+>`)

// Input sanitizes user text: NFKC normalization, HTML tag stripping,
// control character removal (except \n and \t), trimming.
func Input(text string) string {
	// NFKC normalization
	text = norm.NFKC.String(text)
	// Strip HTML tags
	text = htmlRe.ReplaceAllString(text, "")
	// Remove control characters except \n and \t
	text = strings.Map(func(r rune) rune {
		if r == '\n' || r == '\t' {
			return r
		}
		if unicode.IsControl(r) {
			return -1
		}
		return r
	}, text)
	return strings.TrimSpace(text)
}
