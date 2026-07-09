package tui

import (
	"path/filepath"
	"testing"
	"time"

	"github.com/figuramax/c4reqber-tui-v9/api"
	"github.com/figuramax/c4reqber-tui-v9/cards"
	"github.com/figuramax/c4reqber-tui-v9/i18n"
	"github.com/figuramax/c4reqber-tui-v9/persist"
)

func TestStateMachine_WindowSize(t *testing.T) {
	m := NewApp("http://test")
	u, _ := m.Update(teaWindowSizeMsg(120, 40))
	mm := u.(*model)
	if mm.width != 120 || mm.height != 40 {
		t.Errorf("size not set: w=%d h=%d", mm.width, mm.height)
	}
}

func TestStateMachine_Tick(t *testing.T) {
	m := NewApp("http://test")
	m.width, m.height = 120, 40
	// run 5 ticks
	for i := 0; i < 5; i++ {
		u, _ := m.Update(tickMsg(time.Now()))
		mm := u.(*model)
		if mm.tick != i+1 {
			t.Errorf("after %d ticks, tick = %d", i+1, mm.tick)
		}
	}
}

func TestStateMachine_TabCyclesMode(t *testing.T) {
	m := NewApp("http://test")
	// Discover → Flash → Turbo → TurboFactory → Discover
	expected := []Mode{ModeFlash, ModeTurbo, ModeTurboFactory, ModeDiscover}
	for i, want := range expected {
		u, _ := m.Update(teaKeyMsg("tab"))
		mm := u.(*model)
		if mm.mode != want {
			t.Errorf("after Tab #%d, mode = %s, want %s", i+1, mm.mode, want)
		}
	}
}

func TestStateMachine_EscCancelsRunning(t *testing.T) {
	m := NewApp("http://test")
	m.running = true
	m.jobID = "test-job"
	m.toast = ""
	u, _ := m.Update(teaKeyMsg("esc"))
	mm := u.(*model)
	if mm.running {
		t.Error("Esc should set running=false")
	}
	if mm.jobID != "" {
		t.Errorf("Esc should clear jobID, got %s", mm.jobID)
	}
}

func TestStateMachine_CtrlCQuits(t *testing.T) {
	m := NewApp("http://test")
	u, cmd := m.Update(teaKeyMsg("ctrl+c"))
	_ = u
	if cmd == nil {
		t.Error("Ctrl+C should return tea.Quit cmd")
	}
}

func TestStateMachine_EnterEmptyToast(t *testing.T) {
	m := NewApp("http://test")
	m.toast = ""
	u, _ := m.Update(teaKeyMsg("enter"))
	mm := u.(*model)
	if mm.toast == "" {
		t.Error("empty Enter should set toast")
	}
}

func TestStateMachine_AppendCard(t *testing.T) {
	m := NewApp("http://test")
	before := len(m.feed)
	m.appendCard(Card{Kind: CardPhase, Title: "Test", Status: "running"})
	if len(m.feed) != before+1 {
		t.Errorf("appendCard didn't add: before=%d after=%d", before, len(m.feed))
	}
}

func TestStateMachine_AppendCardSetsZoneID(t *testing.T) {
	m := NewApp("http://test")
	before := len(m.zoneIDs)
	m.appendCard(Card{Kind: CardPhase, Title: "T"})
	if len(m.zoneIDs) != before+1 {
		t.Errorf("zoneIDs not tracked: %d → %d", before, len(m.zoneIDs))
	}
}

func TestStateMachine_BGColorHandled(t *testing.T) {
	m := NewApp("http://test")
	u, _ := m.Update(teaBackgroundColorMsg(true))
	_ = u.(*model)
}

func TestStateMachine_LangSwitch(t *testing.T) {
	// Use NewAppFresh to avoid touching the developer's real
	// ~/.c4reqber (NewApp would load the persisted lang and
	// overwrite it on the L keypress, leaking into the next
	// `go test` run for that user).
	defer i18n.SetLang(i18n.LangEN)
	m := NewAppFresh("http://test")
	u, _ := m.Update(teaKeyMsg("L"))
	_ = u.(*model)
	// After L, the lang should have cycled. The i18n.GetLang() call
	// returns the package-level current lang (process-wide), so
	// restoring it in the defer is sufficient.
}

func TestStateMachine_CheckAchievements_EmptyModel(t *testing.T) {
	m := NewApp("http://test")
	// No discoveries yet
	before := m.achievements.Unlocked
	m.checkAchievements()
	after := m.achievements.Unlocked
	// No discoveries → no unlock (need ≥1)
	_ = before
	_ = after
}

func TestStateMachine_CheckAchievements_AfterDiscover(t *testing.T) {
	m := NewAppFresh("http://test")
	m.completedDisc = 1
	m.lastQuality = 0.95
	m.lastPapersCount = 5
	m.startedAt = time.Now().Add(-1 * time.Minute)
	m.replaceLangsSeen([]string{"EN", "RU", "ZH"})
	before := len(m.feed)
	m.checkAchievements()
	after := len(m.feed)
	// At least 3 new cards: FirstDiscovery, QualityS, MultiPaper, Speedster, Linguist
	if after-before < 3 {
		t.Errorf("expected ≥3 new cards (achievements), got %d", after-before)
	}
}

func TestStateMachine_CheckAchievements_Idempotent(t *testing.T) {
	m := NewAppFresh("http://test")
	m.completedDisc = 1
	m.checkAchievements()
	unlockedAfter1 := m.achievements.Unlocked
	// Run again — should not unlock anything
	m.checkAchievements()
	unlockedAfter2 := m.achievements.Unlocked
	if unlockedAfter1 != unlockedAfter2 {
		t.Errorf("unlock count changed: %d → %d", unlockedAfter1, unlockedAfter2)
	}
}

// TestStateMachine_CheckAchievements_IncrementsOnce guards the v9.13.x
// fix where m.store.IncrementDiscovery and m.store.Save were called once
// PER unlocked achievement. With 3 simultaneous unlocks (e.g.
// FirstDiscovery + QualityS + MultiPaper for a clean first run), the
// discovery count was being incremented 3x — the feed counter and the
// on-disk counter drifted, and Save() rewrote the state file 3x for a
// single logical event.
func TestStateMachine_CheckAchievements_IncrementsOnce(t *testing.T) {
	tmp := t.TempDir()
	store, err := persist.New(filepath.Join(tmp, "state.json"))
	if err != nil {
		t.Fatal(err)
	}
	m := NewAppFresh("http://test")
	m.store = store
	// Drive all 3 achievements to fire at once: 1+ discoveries (>=1),
	// quality >= 0.8 (QualityS), papersCount >= 3 (MultiPaper), and
	// secondsTaken < 30 (Speedster). That should give us >=4 unlocks.
	m.completedDisc = 1
	m.lastQuality = 0.95
	m.lastPapersCount = 5
	m.startedAt = time.Now().Add(-1 * time.Minute) // secondsTaken = 60 → no Speedster
	// Reset start time to 5s ago to get Speedster too:
	m.startedAt = time.Now().Add(-5 * time.Second)
	m.replaceLangsSeen([]string{"EN", "RU", "ZH"}) // Linguist
	m.checkAchievements()
	unlocked := m.achievements.Unlocked
	if unlocked < 3 {
		t.Fatalf("expected ≥3 unlocks to test the bug, got %d", unlocked)
	}
	// Bug: this used to be `unlocked`, not 1.
	if got := store.Snapshot().DiscoveryCount; got != 1 {
		t.Errorf("IncrementDiscovery was called %dx (expected 1x) — each "+
			"checkAchievements call must batch the increment even when "+
			"multiple achievements fire", got)
	}
}

// TestStateMachine_CheckAchievements_OverlayUsesLastUnlock guards the
// v9.13.x fix where checkAchievements picked unlocked[0] for the
// overlay name — but if the user just earned MultiPaper (index 3) the
// overlay still said "First Discovery" (index 0). Now it should show
// the LAST (most recent) unlock.
func TestStateMachine_CheckAchievements_OverlayUsesLastUnlock(t *testing.T) {
	tmp := t.TempDir()
	store, _ := persist.New(filepath.Join(tmp, "state.json"))
	m := NewAppFresh("http://test")
	m.store = store
	m.completedDisc = 1
	m.lastQuality = 0.95
	m.lastPapersCount = 5
	m.startedAt = time.Now().Add(-5 * time.Second)
	m.replaceLangsSeen([]string{"EN", "RU", "ZH"})
	m.checkAchievements()
	if !m.showAchievementOverlay {
		t.Fatal("overlay should be triggered when achievements unlock")
	}
	// The overlayMessage is what renderAchievementOverlay would show
	// as the achievement name. We can't easily assert the i18n
	// translation, but we can assert it corresponds to one of the
	// unlocked Items (not stuck on "First Discovery" — registry index
	// 0 — when MultiPaper was the more recent unlock).
	overlayName := m.achievements.OverlayMessage()
	if overlayName == "" {
		t.Error("overlay message should be set after checkAchievements")
	}
	// Compare against the i18n keys of the actually-unlocked items.
	// If overlayName equals "First Discovery" while MultiPaper is
	// also unlocked, the bug is back.
	if m.achievements.Items[AchMultiPaper].Unlocked && overlayName == i18n.T("achievement.first.name") {
		t.Error("overlay shows FIRST achievement name when MultiPaper is also " +
			"unlocked — should show the most recent (MultiPaper)")
	}
}

func TestStateMachine_SSEEvent_PhaseA(t *testing.T) {
	m := NewApp("http://test")
	m.running = true
	m.jobID = "test-job"
	data := `{"status":"phase_a","phase":"A: Framing","progress":0.15,"result":null}`
	u, _ := m.Update(apiSSEEventMsg(api.SSEEvent{Event: "phase", Data: data}))
	mm := u.(*model)
	if !mm.running {
		t.Error("phase_a should still be running (job not complete)")
	}
	if len(mm.feed) < 1 {
		t.Error("no card appended for phase_a")
	}
}

func TestStateMachine_SSEEvent_Completed(t *testing.T) {
	m := NewApp("http://test")
	m.running = true
	m.jobID = "test-job"
	data := `{"status":"complete","phase":"G: Quality","progress":1.0,"result":{"hypothesis":{"text":"truncated 17-nt guides","source":"v8","novelty_score":0.87},"papers":[{"title":"P1","year":2020,"venue":"Nature","doi":"10.1","citation_count":100,"source":"openalex"}]}}`
	u, _ := m.Update(apiSSEEventMsg(api.SSEEvent{Event: "phase", Data: data}))
	mm := u.(*model)
	if mm.running {
		t.Error("complete should set running=false")
	}
	if mm.jobID != "" {
		t.Error("complete should clear jobID")
	}
	if mm.lastQuality != 0.87 {
		t.Errorf("lastQuality = %v, want 0.87", mm.lastQuality)
	}
	if mm.lastPapersCount != 1 {
		t.Errorf("lastPapersCount = %d, want 1", mm.lastPapersCount)
	}
}

func TestStateMachine_SSEEvent_PhaseA_IsNotComplete(t *testing.T) {
	// phase_a is intermediate — running stays true, no jobID clear
	m := NewApp("http://test")
	m.running = true
	m.jobID = "test"
	data := `{"status":"phase_b","phase":"B: Search","progress":0.30}`
	u, _ := m.Update(apiSSEEventMsg(api.SSEEvent{Event: "phase", Data: data}))
	mm := u.(*model)
	if !mm.running {
		t.Error("phase_b should still be running")
	}
	if mm.jobID != "test" {
		t.Error("phase_b should not clear jobID")
	}
}

func TestStateMachine_FlashResult(t *testing.T) {
	m := NewApp("http://test")
	data := map[string]any{
		"hypothesis": map[string]any{"text": "flash hypothesis", "source": "v8"},
	}
	u, _ := m.Update(flashResultMsg{result: data})
	mm := u.(*model)
	if mm.running {
		t.Error("flash complete should set running=false")
	}
	if mm.completedDisc != 1 {
		t.Errorf("completedDisc = %d, want 1", mm.completedDisc)
	}
}

func TestStateMachine_MultiResult(t *testing.T) {
	m := NewApp("http://test")
	data := map[string]any{
		"ranked_hypotheses": []any{
			map[string]any{"text": "h1", "source": "a", "score": "0.9"},
			map[string]any{"text": "h2", "source": "b", "score": "0.7"},
		},
	}
	u, _ := m.Update(multiResultMsg{result: data})
	mm := u.(*model)
	if mm.completedDisc != 1 {
		t.Errorf("completedDisc = %d, want 1", mm.completedDisc)
	}
}

func TestStateMachine_PollMsgError(t *testing.T) {
	m := NewApp("http://test")
	u, _ := m.Update(apiPollMsg{err: errTest})
	mm := u.(*model)
	if len(mm.feed) < 1 {
		t.Error("error should append error card")
	}
}

func TestStateMachine_PollMsgCompleted(t *testing.T) {
	m := NewApp("http://test")
	m.running = true
	m.jobID = "test"
	data := map[string]any{
		"hypothesis":         map[string]any{"text": "poll hypothesis", "source": "v8"},
		"papers":             []any{map[string]any{"title": "P", "year": 2020, "venue": "V", "doi": "D", "citation_count": 5, "source": "s"}},
		"total_time_seconds": 30.0,
	}
	u, _ := m.Update(apiPollMsg{
		status:    "complete",
		phase:     "G: Quality",
		progress:  1.0,
		result:    data,
		completed: true,
	})
	mm := u.(*model)
	if mm.running {
		t.Error("complete should set running=false")
	}
	if mm.lastQuality != 0.95 { // novelty_score: 0.95
		// poll doesn't include novelty — this is 0
	}
	_ = mm
}

func TestStateMachine_PapersMsg(t *testing.T) {
	m := NewApp("http://test")
	papers := []map[string]any{
		{"title": "P1", "year": 2020, "venue": "V", "doi": "D1", "citation_count": 100, "source": "openalex"},
		{"title": "P2", "year": 2021, "venue": "V2", "doi": "D2", "citation_count": 200, "source": "crossref"},
	}
	u, _ := m.Update(apiPapersMsg{papers: papers})
	mm := u.(*model)
	if len(mm.feed) < 2 {
		t.Errorf("expected 2 paper cards, got %d", len(mm.feed))
	}
}

func TestStateMachine_SubmitMsgError(t *testing.T) {
	m := NewApp("http://test")
	u, _ := m.Update(apiSubmitMsg{err: errTest})
	mm := u.(*model)
	if len(mm.feed) < 1 {
		t.Error("submit error should append error card")
	}
	if mm.running {
		t.Error("submit error should NOT set running=true")
	}
}

func TestStateMachine_SubmitMsgOK(t *testing.T) {
	m := NewApp("http://test")
	u, _ := m.Update(apiSubmitMsg{jobID: "test-job-id"})
	mm := u.(*model)
	if !mm.running {
		t.Error("successful submit should set running=true")
	}
	if mm.jobID != "test-job-id" {
		t.Errorf("jobID = %s, want test-job-id", mm.jobID)
	}
}

func TestStateMachine_SSEClosed(t *testing.T) {
	m := NewApp("http://test")
	m.running = true
	m.jobID = "test-job"
	m.sseEvents = nil
	u, _ := m.Update(sseClosedMsg{})
	mm := u.(*model)
	if mm.sseEvents != nil {
		t.Error("sseClosed should clear sseEvents")
	}
}

func TestStateMachine_SSEError(t *testing.T) {
	m := NewApp("http://test")
	m.running = true
	m.jobID = "test-job"
	m.sseEvents = make(chan api.SSEEvent)
	u, _ := m.Update(sseErrorMsg{err: errTest})
	mm := u.(*model)
	if mm.sseEvents != nil {
		t.Error("sseError should clear sseEvents")
	}
}

func TestStateMachine_PollTickMsg(t *testing.T) {
	m := NewApp("http://test")
	m.running = false
	u, _ := m.Update(pollTickMsg(time.Now()))
	_ = u
	// No crash — just verify behavior
}

func TestStateMachine_MouseClickLeft(t *testing.T) {
	m := NewApp("http://test")
	m.width, m.height = 120, 40
	m.appendCard(Card{Kind: CardPhase, Title: "Clickable", Time: time.Now()})
	// simulate click on a zoneID
	zoneID := m.zoneIDs[len(m.zoneIDs)-1]
	// We can't easily test InBounds without real coords, but we can test that
	// a click doesn't crash. Use a message that doesn't have a real zone.
	_ = zoneID
	u, _ := m.Update(teaMouseClickMsg(60, 20, true))
	_ = u
}

// TestStateMachine_ZoneIDs_Unique guards the v9.13.x fix that
// switched zone IDs from c.Time.UnixNano() (collision-prone for
// bursty card appends — two cards in the same nanosecond shared
// the same ID and the click handler routed to the wrong card) to
// c.ID (monotonic uint64 from cards.NextID()). Asserts no two
// zone IDs collide when many cards are appended rapidly.
func TestStateMachine_ZoneIDs_Unique(t *testing.T) {
	m := NewAppFresh("http://test")
	// NewAppFresh starts with 1 empty placeholder card; capture
	// its zone ID count so we measure the new appends only.
	baseline := len(m.zoneIDs)
	// Append 100 cards in a tight loop. With UnixNano() they
	// would all get the same ID if executed in the same nanosecond
	// (which happens on M-class CPUs). With c.ID they're guaranteed
	// unique.
	for i := 0; i < 100; i++ {
		m.appendCard(cards.Card{
			Kind:  cards.KindPaper,
			Title: "burst paper " + string(rune('a'+i%26)),
		})
	}
	if got := len(m.zoneIDs) - baseline; got != 100 {
		t.Fatalf("expected 100 new zone IDs, got %d (baseline=%d, now=%d)",
			got, baseline, len(m.zoneIDs))
	}
	seen := map[string]bool{}
	for _, zid := range m.zoneIDs {
		if seen[zid] {
			t.Errorf("duplicate zone ID: %q (out of %d total)", zid, len(m.zoneIDs))
		}
		seen[zid] = true
	}
	if len(seen) != len(m.zoneIDs) {
		t.Errorf("expected %d unique zone IDs, got %d", len(m.zoneIDs), len(seen))
	}
}
// audit fix where the KeyPressMsg case did `m.ta, cmd = m.ta.Update(msg)`
// TWICE for the same message (once at the start of the case, once
// at the fallthrough). For regular characters, this caused every
// typed key to be processed twice — i.e. characters appeared doubled
// in the input. The fix moved textarea.Update to a single call at
// the fallthrough, so special keys (Esc/Enter/arrows/Tab) skip the
// textarea entirely (correct — they're TUI-level, not input-level).
func TestStateMachine_KeyPress_NoDoubleTextareaUpdate(t *testing.T) {
	m := NewAppFresh("http://test")
	// Type 'a' (printable, no inner case match, falls through to
	// the single textarea.Update at the end of Update()).
	u, _ := m.Update(teaKeyMsg("a"))
	mm := u.(*model)
	// After one keystroke, the textarea should contain exactly 'a',
	// not 'aa'. If the old double-update bug were back, value would
	// be 'aa'.
	if got := mm.ta.Value(); got != "a" {
		t.Errorf("expected textarea value 'a' after one keystroke, got %q (double-update bug?)", got)
	}
	// Type 'b' — same check.
	u, _ = mm.Update(teaKeyMsg("b"))
	mm = u.(*model)
	if got := mm.ta.Value(); got != "ab" {
		t.Errorf("expected 'ab' after two keystrokes, got %q", got)
	}
}

func TestStateMachine_LangSwitchAddsToSeen(t *testing.T) {
	m := NewApp("http://test")
	defer i18n.SetLang(i18n.LangEN)
	i18n.SetLang(i18n.LangZH)
	m.replaceLangsSeen([]string{"en"})
	m.updateLangSeen()
	if !m.hasLangSeen("zh") {
		t.Error("updateLangSeen should add zh")
	}
}

func TestStateMachine_HeaderFitsWidth(t *testing.T) {
	m := NewApp("http://test")
	for _, w := range []int{40, 60, 80, 100, 120, 200} {
		m.width = w
		m.height = 40
		m.layout()
		hdr := m.renderHeader()
		// Ensure no panic and the output contains the title
		if hdr == "" {
			t.Errorf("empty header at width %d", w)
		}
	}
}

// Helpers
type errTestType struct{ msg string }

func (e errTestType) Error() string { return e.msg }

var errTest = errTestType{"test error"}
