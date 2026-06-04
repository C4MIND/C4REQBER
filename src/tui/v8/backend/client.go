package backend

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/http/cookiejar"
	"strings"
	"sync"
	"time"
)

// Client talks to the Python FastAPI backend.
type Client struct {
	BaseURL        string
	HTTP           *http.Client
	SSEClient      *http.Client // no global timeout — SSE streams can idle for long periods
	APIKey         string
	DevBypassToken string
	csrfToken      string
	csrfMu         sync.Mutex
}

// NewClient creates a client pointing at the FastAPI server.
func NewClient(baseURL string) *Client {
	jar, _ := cookiejar.New(nil)
	return &Client{
		BaseURL:   strings.TrimSuffix(baseURL, "/"),
		HTTP:      &http.Client{Timeout: 30 * time.Second, Jar: jar},
		SSEClient: &http.Client{Timeout: 15 * time.Minute, Jar: jar}, // SSE streams can be long-running
	}
}

// SetCredentials configures API key and dev bypass token.
func (c *Client) SetCredentials(apiKey, devBypass string) {
	c.APIKey = apiKey
	c.DevBypassToken = devBypass
}

// ---------------------------------------------------------------------------
// Request / Response types
// ---------------------------------------------------------------------------

// HealthResponse mirrors the backend health check.
type HealthResponse struct {
	Status string `json:"status"`
}

// OneClickRequest starts a full discovery pipeline.
type OneClickRequest struct {
	Problem string `json:"problem"`
	Domain  string `json:"domain"`
	Turbo   bool   `json:"turbo,omitempty"`
}

// OneClickResponse is returned immediately; the job runs async.
type OneClickResponse struct {
	JobID  string `json:"job_id"`
	Status string `json:"status"`
}

// FlashRequest starts a lightweight discovery.
type FlashRequest struct {
	Problem string `json:"problem"`
	Domain  string `json:"domain"`
	Level   string `json:"level"`
}

// FlashResponse is returned immediately; the job runs async.
type FlashResponse struct {
	JobID  string `json:"job_id"`
	Status string `json:"status"`
}

// TurboRequest starts a turbo discovery.
type TurboRequest struct {
	Problem    string `json:"problem"`
	Domain     string `json:"domain"`
	Level      string `json:"level"`
	Vector     string `json:"vector"`
	AgentCount int    `json:"agent_count"`
}

// SearchRequest queries knowledge sources.
type SearchRequest struct {
	Query      string   `json:"query"`
	Sources    []string `json:"sources,omitempty"`
	MaxResults int      `json:"max_results"`
	SortBy     string   `json:"sort_by,omitempty"`
	Category   string   `json:"category,omitempty"`
}

// SearchResult represents a single paper/entry.
type SearchResult struct {
	Title    string   `json:"title"`
	Authors  []string `json:"authors"`
	Abstract string   `json:"abstract"`
	Year     int      `json:"year"`
	Source   string   `json:"source"`
	URL      string   `json:"url"`
}

// SearchResponse is the unified search result.
type SearchResponse struct {
	Results     []SearchResult `json:"results"`
	Total       int            `json:"total"`
	Query       string         `json:"query"`
	SourcesUsed []string       `json:"sources_used"`
}

// VerifyRequest runs formal verification.
type VerifyRequest struct {
	Code          string            `json:"code"`
	Specification map[string]string `json:"specification,omitempty"`
	FormalMethod  string            `json:"formal_method"`
	Proof         string            `json:"proof"`
}

// VerifyResponse is the verification result.
type VerifyResponse struct {
	VerifyID string   `json:"verify_id"`
	Verified bool     `json:"verified"`
	Errors   []string `json:"errors"`
	Method   string   `json:"method"`
}

// JobStatusResponse represents the current state of a pipeline job.
type JobStatusResponse struct {
	JobID       string         `json:"job_id"`
	JobType     string         `json:"job_type"`
	Status      string         `json:"status"`
	Phase       string         `json:"phase"`
	PhaseDetail string         `json:"phase_detail"`
	Progress    float64        `json:"progress"`
	Result      map[string]any `json:"result"`
	Errors      []string       `json:"errors"`
	CreatedAt   float64        `json:"created_at"`
	UpdatedAt   float64        `json:"updated_at"`
	CompletedAt float64        `json:"completed_at"`
}

// C4NavigateRequest asks the backend to compute a C4 path.
type C4NavigateRequest struct {
	Problem string `json:"problem"`
}

// C4NavigateResponse holds the computed path.
type C4NavigateResponse struct {
	Start           string   `json:"start"`
	End             string   `json:"end"`
	Path            []string `json:"path"`
	Steps           int      `json:"steps"`
	StatesVisited   int      `json:"states_visited"`
	Operators       []string `json:"operators"`
	HammingDistance int      `json:"hamming_distance"`
	Problem         string   `json:"problem"`
}

// ---------------------------------------------------------------------------
// Auth helpers
// ---------------------------------------------------------------------------

func (c *Client) setAuthHeaders(req *http.Request) {
	if c.APIKey != "" {
		req.Header.Set("X-API-Key", c.APIKey)
	}
	if c.DevBypassToken != "" {
		req.Header.Set("X-C4-DEV-BYPASS", c.DevBypassToken)
	}
}

func (c *Client) ensureCSRFCookie(ctx context.Context) error {
	c.csrfMu.Lock()
	defer c.csrfMu.Unlock()
	if c.csrfToken != "" {
		return nil
	}
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, c.BaseURL+"/api/v1/health", nil)
	if err != nil {
		return err
	}
	c.setAuthHeaders(req)
	resp, err := c.HTTP.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	_, _ = io.Copy(io.Discard, resp.Body)
	for _, cookie := range resp.Cookies() {
		if cookie.Name == "csrf_token" {
			c.csrfToken = cookie.Value
			return nil
		}
	}
	return nil // proceed without CSRF if cookie not present (some deployments skip CSRF)
}

// ---------------------------------------------------------------------------
// HTTP helpers
// ---------------------------------------------------------------------------

func (c *Client) postJSON(ctx context.Context, path string, payload any) (*http.Response, error) {
	return c.doPostJSON(ctx, path, payload, true)
}

func (c *Client) doPostJSON(ctx context.Context, path string, payload any, canRetry bool) (*http.Response, error) {
	if err := c.ensureCSRFCookie(ctx); err != nil {
		return nil, fmt.Errorf("csrf cookie: %w", err)
	}
	body, err := json.Marshal(payload)
	if err != nil {
		return nil, fmt.Errorf("marshal request: %w", err)
	}
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, c.BaseURL+path, bytes.NewReader(body))
	if err != nil {
		return nil, fmt.Errorf("create request: %w", err)
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Accept", "application/json")
	c.setAuthHeaders(req)
	c.csrfMu.Lock()
	if c.csrfToken != "" {
		req.Header.Set("X-CSRF-Token", c.csrfToken)
	}
	c.csrfMu.Unlock()
	resp, err := c.doWithRetry(req)
	if err != nil {
		return nil, fmt.Errorf("POST %s: %w", path, err)
	}
	if resp.StatusCode == 403 && canRetry {
		resp.Body.Close()
		c.csrfMu.Lock()
		c.csrfToken = ""
		c.csrfMu.Unlock()
		return c.doPostJSON(ctx, path, payload, false)
	}
	return resp, nil
}

func (c *Client) get(ctx context.Context, path string) (*http.Response, error) {
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, c.BaseURL+path, nil)
	if err != nil {
		return nil, fmt.Errorf("create request: %w", err)
	}
	c.setAuthHeaders(req)
	resp, err := c.doWithRetry(req)
	if err != nil {
		return nil, fmt.Errorf("GET %s: %w", path, err)
	}
	return resp, nil
}

// doWithRetry executes an HTTP request with up to 3 retries on transient failures.
// For POST/PUT requests the request body is preserved across retries by cloning the request.
func (c *Client) doWithRetry(req *http.Request) (*http.Response, error) {
	const maxBodySize = 10 * 1024 * 1024 // 10 MB
	var bodyBytes []byte
	if req.Body != nil {
		var err error
		bodyBytes, err = io.ReadAll(io.LimitReader(req.Body, maxBodySize))
		if err != nil {
			return nil, fmt.Errorf("read request body: %w", err)
		}
		req.Body.Close()
	}

	idempotent := req.Method == http.MethodGet || req.Method == http.MethodHead ||
		req.Method == http.MethodOptions || req.Method == http.MethodDelete ||
		req.Method == http.MethodTrace

	var resp *http.Response
	var err error
	for attempt := 0; attempt < 3; attempt++ {
		if attempt > 0 {
			backoff := time.Duration(attempt) * 500 * time.Millisecond
			select {
			case <-req.Context().Done():
				return nil, req.Context().Err()
			case <-time.After(backoff):
			}
		}
		if req.Context().Err() != nil {
			return nil, req.Context().Err()
		}
		// Clone request with a fresh body reader for each attempt
		r := req.Clone(req.Context())
		if bodyBytes != nil {
			r.Body = io.NopCloser(bytes.NewReader(bodyBytes))
			r.ContentLength = int64(len(bodyBytes))
		}
		resp, err = c.HTTP.Do(r)
		if err != nil {
			continue // retry on network errors
		}
		if resp.StatusCode == 408 || resp.StatusCode == 429 || resp.StatusCode >= 500 {
			if attempt == 2 || !idempotent {
				// final attempt or non-idempotent method — return response as-is
				return resp, nil
			}
			_, _ = io.Copy(io.Discard, resp.Body)
			resp.Body.Close()
			continue
		}
		return resp, nil
	}
	if err != nil {
		return nil, err
	}
	return resp, nil
}

func decodeJSON(resp *http.Response, dst any) error {
	if resp == nil {
		return fmt.Errorf("nil response")
	}
	defer resp.Body.Close()
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		body, err := io.ReadAll(io.LimitReader(resp.Body, 1<<20))
		if err != nil {
			return fmt.Errorf("%s returned %d", resp.Request.URL.Path, resp.StatusCode)
		}
		return fmt.Errorf("%s returned %d: %s", resp.Request.URL.Path, resp.StatusCode, string(body))
	}
	if err := json.NewDecoder(resp.Body).Decode(dst); err != nil {
		_, _ = io.Copy(io.Discard, resp.Body)
		return fmt.Errorf("decode response: %w", err)
	}
	return nil
}

// ---------------------------------------------------------------------------
// Endpoint methods
// ---------------------------------------------------------------------------

// Health pings the backend.
func (c *Client) Health(ctx context.Context) (*HealthResponse, error) {
	resp, err := c.get(ctx, "/api/v1/health")
	if err != nil {
		return nil, err
	}
	var h HealthResponse
	if err := decodeJSON(resp, &h); err != nil {
		return nil, err
	}
	return &h, nil
}

// OneClick starts a full discovery pipeline asynchronously.
func (c *Client) OneClick(ctx context.Context, req OneClickRequest) (*OneClickResponse, error) {
	resp, err := c.postJSON(ctx, "/v8/discover/one-click", req)
	if err != nil {
		return nil, err
	}
	var r OneClickResponse
	if err := decodeJSON(resp, &r); err != nil {
		return nil, err
	}
	return &r, nil
}

// Flash starts a lightweight discovery pipeline asynchronously.
func (c *Client) Flash(ctx context.Context, req FlashRequest) (*FlashResponse, error) {
	resp, err := c.postJSON(ctx, "/v8/discover/flash", req)
	if err != nil {
		return nil, err
	}
	var r FlashResponse
	if err := decodeJSON(resp, &r); err != nil {
		return nil, err
	}
	return &r, nil
}

// Search queries knowledge sources.
func (c *Client) Search(ctx context.Context, req SearchRequest) (*SearchResponse, error) {
	resp, err := c.postJSON(ctx, "/v8/knowledge/search", req)
	if err != nil {
		return nil, err
	}
	var r SearchResponse
	if err := decodeJSON(resp, &r); err != nil {
		return nil, err
	}
	return &r, nil
}

// Verify runs formal verification.
func (c *Client) Verify(ctx context.Context, req VerifyRequest) (*VerifyResponse, error) {
	resp, err := c.postJSON(ctx, "/v8/verification/verify", req)
	if err != nil {
		return nil, err
	}
	var r VerifyResponse
	if err := decodeJSON(resp, &r); err != nil {
		return nil, err
	}
	return &r, nil
}

// JobStatus polls the current state of a pipeline job.
func (c *Client) JobStatus(ctx context.Context, jobID string) (*JobStatusResponse, error) {
	resp, err := c.get(ctx, "/v8/discover/status/"+jobID)
	if err != nil {
		return nil, err
	}
	var r JobStatusResponse
	if err := decodeJSON(resp, &r); err != nil {
		return nil, err
	}
	return &r, nil
}

// C4Navigate asks the backend to compute a C4 cognitive path.
func (c *Client) C4Navigate(ctx context.Context, req C4NavigateRequest) (*C4NavigateResponse, error) {
	resp, err := c.postJSON(ctx, "/v8/discover/navigate-c4", req)
	if err != nil {
		return nil, err
	}
	var r C4NavigateResponse
	if err := decodeJSON(resp, &r); err != nil {
		return nil, err
	}
	return &r, nil
}
