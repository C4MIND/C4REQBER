package tui

import (
	"bufio"
	"os"
	"regexp"
	"strings"
	"sync"
)

type Lang string

const (
	LangEN Lang = "en"
	LangRU Lang = "ru"
)

var (
	currentLangMu sync.RWMutex
	currentLang   Lang = LangEN
)

func T(key string) string {
	currentLangMu.RLock()
	l := currentLang
	currentLangMu.RUnlock()
	return TFor(key, l)
}

func TFor(key string, lang Lang) string {
	if val, ok := translations[lang][key]; ok {
		return val
	}
	if val, ok := translations[LangEN][key]; ok {
		return val
	}
	return key
}

func SetLang(l Lang) {
	currentLangMu.Lock()
	defer currentLangMu.Unlock()
	currentLang = l
}

func GetLang() Lang {
	currentLangMu.RLock()
	defer currentLangMu.RUnlock()
	return currentLang
}

var translations = map[Lang]map[string]string{
	LangEN: {
		"app.title":           "C4REQBER v9",
		"app.lang":            "EN",
		"app.model":           "DeepSeek",
		"footer.ready":        "READY",
		"footer.running":      "RUNNING",
		"footer.done":         "COMPLETE",
		"footer.cost":         "$0.00",
		"keymap.run":          "Run",
		"keymap.help":         "Help",
		"keymap.quit":         "Quit",
		"keymap.cancel":       "Cancel",
		"phase.a":             "Framing",
		"phase.b":             "Knowledge acquisition",
		"phase.c":             "Gap analysis",
		"phase.d":             "Hypothesis generation",
		"phase.e":             "Simulation",
		"phase.f":             "Dissertation",
		"phase.g":             "Quality control",
		"card.phase.status":   "in progress",
		"card.hypothesis.t":   "Hypothesis",
		"card.paper.t":        "Paper",
		"card.code.t":         "Simulation",
		"card.error.t":        "Error",
		"empty.title":         "Ready for your first discovery",
		"empty.hint":          "Type a question above and press Enter",
		"placeholder":         "design a CRISPR guide RNA with minimal off-targets in T-cells",
		"toast.empty":         "Type a problem first",
		"toast.cancelled":     "Cancelled",
		"toast.complete":      "Discovery complete",
		"toast.submit_failed": "Submit failed",
	},
	LangRU: {
		"app.title":           "C4REQBER v9",
		"app.lang":            "RU",
		"app.model":           "DeepSeek",
		"footer.ready":        "ГОТОВ",
		"footer.running":      "ИДЁТ",
		"footer.done":         "ГОТОВО",
		"footer.cost":         "$0.00",
		"keymap.run":          "Запуск",
		"keymap.help":         "Помощь",
		"keymap.quit":         "Выход",
		"keymap.cancel":       "Отмена",
		"phase.a":             "Фрейминг",
		"phase.b":             "Сбор знаний",
		"phase.c":             "Анализ пробелов",
		"phase.d":             "Генерация гипотез",
		"phase.e":             "Симуляция",
		"phase.f":             "Диссертация",
		"phase.g":             "Контроль качества",
		"card.phase.status":   "в процессе",
		"card.hypothesis.t":   "Гипотеза",
		"card.paper.t":        "Статья",
		"card.code.t":         "Симуляция",
		"card.error.t":        "Ошибка",
		"empty.title":         "Готов к первому открытию",
		"empty.hint":          "Введи вопрос выше и нажми Enter",
		"placeholder":         "спроектируй guide RNA для CRISPR с минимальными off-targets в T-клетках",
		"toast.empty":         "Сначала введи задачу",
		"toast.cancelled":     "Отменено",
		"toast.complete":      "Открытие завершено",
		"toast.submit_failed": "Ошибка отправки",
	},
}

// LoadLangFromToml is a stub for future TOML loading.
func LoadLangFromToml(path string, lang Lang) error {
	f, err := os.Open(path)
	if err != nil {
		return err
	}
	defer f.Close()
	m := translations[lang]
	if m == nil {
		m = map[string]string{}
		translations[lang] = m
	}
	scanner := bufio.NewScanner(f)
	keyRe := regexp.MustCompile(`^([a-z0-9_.]+)\s*=\s*"([^"]*)"\s*$`)
	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		matches := keyRe.FindStringSubmatch(line)
		if len(matches) == 3 {
			m[matches[1]] = matches[2]
		}
	}
	return scanner.Err()
}
