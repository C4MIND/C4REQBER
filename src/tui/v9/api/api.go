// Package api wraps the c4reqber backend HTTP client for TUI v9.
package api

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/cookiejar"
	"net/url"
	"strings"
	"time"
)

const (
	defaultTimeout = 30 * time.Second
)

type Client struct {
	BaseURL string
	jar     *cookiejar.Jar
	csrf    string
	token   string
	http    *http.Client
}

func New(baseURL string) *Client {
	jar, _ := cookiejar.New(nil)
	return &Client{
		BaseURL: baseURL,
		jar:     jar,
		http:    &http.Client{Timeout: defaultTimeout, Jar: jar},
	}
}

// Health checks connectivity and harvests the CSRF cookie.
func (c *Client) Health(ctx context.Context) error {
	req, _ := http.NewRequestWithContext(ctx, "GET", c.BaseURL+"/api/v1/health", nil)
	resp, err := c.http.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	for _, ck := range resp.Cookies() {
		if ck.Name == "csrf_token" {
			c.csrf = ck.Value
		}
	}
	return nil
}

// CSRF returns the current CSRF token (after Health/Auth).
func (c *Client) CSRF() string { return c.csrf }

// Token returns the current JWT bearer token.
func (c *Client) Token() string { return c.token }

// Register creates a new user (idempotent — server returns 200/409/422 if exists).
func (c *Client) Register(ctx context.Context, email, password, name string) error {
	body := fmt.Sprintf(`{"email":%q,"password":%q,"name":%q}`, email, password, name)
	req, _ := http.NewRequestWithContext(ctx, "POST", c.BaseURL+"/api/v1/auth/register", strings.NewReader(body))
	c.addCommonHeaders(req)
	resp, err := c.http.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	// 200 = created, 409/422 = already exists, anything else = error
	if resp.StatusCode == 200 || resp.StatusCode == 409 || resp.StatusCode == 422 {
		return nil
	}
	return fmt.Errorf("register status %d", resp.StatusCode)
}

// Login exchanges credentials for a JWT bearer token.
func (c *Client) Login(ctx context.Context, email, password string) error {
	body := fmt.Sprintf(`{"email":%q,"password":%q,"name":""}`, email, password)
	req, _ := http.NewRequestWithContext(ctx, "POST", c.BaseURL+"/api/v1/auth/login", strings.NewReader(body))
	c.addCommonHeaders(req)
	resp, err := c.http.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode >= 400 {
		// Read response body for diagnostics
		buf := make([]byte, 1024)
		n, _ := resp.Body.Read(buf)
		return fmt.Errorf("login status %d: %s", resp.StatusCode, string(buf[:n]))
	}
	var out struct {
		AccessToken string `json:"access_token"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&out); err != nil {
		return err
	}
	c.token = out.AccessToken
	return nil
}

// OneClick submits a one-click discovery job and returns its job_id.
func (c *Client) OneClick(ctx context.Context, problem, domain string) (string, error) {
	if domain == "" {
		domain = "science"
	}
	body := fmt.Sprintf(`{"problem":%q,"domain":%q}`, problem, domain)
	req, _ := http.NewRequestWithContext(ctx, "POST", c.BaseURL+"/v8/discover/one-click", strings.NewReader(body))
	c.addCommonHeaders(req)
	resp, err := c.http.Do(req)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()
	if resp.StatusCode >= 400 {
		return "", fmt.Errorf("one-click status %d", resp.StatusCode)
	}
	var out struct {
		JobID string `json:"job_id"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&out); err != nil {
		return "", err
	}
	return out.JobID, nil
}

// JobStatus polls the job status endpoint.
func (c *Client) JobStatus(ctx context.Context, jobID string) (JobStatus, error) {
	u := c.BaseURL + "/v8/discover/status/" + url.PathEscape(jobID)
	req, _ := http.NewRequestWithContext(ctx, "GET", u, nil)
	c.addCommonHeaders(req)
	resp, err := c.http.Do(req)
	if err != nil {
		return JobStatus{}, err
	}
	defer resp.Body.Close()
	if resp.StatusCode >= 400 {
		return JobStatus{}, fmt.Errorf("job status %d", resp.StatusCode)
	}
	var raw map[string]any
	if err := json.NewDecoder(resp.Body).Decode(&raw); err != nil {
		return JobStatus{}, err
	}
	js := JobStatus{
		Status:   fieldString(raw, "status"),
		Phase:    fieldString(raw, "phase"),
		Progress: fieldFloat(raw, "progress"),
	}
	if res, ok := raw["result"].(map[string]any); ok {
		js.Result = res
	}
	js.Completed = js.Status == "complete" || js.Status == "failed" || js.Status == "partial"
	return js, nil
}

// Flash submits /v8/discover/flash (sync, lightweight).
func (c *Client) Flash(ctx context.Context, problem, domain string) (map[string]any, error) {
	if domain == "" {
		domain = "science"
	}
	body := fmt.Sprintf(`{"problem":%q,"domain":%q}`, problem, domain)
	req, _ := http.NewRequestWithContext(ctx, "POST", c.BaseURL+"/v8/discover/flash", strings.NewReader(body))
	c.addCommonHeaders(req)
	resp, err := c.http.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	if resp.StatusCode >= 400 {
		return nil, fmt.Errorf("flash status %d", resp.StatusCode)
	}
	var out map[string]any
	if err := json.NewDecoder(resp.Body).Decode(&out); err != nil {
		return nil, err
	}
	return out, nil
}

// Multi submits /v8/discover/multi (sync, multi-hypothesis).
func (c *Client) Multi(ctx context.Context, problem, domain string, count int) (map[string]any, error) {
	if domain == "" {
		domain = "science"
	}
	if count <= 0 {
		count = 3
	}
	body := fmt.Sprintf(`{"problem":%q,"domain":%q,"count":%d}`, problem, domain, count)
	req, _ := http.NewRequestWithContext(ctx, "POST", c.BaseURL+"/v8/discover/multi", strings.NewReader(body))
	c.addCommonHeaders(req)
	resp, err := c.http.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	if resp.StatusCode >= 400 {
		return nil, fmt.Errorf("multi status %d", resp.StatusCode)
	}
	var out map[string]any
	if err := json.NewDecoder(resp.Body).Decode(&out); err != nil {
		return nil, err
	}
	return out, nil
}

// KnowledgeSearch queries /v8/knowledge/search.
func (c *Client) KnowledgeSearch(ctx context.Context, query string, maxResults int) ([]map[string]any, error) {
	if maxResults <= 0 {
		maxResults = 3
	}
	body := fmt.Sprintf(`{"query":%q,"max_results":%d}`, query, maxResults)
	req, _ := http.NewRequestWithContext(ctx, "POST", c.BaseURL+"/v8/knowledge/search", strings.NewReader(body))
	c.addCommonHeaders(req)
	resp, err := c.http.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	if resp.StatusCode >= 400 {
		return nil, fmt.Errorf("knowledge search status %d", resp.StatusCode)
	}
	var raw struct {
		Results []map[string]any `json:"results"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&raw); err != nil {
		return nil, err
	}
	return raw.Results, nil
}

// JobStatus describes a one-click job's current state.
type JobStatus struct {
	Status    string
	Phase     string
	Progress  float64
	Result    map[string]any
	Completed bool
}

// SSEEvent is one Server-Sent Event from /v8/discover/stream/{job_id}.
type SSEEvent struct {
	Event string
	Data  string
}

// Stream opens an SSE connection and returns a channel of events + an error.
// The channel is closed when the server closes the connection or on error.
// Caller MUST drain the channel and call the cancel func to release resources.
func (c *Client) Stream(ctx context.Context, jobID string) (<-chan SSEEvent, func(), error) {
	u := c.BaseURL + "/v8/discover/stream/" + url.PathEscape(jobID)
	req, _ := http.NewRequestWithContext(ctx, "GET", u, nil)
	req.Header.Set("Accept", "text/event-stream")
	if c.token != "" {
		req.Header.Set("Authorization", "Bearer "+c.token)
	}
	if c.csrf != "" {
		req.Header.Set("X-CSRF-Token", c.csrf)
	}
	resp, err := c.http.Do(req)
	if err != nil {
		return nil, nil, err
	}
	if resp.StatusCode >= 400 {
		resp.Body.Close()
		return nil, nil, fmt.Errorf("stream status %d", resp.StatusCode)
	}
	out := make(chan SSEEvent, 16)
	streamCtx, cancel := context.WithCancel(ctx)
	go func() {
		defer close(out)
		defer resp.Body.Close()
		buf := make([]byte, 4096)
		var pending string
		for {
			select {
			case <-streamCtx.Done():
				return
			default:
			}
			n, err := resp.Body.Read(buf)
			if n > 0 {
				pending += string(buf[:n])
				for {
					idx := indexOfSSEBoundary(pending)
					if idx < 0 {
						break
					}
					event := parseSSEEvent(pending[:idx])
					pending = pending[idx+2:]
					if event.Event != "" || event.Data != "" {
						select {
						case out <- event:
						case <-streamCtx.Done():
							return
						}
					}
				}
			}
			if err != nil {
				return
			}
		}
	}()
	return out, cancel, nil
}

// indexOfSSEBoundary finds "\n\n" in s. Returns -1 if not found.
func indexOfSSEBoundary(s string) int {
	for i := 0; i < len(s)-1; i++ {
		if s[i] == '\n' && s[i+1] == '\n' {
			return i
		}
	}
	return -1
}

// parseSSEEvent parses a single SSE event block.
// Format:
// event: phase\n
// data: {"status":"phase_b"}\n
// \n
// Multi-line data is concatenated with '\n' (SSE spec).
func parseSSEEvent(block string) SSEEvent {
	out := SSEEvent{}
	var dataLines []string
	for _, line := range strings.Split(block, "\n") {
		switch {
		case strings.HasPrefix(line, "event:"):
			out.Event = strings.TrimSpace(line[len("event:"):])
		case strings.HasPrefix(line, "data:"):
			dataLines = append(dataLines, strings.TrimSpace(line[len("data:"):]))
		}
	}
	if len(dataLines) > 0 {
		out.Data = strings.Join(dataLines, "\n")
	}
	return out
}

func (c *Client) addCommonHeaders(req *http.Request) {
	req.Header.Set("Content-Type", "application/json")
	if c.token != "" {
		req.Header.Set("Authorization", "Bearer "+c.token)
	}
	if c.csrf != "" {
		req.Header.Set("X-CSRF-Token", c.csrf)
	}
}

// fieldString safely extracts a string field from a generic map.
func fieldString(m map[string]any, key string) string {
	if m == nil {
		return ""
	}
	v, ok := m[key]
	if !ok || v == nil {
		return ""
	}
	if s, ok := v.(string); ok {
		return s
	}
	return fmt.Sprintf("%v", v)
}

// fieldFloat safely extracts a float field from a generic map.
func fieldFloat(m map[string]any, key string) float64 {
	if m == nil {
		return 0
	}
	if v, ok := m[key].(float64); ok {
		return v
	}
	return 0
}
