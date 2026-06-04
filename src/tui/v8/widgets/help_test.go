package widgets

import "testing"

func TestHelp_Toggle(t *testing.T) {
	h := Help{}
	if h.Visible {
		t.Fatal("expected initially hidden")
	}
	h.Toggle()
	if !h.Visible {
		t.Fatal("expected visible after toggle")
	}
	h.Toggle()
	if h.Visible {
		t.Fatal("expected hidden after second toggle")
	}
}

func TestHelp_View(t *testing.T) {
	h := Help{Visible: true}
	v := h.View(60)
	if v == "" {
		t.Fatal("expected non-empty view")
	}
	h.Visible = false
	v2 := h.View(60)
	if v2 == "" {
		t.Fatal("expected non-empty minimized view")
	}
}
