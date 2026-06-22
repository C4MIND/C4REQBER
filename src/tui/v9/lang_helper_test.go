package tui

import "github.com/figuramax/c4reqber-tui-v9/i18n"

func langFromString(s string) i18n.Lang {
	switch s {
	case "en":
		return i18n.LangEN
	case "ru":
		return i18n.LangRU
	case "zh":
		return i18n.LangZH
	case "ja":
		return i18n.LangJA
	case "de":
		return i18n.LangDE
	case "ar":
		return i18n.LangAR
	case "hi":
		return i18n.LangHI
	}
	return i18n.LangEN
}
