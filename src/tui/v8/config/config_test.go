package config

import (
	"os"
	"testing"
	"time"
)

func TestDefault(t *testing.T) {
	cfg := Default()
	if cfg.API.BaseURL != "http://localhost:8000" {
		t.Fatalf("expected default base URL, got %s", cfg.API.BaseURL)
	}
	if cfg.API.Timeout != 30*time.Second {
		t.Fatalf("expected default timeout 30s, got %v", cfg.API.Timeout)
	}
	if cfg.Layout.MaxInputLen != 500 {
		t.Fatalf("expected default max input 500, got %d", cfg.Layout.MaxInputLen)
	}
}

func TestFromEnv(t *testing.T) {
	os.Setenv("C4_API_URL", "http://test:9000")
	os.Setenv("C4_API_TIMEOUT", "10s")
	os.Setenv("C4_MAX_INPUT_LEN", "1000")
	defer os.Unsetenv("C4_API_URL")
	defer os.Unsetenv("C4_API_TIMEOUT")
	defer os.Unsetenv("C4_MAX_INPUT_LEN")

	cfg := FromEnv()
	if cfg.API.BaseURL != "http://test:9000" {
		t.Fatalf("expected env base URL, got %s", cfg.API.BaseURL)
	}
	if cfg.API.Timeout != 10*time.Second {
		t.Fatalf("expected env timeout 10s, got %v", cfg.API.Timeout)
	}
	if cfg.Layout.MaxInputLen != 1000 {
		t.Fatalf("expected env max input 1000, got %d", cfg.Layout.MaxInputLen)
	}
}

func TestValidate(t *testing.T) {
	cfg := Default()
	if err := cfg.Validate(); err != nil {
		t.Fatalf("expected valid config, got %v", err)
	}

	cfg.API.BaseURL = ""
	if err := cfg.Validate(); err == nil {
		t.Fatal("expected error for empty base URL")
	}

	cfg.API.BaseURL = "http://test"
	cfg.API.Timeout = 0
	if err := cfg.Validate(); err == nil {
		t.Fatal("expected error for zero timeout")
	}

	cfg.API.Timeout = 30 * time.Second
	cfg.Layout.MaxInputLen = 5
	if err := cfg.Validate(); err == nil {
		t.Fatal("expected error for small max input")
	}
}
