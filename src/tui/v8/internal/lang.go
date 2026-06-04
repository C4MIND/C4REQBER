package internal

import "strings"

// Language represents a UI language.
type Language int

const (
	LangEN Language = iota
	LangRU
	LangZH
	LangJA
	LangDE
	LangAR
	LangHI
)

var (
	// AllLanguages is the ordered list of supported languages.
	AllLanguages = []Language{LangEN, LangRU, LangZH, LangJA, LangDE, LangAR, LangHI}

	// LanguageFlags maps languages to emoji flags.
	LanguageFlags = map[Language]string{
		LangEN: "🇬🇧",
		LangRU: "🇷🇺",
		LangZH: "🇨🇳",
		LangJA: "🇯🇵",
		LangDE: "🇩🇪",
		LangAR: "🇸🇦",
		LangHI: "🇮🇳",
	}

	// LanguageNames maps languages to human-readable names.
	LanguageNames = map[Language]string{
		LangEN: "English",
		LangRU: "Русский",
		LangZH: "中文",
		LangJA: "日本語",
		LangDE: "Deutsch",
		LangAR: "العربية",
		LangHI: "हिन्दी",
	}
)

// NextLanguage returns the next language in the cycle.
func NextLanguage(current Language) Language {
	for i, l := range AllLanguages {
		if l == current {
			return AllLanguages[(i+1)%len(AllLanguages)]
		}
	}
	return LangEN
}

// ParseLanguage converts a language code string to a Language constant.
// Supported codes: en, ru, zh, ja, de, ar, hi (case-insensitive).
// Returns LangEN for unknown codes.
func ParseLanguage(code string) Language {
	switch strings.ToLower(code) {
	case "en", "english":
		return LangEN
	case "ru", "russian", "русский":
		return LangRU
	case "zh", "chinese", "中文":
		return LangZH
	case "ja", "japanese", "日本語":
		return LangJA
	case "de", "german", "deutsch":
		return LangDE
	case "ar", "arabic", "العربية":
		return LangAR
	case "hi", "hindi", "हिन्दी":
		return LangHI
	default:
		return LangEN
	}
}
