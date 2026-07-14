package tui

import (
	"strings"
	"testing"
	"time"

	tea "charm.land/bubbletea/v2"
)

func TestDream_StartsInactive(t *testing.T) {
	d := NewDreamState()
	if d.Active() {
		t.Error("dream should start inactive")
	}
}

func TestDream_TouchKeepsInactive(t *testing.T) {
	d := NewDreamState()
	d.Touch()
	if d.Active() {
		t.Error("Touch should not activate dream")
	}
}

func TestDream_ActivatesAfterIdle(t *testing.T) {
	d := NewDreamState()
	d.idleSeconds = 0
	d.startedAt = time.Now().Add(-time.Hour)
	d.Tick()
	if !d.Active() {
		t.Error("dream should activate after idle seconds = 0")
	}
}

func TestDream_Tick_AdvancesArt(t *testing.T) {
	d := NewDreamState()
	d.idleSeconds = 0
	d.startedAt = time.Now().Add(-time.Hour)
	d.Tick()
	art1 := d.currentArt
	d.lastArtTick = time.Now().Add(-20 * time.Second)
	d.Tick()
	if d.currentArt == art1 {
		t.Error("expected art to rotate after 20s idle")
	}
}

func TestDream_ResetDisables(t *testing.T) {
	d := NewDreamState()
	d.idleSeconds = 0
	d.startedAt = time.Now().Add(-time.Hour)
	d.Tick()
	if !d.Active() {
		t.Fatal("dream should be active")
	}
	d.Reset()
	if d.Active() {
		t.Error("Reset should disable dream")
	}
}

func TestDream_TouchDisables(t *testing.T) {
	d := NewDreamState()
	d.idleSeconds = 0
	d.startedAt = time.Now().Add(-time.Hour)
	d.Tick()
	if !d.Active() {
		t.Fatal("dream should be active")
	}
	d.Touch()
	if d.Active() {
		t.Error("Touch should disable dream")
	}
}

func TestDream_RenderEmptyWhenInactive(t *testing.T) {
	d := NewDreamState()
	out := d.Render(120, 40)
	if out != "" {
		t.Error("Render should return empty when not active")
	}
}

func TestDream_RenderContainsTitleAndArtWhenActive(t *testing.T) {
	d := NewDreamState()
	d.idleSeconds = 0
	d.startedAt = time.Now().Add(-time.Hour)
	d.Tick()
	out := d.Render(120, 40)
	if !strings.Contains(out, "DREAM MODE") {
		t.Errorf("missing DREAM MODE title in:\n%s", out)
	}
}

func TestDream_RenderContainsIdleTime(t *testing.T) {
	d := NewDreamState()
	d.idleSeconds = 0
	d.startedAt = time.Now().Add(-30 * time.Second)
	d.Tick()
	out := d.Render(120, 40)
	if !strings.Contains(out, "0.5") && !strings.Contains(out, "30s") {
		t.Errorf("missing idle time in:\n%s", out)
	}
}

func TestDream_AppTouchesOnKeyPress(t *testing.T) {
	m := NewApp("http://test")
	if m.dream == nil {
		t.Fatal("dream should be wired in NewApp")
	}
	m.dream.ActivateForTest()
	if !m.dream.Active() {
		t.Fatal("dream should be active")
	}
	u, _ := m.Update(tea.KeyPressMsg{Code: 'a'})
	mm := u.(*model)
	if mm.dream.Active() {
		t.Error("dream should deactivate on key press")
	}
}

func TestDream_PauseResume(t *testing.T) {
	d := NewDreamState()
	if d.Paused() {
		t.Error("dream should not be paused initially")
	}
	d.Pause()
	if !d.Paused() {
		t.Error("Pause should set paused")
	}
	d.Resume()
	if d.Paused() {
		t.Error("Resume should clear paused")
	}
}

func TestDream_HasMultipleArts(t *testing.T) {
	if len(dreamArts) < 3 {
		t.Errorf("expected at least 3 dream arts, got %d", len(dreamArts))
	}
}

func TestDream_HasMultipleQuotes(t *testing.T) {
	if len(dreamQuotes) < 5 {
		t.Errorf("expected at least 5 dream quotes, got %d", len(dreamQuotes))
	}
}

func TestDream_QuoteRotation(t *testing.T) {
	q0 := QuoteForTest(0)
	q1 := QuoteForTest(1)
	if q0 == q1 {
		t.Error("expected different quotes for indices 0 and 1")
	}
}
