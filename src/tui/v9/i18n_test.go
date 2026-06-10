package tui

import (
	"strings"
	"testing"
)

func TestAllKeysPresentEN(t *testing.T) {
	en := translations[LangEN]
	required := []string{
		"app.title", "app.lang", "app.model", "footer.ready", "footer.running",
		"footer.done", "footer.cost", "keymap.run", "keymap.help", "keymap.quit",
		"keymap.cancel", "phase.a", "phase.b", "phase.c", "phase.d", "phase.e",
		"phase.f", "phase.g", "card.phase.status", "card.hypothesis.t",
		"card.paper.t", "card.code.t", "card.error.t", "empty.title", "empty.hint",
		"placeholder", "toast.empty", "toast.cancelled", "toast.complete",
		"toast.submit_failed",
	}
	for _, k := range required {
		if v, ok := en[k]; !ok || v == "" {
			t.Errorf("EN missing key: %s", k)
		}
	}
}

func TestAllKeysPresentRU(t *testing.T) {
	ru := translations[LangRU]
	en := translations[LangEN]
	for k := range en {
		if rv, ok := ru[k]; !ok {
			t.Errorf("RU missing key: %s", k)
		} else if rv == "" {
			t.Errorf("RU empty value for: %s", k)
		} else if strings.Contains(rv, k) {
			t.Errorf("RU has English key as value for %s: %s", k, rv)
		}
	}
}

func TestTDefaultToEN(t *testing.T) {
	defer SetLang(LangEN)
	SetLang(LangEN)
	if T("app.title") != "C4REQBER v9" {
		t.Error("EN title wrong")
	}
}

func TestTLangSwitch(t *testing.T) {
	defer SetLang(LangEN)
	SetLang(LangEN)
	if !strings.Contains(T("keymap.run"), "Run") {
		t.Error("EN run keymap")
	}
	SetLang(LangRU)
	if !strings.Contains(T("keymap.run"), "Запуск") {
		t.Error("RU run keymap")
	}
}
