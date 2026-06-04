package widgets

import (
	"testing"
	"time"
)

func TestToast_ShowAndVisible(t *testing.T) {
	toast := NewToast()
	if toast.Visible() {
		t.Error("new toast should not be visible")
	}

	toast.Show("hello", "info")
	if !toast.Visible() {
		t.Error("toast should be visible after Show")
	}
	if toast.Message != "hello" {
		t.Errorf("expected message 'hello', got %q", toast.Message)
	}
	if toast.Kind != "info" {
		t.Errorf("expected kind 'info', got %q", toast.Kind)
	}
}

func TestToast_Expires(t *testing.T) {
	toast := NewToast()
	toast.Show("quick", "info")
	// Manually set expiry to the past
	toast.expiresAt = time.Now().Add(-1 * time.Second)
	if toast.Visible() {
		t.Error("toast should not be visible after expiry")
	}
}

func TestToast_View(t *testing.T) {
	toast := NewToast()
	if toast.View(80) != "" {
		t.Error("empty toast should render empty string")
	}

	toast.Show("test", "success")
	v := toast.View(80)
	if v == "" {
		t.Error("active toast should render non-empty string")
	}
}
