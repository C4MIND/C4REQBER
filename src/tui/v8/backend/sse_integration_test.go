package backend

import (
	"bufio"
	"context"
	"net/http"
	"os"
	"strings"
	"testing"
	"time"
)

func TestIntegrationSSEStream(t *testing.T) {
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

	// Start a job
	resp, err := client.OneClick(ctx, OneClickRequest{Problem: "neural networks", Domain: "cs"})
	if err != nil {
		t.Fatalf("one-click failed: %v", err)
	}

	// Build SSE request manually (SSEClient has no timeout, but we add ctx timeout)
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, baseURL+"/v8/discover/stream/"+resp.JobID, nil)
	if err != nil {
		t.Fatalf("create request: %v", err)
	}
	client.setAuthHeaders(req)

	httpResp, err := client.SSEClient.Do(req)
	if err != nil {
		t.Fatalf("sse request failed: %v", err)
	}
	defer httpResp.Body.Close()

	if httpResp.StatusCode != 200 {
		t.Fatalf("expected 200, got %d", httpResp.StatusCode)
	}

	scanner := bufio.NewScanner(httpResp.Body)
	eventCount := 0
	timeout := time.AfterFunc(5*time.Second, func() {
		t.Log("SSE timeout reached")
	})
	defer timeout.Stop()

	for scanner.Scan() && eventCount < 3 {
		line := scanner.Text()
		if strings.HasPrefix(line, "event: ") || strings.HasPrefix(line, "data: ") {
			t.Logf("SSE: %s", line)
			eventCount++
		}
	}

	if eventCount == 0 {
		t.Fatal("expected at least one SSE event")
	}
	t.Logf("Received %d SSE events", eventCount)
}
