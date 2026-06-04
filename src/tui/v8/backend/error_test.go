package backend

import (
	"context"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"
)

func TestClient_NoCredentials(t *testing.T) {
	ts := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusUnauthorized)
		w.Write([]byte(`{"detail":"API key required"}`))
	}))
	defer ts.Close()

	client := NewClient(ts.URL)
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	_, err := client.Health(ctx)
	if err == nil {
		t.Fatal("expected error without API key")
	}
	if !contains(err.Error(), "401") {
		t.Fatalf("expected 401, got: %v", err)
	}
}

func TestClient_WithCredentials(t *testing.T) {
	ts := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Header.Get("X-API-Key") != "test-key" {
			w.WriteHeader(http.StatusUnauthorized)
			return
		}
		if r.Header.Get("X-C4-DEV-BYPASS") != "bypass-token" {
			w.WriteHeader(http.StatusForbidden)
			return
		}
		w.Write([]byte(`{"status":"healthy"}`))
	}))
	defer ts.Close()

	client := NewClient(ts.URL)
	client.SetCredentials("test-key", "bypass-token")
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	h, err := client.Health(ctx)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if h.Status != "healthy" {
		t.Fatalf("expected healthy, got %s", h.Status)
	}
}

func TestClient_ConnectionRefused(t *testing.T) {
	client := NewClient("http://localhost:59999")
	client.SetCredentials("test", "test")
	ctx, cancel := context.WithTimeout(context.Background(), 1*time.Second)
	defer cancel()

	_, err := client.Health(ctx)
	if err == nil {
		t.Fatal("expected connection error")
	}
}

func contains(s, substr string) bool {
	return len(s) >= len(substr) && (s == substr || len(s) > 0 && containsHelper(s, substr))
}

func containsHelper(s, substr string) bool {
	for i := 0; i <= len(s)-len(substr); i++ {
		if s[i:i+len(substr)] == substr {
			return true
		}
	}
	return false
}
