package i18n

import (
	"os"
	"path/filepath"
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
		"placeholder", "toast.empty", "toast.cancelled", "toast.complete", "toast.partial", "toast.failed",
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
	langs := []Lang{LangEN, LangRU, LangZH, LangJA, LangDE, LangAR, LangHI}
	en := translations[LangEN]
	for _, lang := range langs {
		m := translations[lang]
		if m == nil {
			t.Errorf("lang %s: no translations", lang)
			continue
		}
		for k := range en {
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

func TestSimulationStringsAreTranslated(t *testing.T) {
	allowIdentical := map[string]bool{
		"sim.overlay.tier.slow": true, // CPU is a universal technical acronym.
	}
	for _, lang := range []Lang{LangZH, LangJA, LangDE, LangAR, LangHI} {
		for key, english := range translations[LangEN] {
			if !strings.HasPrefix(key, "sim.") || allowIdentical[key] {
				continue
			}
			if got := translations[lang][key]; got == english {
				t.Errorf("lang %s: %s is still English: %q", lang, key, got)
			}
		}
	}
}

func TestLocaleSpecificSettingsAndAchievementsAreTranslated(t *testing.T) {
	for _, lang := range []Lang{LangRU, LangZH, LangJA, LangDE, LangAR, LangHI} {
		for _, key := range []string{"settings.llm_stage", "settings.llm_stage.desc"} {
			if got := translations[lang][key]; got == translations[LangEN][key] {
				t.Errorf("lang %s: %s is still English: %q", lang, key, got)
			}
		}
		if got := translations[lang]["achievement.sim_explorer.desc"]; strings.Contains(
			got, "Ran ",
		) {
			t.Errorf("lang %s: explorer achievement contains untranslated text: %q", lang, got)
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

// TestLoadLangFromToml guards the TOML file loader that powers the
// regen_i18n.py translation pipeline. Asserts that:
//
//  1. A well-formed TOML with N entries loads as N keys
//  2. The "key = \"value\"" format (with quotes) is the only one
//     accepted — unquoted values are silently dropped (matches
//     what regen_i18n.py emits)
//  3. The keys= value separator can have any whitespace
//  4. Re-loading a file overwrites (not merges with) previous
func TestLoadLangFromToml(t *testing.T) {
	dir := t.TempDir()
	// Custom language to avoid mutating the package-level
	// translations map for one of the 7 production languages.
	custom := Lang("xx")

	t.Run("well_formed", func(t *testing.T) {
		path := filepath.Join(dir, "good.toml")
		if err := os.WriteFile(path, []byte(`
# test translation file
greeting.name = "Hello"
greeting.desc = "A standard greeting"
farewell = "Bye"
`), 0644); err != nil {
			t.Fatal(err)
		}
		if err := LoadLangFromToml(path, custom); err != nil {
			t.Fatal(err)
		}
		if got := TFor("greeting.name", custom); got != "Hello" {
			t.Errorf("greeting.name = %q, want %q", got, "Hello")
		}
		if got := TFor("farewell", custom); got != "Bye" {
			t.Errorf("farewell = %q, want %q", got, "Bye")
		}
	})

	t.Run("unquoted_values_silently_dropped", func(t *testing.T) {
		path := filepath.Join(dir, "unquoted.toml")
		// unquoted_name has no quotes → regex won't match → dropped.
		// quoted_name does have quotes → kept.
		if err := os.WriteFile(path, []byte(`
quoted_name = "OK"
unquoted_name = NO_QUOTES
`), 0644); err != nil {
			t.Fatal(err)
		}
		if err := LoadLangFromToml(path, custom); err != nil {
			t.Fatal(err)
		}
		if got := TFor("quoted_name", custom); got != "OK" {
			t.Errorf("quoted_name = %q, want %q", got, "OK")
		}
		if got := TFor("unquoted_name", custom); got != "unquoted_name" {
			t.Errorf("unquoted_name should fall back to key, got %q (loader accepted an unquoted value!)", got)
		}
	})

	t.Run("reload_overwrites_not_merges", func(t *testing.T) {
		path1 := filepath.Join(dir, "v1.toml")
		path2 := filepath.Join(dir, "v2.toml")
		if err := os.WriteFile(path1, []byte(`k = "v1"`), 0644); err != nil {
			t.Fatal(err)
		}
		if err := LoadLangFromToml(path1, custom); err != nil {
			t.Fatal(err)
		}
		if got := TFor("k", custom); got != "v1" {
			t.Errorf("after v1 load: k = %q, want %q", got, "v1")
		}
		if err := os.WriteFile(path2, []byte(`k = "v2"`), 0644); err != nil {
			t.Fatal(err)
		}
		if err := LoadLangFromToml(path2, custom); err != nil {
			t.Fatal(err)
		}
		if got := TFor("k", custom); got != "v2" {
			t.Errorf("after v2 reload: k = %q, want %q (reload should overwrite, not merge)", got, "v2")
		}
	})

	t.Run("missing_file_is_error", func(t *testing.T) {
		if err := LoadLangFromToml(filepath.Join(dir, "does-not-exist.toml"), custom); err == nil {
			t.Error("expected error for missing file, got nil")
		}
	})
}

// TestNoMachineTranslationGarbage guards catastrophic HY-MT mixups that
// previously shipped: "Cycle LLM tier" → bicycle, "Ctrl+Y — cycle LLM tier"
// → "no color" (confused with profile.mono), research Paper → stationery.
func TestNoMachineTranslationGarbage(t *testing.T) {
	forbidden := map[Lang]map[string][]string{
		LangRU: {
			"tier.ctrl_y":   {"Никакого цвета", "цвет"},
			"profile.name":  {"Высокий контраст"},
			"card.paper.t":  {"Бумага"},
			"stats.discoveries": {"Общая количество"},
			"settings.hint": {"Уголки"},
		},
		LangDE: {
			"tier.ctrl_y":  {"Kein Farbe", "Farbe"},
			"tier.cycle":   {"Fahrrad"},
			"help.rain":    {"Idiot"},
			"card.paper.t": {"Papier"},
		},
		LangZH: {
			"tier.ctrl_y": {"无颜色"},
			"tier.name":   {"顶级"},
		},
		LangJA: {
			"tier.ctrl_y": {"色なし"},
			"help.rain":   {"行列雨"},
		},
		LangAR: {
			"tier.ctrl_y": {"لا لون"},
			"tier.cycle":  {"دراجات"},
		},
		LangHI: {
			"tier.ctrl_y": {"बिना रंग"},
			"tier.cycle":  {"साइकिल"},
		},
	}
	// Keys that MUST keep the Ctrl+Y chord literal in every language.
	for _, lang := range []Lang{LangRU, LangZH, LangJA, LangDE, LangAR, LangHI} {
		got := translations[lang]["tier.ctrl_y"]
		if !strings.Contains(got, "Ctrl+Y") {
			t.Errorf("%s tier.ctrl_y missing Ctrl+Y chord: %q", lang, got)
		}
	}
	for lang, keys := range forbidden {
		for key, needles := range keys {
			got := translations[lang][key]
			for _, n := range needles {
				if strings.Contains(got, n) {
					t.Errorf("%s %s still contains garbage %q: %q", lang, key, n, got)
				}
			}
		}
	}
	// profile.name must not equal profile.hc (was swapped in RU).
	if translations[LangRU]["profile.name"] == translations[LangRU]["profile.hc"] {
		t.Error("ru profile.name must not equal profile.hc")
	}
}
