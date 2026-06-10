// Package i18n provides translation lookups for the TUI v9.
package i18n

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
	LangZH Lang = "zh"
	LangJA Lang = "ja"
	LangDE Lang = "de"
	LangAR Lang = "ar"
	LangHI Lang = "hi"
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

func Translations() map[Lang]map[string]string {
	cp := make(map[Lang]map[string]string, len(translations))
	for k, v := range translations {
		inner := make(map[string]string, len(v))
		for ik, iv := range v {
			inner[ik] = iv
		}
		cp[k] = inner
	}
	return cp
}

func SetTranslations(lang Lang, m map[string]string) {
	if m == nil {
		return
	}
	currentLangMu.Lock()
	defer currentLangMu.Unlock()
	if translations[lang] == nil {
		translations[lang] = make(map[string]string)
	}
	for k, v := range m {
		translations[lang][k] = v
	}
}

// All translations are stored in i18n/*.toml files (one per language) and
// loaded at init via LoadDefaults(). The maps below are pre-populated with
// fallbacks so unit tests work without filesystem access.
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

		"achievement.first.name":   "First Discovery",
		"achievement.first.desc":   "Run your first discovery",
		"achievement.qualityS.name": "Quality S",
		"achievement.qualityS.desc": "Hypothesis with ≥80% confidence",
		"achievement.multiPaper.name": "Multi-source",
		"achievement.multiPaper.desc": "Cited 3+ papers in one discovery",
		"achievement.ten.name":  "10 Discoveries",
		"achievement.ten.desc":  "Complete 10 discoveries",
		"achievement.speed.name": "Speed Demon",
		"achievement.speed.desc": "Discovery under 30 seconds",
		"achievement.linguist.name": "Polyglot",
		"achievement.linguist.desc": "Used 3+ languages",
		"achievement.streak.name": "On Fire",
		"achievement.streak.desc": "5 discoveries in one session",

		"mode.discover":     "Discover",
		"mode.flash":        "Flash",
		"mode.turbo":        "Turbo",
		"mode.turbofactory": "TurboFactory",

		"lang.name": "Language",
		"keymap.cycle_mode":   "Mode",
		"keymap.cycle_lang":   "Lang",
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

		"achievement.first.name":   "Первое открытие",
		"achievement.first.desc":   "Запусти своё первое открытие",
		"achievement.qualityS.name": "Качество S",
		"achievement.qualityS.desc": "Гипотеза с уверенностью ≥80%",
		"achievement.multiPaper.name": "Мульти-источник",
		"achievement.multiPaper.desc": "Процитировано 3+ статей в одном открытии",
		"achievement.ten.name":  "10 открытий",
		"achievement.ten.desc":  "Заверши 10 открытий",
		"achievement.speed.name": "Демон скорости",
		"achievement.speed.desc": "Открытие менее 30 секунд",
		"achievement.linguist.name": "Полиглот",
		"achievement.linguist.desc": "Использовано 3+ языка",
		"achievement.streak.name": "В ударе",
		"achievement.streak.desc": "5 открытий за сессию",

		"mode.discover":     "Открытие",
		"mode.flash":        "Вспышка",
		"mode.turbo":        "Турбо",
		"mode.turbofactory": "Турбо-фабрика",

		"lang.name": "Язык",
		"keymap.cycle_mode":   "Режим",
		"keymap.cycle_lang":   "Язык",
	},
	LangZH: {
		"app.title":           "C4REQBER v9",
		"app.lang":            "ZH",
		"app.model":           "DeepSeek",
		"footer.ready":        "就绪",
		"footer.running":      "运行中",
		"footer.done":         "已完成",
		"footer.cost":         "$0.00",
		"keymap.run":          "运行",
		"keymap.help":         "帮助",
		"keymap.quit":         "退出",
		"keymap.cancel":       "取消",
		"phase.a":             "框架",
		"phase.b":             "知识获取",
		"phase.c":             "差距分析",
		"phase.d":             "假设生成",
		"phase.e":             "模拟",
		"phase.f":             "论文",
		"phase.g":             "质量控制",
		"card.phase.status":   "进行中",
		"card.hypothesis.t":   "假设",
		"card.paper.t":        "论文",
		"card.code.t":         "模拟",
		"card.error.t":        "错误",
		"empty.title":         "准备进行首次发现",
		"empty.hint":          "在上方输入问题并按Enter键",
		"placeholder":         "设计一个在T细胞中具有最小脱靶效应的CRISPR引导RNA",
		"toast.empty":         "请先输入问题",
		"toast.cancelled":     "已取消",
		"toast.complete":      "发现完成",
		"toast.submit_failed": "提交失败",

		"achievement.first.name":   "首次发现",
		"achievement.first.desc":   "运行您的首次发现",
		"achievement.qualityS.name": "S 级质量",
		"achievement.qualityS.desc": "置信度 ≥80% 的假设",
		"achievement.multiPaper.name": "多源",
		"achievement.multiPaper.desc": "单次发现引用 3+ 篇论文",
		"achievement.ten.name":  "10 次发现",
		"achievement.ten.desc":  "完成 10 次发现",
		"achievement.speed.name": "速度恶魔",
		"achievement.speed.desc": "30 秒内完成发现",
		"achievement.linguist.name": "多语言者",
		"achievement.linguist.desc": "使用 3+ 种语言",
		"achievement.streak.name": "连击中",
		"achievement.streak.desc": "单次会话中 5 次发现",

		"mode.discover":     "发现",
		"mode.flash":        "闪速",
		"mode.turbo":        "特利兹",
		"mode.turbofactory": "特利兹工厂",

		"lang.name": "语言",
		"keymap.cycle_mode":   "模式",
		"keymap.cycle_lang":   "语言",
	},
	LangJA: {
		"app.title":           "C4REQBER v9",
		"app.lang":            "JA",
		"app.model":           "DeepSeek",
		"footer.ready":        "準備完了",
		"footer.running":      "実行中",
		"footer.done":         "完了",
		"footer.cost":         "$0.00",
		"keymap.run":          "実行",
		"keymap.help":         "ヘルプ",
		"keymap.quit":         "終了",
		"keymap.cancel":       "キャンセル",
		"phase.a":             "フレーミング",
		"phase.b":             "知識獲得",
		"phase.c":             "ギャップ分析",
		"phase.d":             "仮説生成",
		"phase.e":             "シミュレーション",
		"phase.f":             "論文",
		"phase.g":             "品質管理",
		"card.phase.status":   "進行中",
		"card.hypothesis.t":   "仮説",
		"card.paper.t":        "論文",
		"card.code.t":         "シミュレーション",
		"card.error.t":        "エラー",
		"empty.title":         "最初の発見の準備ができました",
		"empty.hint":          "上記に質問を入力してEnterキーを押してください",
		"placeholder":         "T細胞でオフターゲットが最小限のCRISPRガイドRNAを設計する",
		"toast.empty":         "まず問題を入力してください",
		"toast.cancelled":     "キャンセルされました",
		"toast.complete":      "発見完了",
		"toast.submit_failed": "送信失敗",

		"achievement.first.name":   "初発見",
		"achievement.first.desc":   "初めての発見を実行",
		"achievement.qualityS.name": "品質S",
		"achievement.qualityS.desc": "信頼度80%以上の仮説",
		"achievement.multiPaper.name": "マルチソース",
		"achievement.multiPaper.desc": "1回の発見で3本以上の論文を引用",
		"achievement.ten.name":  "10発見",
		"achievement.ten.desc":  "10回発見を完了",
		"achievement.speed.name": "スピードデーモン",
		"achievement.speed.desc": "30秒以内に発見完了",
		"achievement.linguist.name": "ポリグロット",
		"achievement.linguist.desc": "3言語以上を使用",
		"achievement.streak.name": "連勝中",
		"achievement.streak.desc": "セッションで5発見",

		"mode.discover":     "発見",
		"mode.flash":        "フラッシュ",
		"mode.turbo":        "ターボ",
		"mode.turbofactory": "ターボファクトリー",

		"lang.name": "言語",
		"keymap.cycle_mode":   "モード",
		"keymap.cycle_lang":   "言語",
	},
	LangDE: {
		"app.title":           "C4REQBER v9",
		"app.lang":            "DE",
		"app.model":           "DeepSeek",
		"footer.ready":        "Bereit",
		"footer.running":      "Läuft",
		"footer.done":         "Abgeschlossen",
		"footer.cost":         "$0.00",
		"keymap.run":          "Ausführen",
		"keymap.help":         "Hilfe",
		"keymap.quit":         "Beenden",
		"keymap.cancel":       "Abbrechen",
		"phase.a":             "Framing",
		"phase.b":             "Wissenserwerb",
		"phase.c":             "Lückenanalyse",
		"phase.d":             "Hypothesengenerierung",
		"phase.e":             "Simulation",
		"phase.f":             "Dissertation",
		"phase.g":             "Qualitätskontrolle",
		"card.phase.status":   "in Bearbeitung",
		"card.hypothesis.t":   "Hypothese",
		"card.paper.t":        "Papier",
		"card.code.t":         "Simulation",
		"card.error.t":        "Fehler",
		"empty.title":         "Bereit für Ihre erste Entdeckung",
		"empty.hint":          "Geben Sie oben eine Frage ein und drücken Sie Enter",
		"placeholder":         "Entwerfen Sie eine CRISPR-Führungs-RNA mit minimalen Off-Target-Effekten in T-Zellen",
		"toast.empty":         "Bitte geben Sie zuerst ein Problem ein",
		"toast.cancelled":     "Abgebrochen",
		"toast.complete":      "Entdeckung abgeschlossen",
		"toast.submit_failed": "Übermittlung fehlgeschlagen",

		"achievement.first.name":   "Erste Entdeckung",
		"achievement.first.desc":   "Führen Sie Ihre erste Entdeckung durch",
		"achievement.qualityS.name": "Qualität S",
		"achievement.qualityS.desc": "Hypothese mit ≥80% Konfidenz",
		"achievement.multiPaper.name": "Multi-Quelle",
		"achievement.multiPaper.desc": "3+ Papiere in einer Entdeckung zitiert",
		"achievement.ten.name":  "10 Entdeckungen",
		"achievement.ten.desc":  "10 Entdeckungen abschließen",
		"achievement.speed.name": "Geschwindigkeitsdämon",
		"achievement.speed.desc": "Entdeckung unter 30 Sekunden",
		"achievement.linguist.name": "Polyglott",
		"achievement.linguist.desc": "3+ Sprachen verwendet",
		"achievement.streak.name": "In Serie",
		"achievement.streak.desc": "5 Entdeckungen in einer Sitzung",

		"mode.discover":     "Entdecken",
		"mode.flash":        "Blitz",
		"mode.turbo":        "Turbo",
		"mode.turbofactory": "Turbo-Fabrik",

		"lang.name": "Sprache",
		"keymap.cycle_mode":   "Modus",
		"keymap.cycle_lang":   "Sprache",
	},
	LangAR: {
		"app.title":           "C4REQBER v9",
		"app.lang":            "AR",
		"app.model":           "DeepSeek",
		"footer.ready":        "جاهز",
		"footer.running":      "قيد التشغيل",
		"footer.done":         "مكتمل",
		"footer.cost":         "$0.00",
		"keymap.run":          "تشغيل",
		"keymap.help":         "مساعدة",
		"keymap.quit":         "خروج",
		"keymap.cancel":       "إلغاء",
		"phase.a":             "التأطير",
		"phase.b":             "اكتساب المعرفة",
		"phase.c":             "تحليل الفجوات",
		"phase.d":             "توليد الفرضية",
		"phase.e":             "المحاكاة",
		"phase.f":             "أطروحة",
		"phase.g":             "مراقبة الجودة",
		"card.phase.status":   "قيد التنفيذ",
		"card.hypothesis.t":   "فرضية",
		"card.paper.t":        "ورقة",
		"card.code.t":         "محاكاة",
		"card.error.t":        "خطأ",
		"empty.title":         "جاهز لاكتشافك الأول",
		"empty.hint":          "اكتب سؤالاً أعلاه واضغط على Enter",
		"placeholder":         "تصميم دليل CRISPR RNA بأقل تأثيرات خارج الهدف في الخلايا التائية",
		"toast.empty":         "يرجى كتابة المشكلة أولاً",
		"toast.cancelled":     "تم الإلغاء",
		"toast.complete":      "اكتشاف مكتمل",
		"toast.submit_failed": "فشل الإرسال",

		"achievement.first.name":   "الاكتشاف الأول",
		"achievement.first.desc":   "قم بأول اكتشاف لك",
		"achievement.qualityS.name": "جودة S",
		"achievement.qualityS.desc": "فرضية بثقة ≥80%",
		"achievement.multiPaper.name": "متعدد المصادر",
		"achievement.multiPaper.desc": "3+ أوراق في اكتشاف واحد",
		"achievement.ten.name":  "10 اكتشافات",
		"achievement.ten.desc":  "أكمل 10 اكتشافات",
		"achievement.speed.name": "شيطان السرعة",
		"achievement.speed.desc": "اكتشاف في أقل من 30 ثانية",
		"achievement.linguist.name": "متعدد اللغات",
		"achievement.linguist.desc": "استخدم 3+ لغات",
		"achievement.streak.name": "في سلسلة",
		"achievement.streak.desc": "5 اكتشافات في جلسة واحدة",

		"mode.discover":     "اكتشاف",
		"mode.flash":        "وميض",
		"mode.turbo":        "تيربو",
		"mode.turbofactory": "مصنع تيربو",

		"lang.name": "اللغة",
		"keymap.cycle_mode":   "الوضع",
		"keymap.cycle_lang":   "اللغة",
	},
	LangHI: {
		"app.title":           "C4REQBER v9",
		"app.lang":            "HI",
		"app.model":           "DeepSeek",
		"footer.ready":        "तैयार",
		"footer.running":      "चल रहा है",
		"footer.done":         "पूर्ण",
		"footer.cost":         "$0.00",
		"keymap.run":          "चलाएं",
		"keymap.help":         "सहायता",
		"keymap.quit":         "बाहर निकलें",
		"keymap.cancel":       "रद्द करें",
		"phase.a":             "फ्रेमिंग",
		"phase.b":             "ज्ञान अधिग्रहण",
		"phase.c":             "अंतर विश्लेषण",
		"phase.d":             "परिकल्पना जनन",
		"phase.e":             "सिमुलेशन",
		"phase.f":             "शोधप्रबंध",
		"phase.g":             "गुणवत्ता नियंत्रण",
		"card.phase.status":   "प्रगति पर",
		"card.hypothesis.t":   "परिकल्पना",
		"card.paper.t":        "पेपर",
		"card.code.t":         "सिमुलेशन",
		"card.error.t":        "त्रुटि",
		"empty.title":         "आपकी पहली खोज के लिए तैयार",
		"empty.hint":          "ऊपर एक प्रश्न टाइप करें और एंटर दबाएं",
		"placeholder":         "टी-कोशिकाओं में न्यूनतम ऑफ-टार्गेट वाला CRISPR गाइड RNA डिजाइन करें",
		"toast.empty":         "कृपया पहले एक समस्या टाइप करें",
		"toast.cancelled":     "रद्द किया गया",
		"toast.complete":      "खोज पूर्ण",
		"toast.submit_failed": "सबमिट विफल",

		"achievement.first.name":   "पहली खोज",
		"achievement.first.desc":   "अपनी पहली खोज चलाएं",
		"achievement.qualityS.name": "गुणवत्ता S",
		"achievement.qualityS.desc": "80%+ विश्वास के साथ परिकल्पना",
		"achievement.multiPaper.name": "बहु-स्रोत",
		"achievement.multiPaper.desc": "एक खोज में 3+ पेपर उद्धृत",
		"achievement.ten.name":  "10 खोजें",
		"achievement.ten.desc":  "10 खोजें पूर्ण करें",
		"achievement.speed.name": "गति राक्षस",
		"achievement.speed.desc": "30 सेकंड में खोज",
		"achievement.linguist.name": "बहुभाषी",
		"achievement.linguist.desc": "3+ भाषाएँ उपयोग की",
		"achievement.streak.name": "लगातार",
		"achievement.streak.desc": "एक सत्र में 5 खोजें",

		"mode.discover":     "खोज",
		"mode.flash":        "फ्लैश",
		"mode.turbo":        "टर्बो",
		"mode.turbofactory": "टर्बो फैक्टरी",

		"lang.name": "भाषा",
		"keymap.cycle_mode":   "मोड",
		"keymap.cycle_lang":   "भाषा",
	},
}

// LoadLangFromToml loads translations from a TOML file.
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
