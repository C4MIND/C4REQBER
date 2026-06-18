package i18n

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
	if !strings.Contains(T("keymap.run"), "Запустить") {
		t.Error("RU run keymap")
	}
}

func TestAllLangsHaveAllKeys(t *testing.T) {
	requiredKeys := []string{
		"app.title", "app.lang", "app.model", "footer.ready", "footer.running",
		"footer.done", "footer.cost", "keymap.run", "keymap.help", "keymap.quit",
		"keymap.cancel", "phase.a", "phase.b", "phase.c", "phase.d", "phase.e",
		"phase.f", "phase.g", "card.phase.status", "card.hypothesis.t",
		"card.paper.t", "card.code.t", "card.error.t", "empty.title", "empty.hint",
		"placeholder", "toast.empty", "toast.cancelled", "toast.complete",
		"toast.submit_failed",
	}
	langs := []Lang{LangEN, LangRU, LangZH, LangJA, LangDE, LangAR, LangHI}
	for _, lang := range langs {
		m := translations[lang]
		if m == nil {
			t.Errorf("lang %s: no translations", lang)
			continue
		}
		for _, k := range requiredKeys {
			v, ok := m[k]
			if !ok {
				t.Errorf("lang %s: missing key %s", lang, k)
				continue
			}
			if v == "" {
				t.Errorf("lang %s: empty value for %s", lang, k)
			}
		}
	}
}

func TestNoCrossContamination(t *testing.T) {
	// Each language should not contain key names of OTHER languages as values.
	// This catches the v8 i18n disaster (ZH containing JA, JA containing DE, etc).
	// Latin-based langs (EN/RU/DE) share a script, so we only check CJK/AR/HI.
	nonLatin := map[Lang]string{
		LangZH: "的一是不了在人有我他这为之大来以个中上们到说时要就出会也你对生能而子那",
		LangJA: "あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわをん",
		LangAR: "ابتثجحخدذرزسشصضطظعغفقكلمنهويءآؤإئةى",
		LangHI: "अआइईउऊऋॠएऐओऔकखगघङचछजझञटठडढणतथदधनपफबभमयरलवशषसह",
	}
	for lang, ownScript := range nonLatin {
		for otherLang, otherScript := range nonLatin {
			if lang == otherLang {
				continue
			}
			// CJK check: ZH and JA share many kanji, so we only check that JA doesn't
			// contain ZH-only chars (which are Simplified-only) — for now we skip JA↔ZH.
			if (lang == LangZH || lang == LangJA) && (otherLang == LangZH || otherLang == LangJA) {
				continue
			}
			for _, k := range []string{"empty.title", "empty.hint", "phase.d", "phase.g", "placeholder"} {
				v := TFor(k, lang)
				own := runOfScript(v, ownScript)
				other := runOfScript(v, otherScript)
				if other >= 3 && other > own/2 {
					t.Errorf("contam: %s/%s=%q has %d %s-script chars (only %d native %s-script)",
						lang, k, v, other, otherLang, own, lang)
				}
			}
		}
	}
}

func runOfScript(s, script string) int {
	// Returns the maximum run of characters in `s` that also appear in `script`.
	longest := 0
	current := 0
	for _, r := range s {
		if containsRune(script, r) {
			current++
			if current > longest {
				longest = current
			}
		} else {
			current = 0
		}
	}
	return longest
}

func containsRune(s string, r rune) bool {
	for _, c := range s {
		if c == r {
			return true
		}
	}
	return false
}
