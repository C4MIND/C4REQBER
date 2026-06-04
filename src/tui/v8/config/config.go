// Package config provides centralised layout and API configuration for TUI v8.
package config

import (
	"fmt"
	"net/url"
	"os"
	"strconv"
	"time"
)

// Config holds all TUI v8 configuration.
type Config struct {
	Layout LayoutConfig
	API    APIConfig
}

// LayoutConfig holds panel dimensions and tick intervals.
type LayoutConfig struct {
	HeaderHeight        int
	ChatCollapsedHeight int
	ChatExpandedHeight  int
	HelpHeight          int
	MascotHeight        int
	PipelineHeight      int
	ResultHeight        int
	TextAreaWidth       int
	TextAreaHeight      int
	MaxInputLen         int
}

// APIConfig holds backend connection settings.
type APIConfig struct {
	BaseURL        string
	Timeout        time.Duration
	RetryCount     int
	RetryBackoff   time.Duration
	PollInterval   time.Duration
	APIKey         string
	DevBypassToken string
}

// Default returns the default configuration.
func Default() Config {
	return Config{
		Layout: LayoutConfig{
			HeaderHeight:        1,
			ChatCollapsedHeight: 2,
			ChatExpandedHeight:  8,
			HelpHeight:          14,
			MascotHeight:        10,
			PipelineHeight:      16,
			ResultHeight:        20,
			TextAreaWidth:       60,
			TextAreaHeight:      3,
			MaxInputLen:         500,
		},
		API: APIConfig{
			BaseURL:        "http://localhost:8000",
			Timeout:        30 * time.Second,
			RetryCount:     3,
			RetryBackoff:   1 * time.Second,
			PollInterval:   500 * time.Millisecond,
			APIKey:         "",
			DevBypassToken: "",
		},
	}
}

// FromEnv overrides defaults with environment variables.
func FromEnv() Config {
	cfg := Default()

	if v := os.Getenv("C4_API_URL"); v != "" {
		cfg.API.BaseURL = v
	}
	if v := os.Getenv("C4_API_TIMEOUT"); v != "" {
		if d, err := time.ParseDuration(v); err == nil {
			cfg.API.Timeout = d
		}
	}
	if v := os.Getenv("C4_API_RETRY"); v != "" {
		if n, err := strconv.Atoi(v); err == nil {
			cfg.API.RetryCount = n
		}
	}
	if v := os.Getenv("C4_POLL_INTERVAL"); v != "" {
		if d, err := time.ParseDuration(v); err == nil {
			cfg.API.PollInterval = d
		}
	}
	if v := os.Getenv("C4_MAX_INPUT_LEN"); v != "" {
		if n, err := strconv.Atoi(v); err == nil {
			cfg.Layout.MaxInputLen = n
		}
	}
	if v := os.Getenv("C4_API_KEY"); v != "" {
		cfg.API.APIKey = v
	}
	if v := os.Getenv("C4_DEV_BYPASS"); v != "" {
		cfg.API.DevBypassToken = v
	}

	return cfg
}

// Validate checks configuration for sanity.
func (c Config) Validate() error {
	if c.API.BaseURL == "" {
		return fmt.Errorf("API base URL is required")
	}
	u, err := url.Parse(c.API.BaseURL)
	if err != nil || (u.Scheme != "http" && u.Scheme != "https") || u.Host == "" {
		return fmt.Errorf("API base URL must be a valid HTTP/HTTPS URL")
	}
	if c.API.Timeout < 1*time.Second {
		return fmt.Errorf("API timeout must be at least 1s")
	}
	if c.Layout.MaxInputLen < 10 {
		return fmt.Errorf("max input length must be at least 10")
	}
	return nil
}
