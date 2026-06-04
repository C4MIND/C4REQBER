package backend

import (
	"context"
	"os"
	"testing"
	"time"
)

// integrationEnabled returns true if the backend is reachable.
func integrationEnabled() bool {
	return os.Getenv("C4_API_URL") != ""
}

func TestIntegrationOneClickAndPoll(t *testing.T) {
	if !integrationEnabled() {
		t.Skip("C4_API_URL not set, skipping integration test")
	}
	baseURL := os.Getenv("C4_API_URL")
	client := NewClient(baseURL)
	client.SetCredentials(
		os.Getenv("C4_API_KEY"),
		os.Getenv("C4_DEV_BYPASS"),
	)

	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	// Health check
	h, err := client.Health(ctx)
	if err != nil {
		t.Fatalf("health check failed: %v", err)
	}
	if h.Status != "healthy" {
		t.Fatalf("expected healthy, got %s", h.Status)
	}

	// One-click discovery
	resp, err := client.OneClick(ctx, OneClickRequest{Problem: "renewable energy storage", Domain: "engineering"})
	if err != nil {
		t.Fatalf("one-click failed: %v", err)
	}
	if resp.JobID == "" {
		t.Fatal("expected job_id, got empty")
	}
	if resp.Status != "queued" {
		t.Fatalf("expected queued, got %s", resp.Status)
	}

	// Poll status at least once
	status, err := client.JobStatus(ctx, resp.JobID)
	if err != nil {
		t.Fatalf("job status failed: %v", err)
	}
	if status.JobID != resp.JobID {
		t.Fatalf("job id mismatch: %s vs %s", status.JobID, resp.JobID)
	}
	if status.Progress < 0 || status.Progress > 1 {
		t.Fatalf("invalid progress: %f", status.Progress)
	}
}

func TestIntegrationC4Navigate(t *testing.T) {
	if !integrationEnabled() {
		t.Skip("C4_API_URL not set, skipping integration test")
	}
	baseURL := os.Getenv("C4_API_URL")
	client := NewClient(baseURL)
	client.SetCredentials(
		os.Getenv("C4_API_KEY"),
		os.Getenv("C4_DEV_BYPASS"),
	)

	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	resp, err := client.C4Navigate(ctx, C4NavigateRequest{Problem: "distributed consensus"})
	if err != nil {
		t.Fatalf("c4 navigate failed: %v", err)
	}
	if len(resp.Path) == 0 {
		t.Fatal("expected non-empty C4 path")
	}
	if resp.Problem != "distributed consensus" {
		t.Fatalf("problem mismatch: %s", resp.Problem)
	}
}

func TestIntegrationFlash(t *testing.T) {
	if !integrationEnabled() {
		t.Skip("C4_API_URL not set, skipping integration test")
	}
	baseURL := os.Getenv("C4_API_URL")
	client := NewClient(baseURL)
	client.SetCredentials(
		os.Getenv("C4_API_KEY"),
		os.Getenv("C4_DEV_BYPASS"),
	)

	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	resp, err := client.Flash(ctx, FlashRequest{Problem: "AI safety", Domain: "cs", Level: "simple"})
	if err != nil {
		t.Fatalf("flash failed: %v", err)
	}
	if resp.JobID == "" {
		t.Fatal("expected job_id, got empty")
	}
}
