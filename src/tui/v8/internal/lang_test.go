package internal

import "testing"

func TestNextLanguage(t *testing.T) {
	cases := []struct {
		current  Language
		expected Language
	}{
		{LangEN, LangRU},
		{LangRU, LangZH},
		{LangZH, LangJA},
		{LangJA, LangDE},
		{LangDE, LangAR},
		{LangAR, LangHI},
		{LangHI, LangEN},
	}
	for _, c := range cases {
		got := NextLanguage(c.current)
		if got != c.expected {
			t.Fatalf("NextLanguage(%d) = %d, want %d", c.current, got, c.expected)
		}
	}
}

func TestLanguageFlags(t *testing.T) {
	for _, l := range AllLanguages {
		if LanguageFlags[l] == "" {
			t.Fatalf("missing flag for language %d", l)
		}
	}
}
