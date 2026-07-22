// Package api wraps the c4reqber backend HTTP client for TUI v9.
// REST calls delegate to the OpenAPI-generated client in internal/oapi.
package api

import (
	"context"
	"fmt"
	"net/http"
	"net/http/cookiejar"
	"strings"
	"time"

	"github.com/figuramax/c4reqber-tui-v9/internal/oapi"
)

const defaultTimeout = 30 * time.Second

type Client struct {
	BaseURL string
	jar     *cookiejar.Jar
	csrf    string
	token   string
	http    *http.Client
	gen     *oapi.ClientWithResponses
}

func New(baseURL string) *Client {
	jar, _ := cookiejar.New(nil)
	// Audit 2026-06-22 H-6: custom Transport with ResponseHeaderTimeout prevents
	// the SSE goroutine from hanging indefinitely on half-closed connections
	// (where httpResp.Body.Read blocks returning (0, nil)). Without this,
	// repeated discovery launches under flaky WiFi accumulate zombie goroutines.
	httpClient := &http.Client{
		Timeout: defaultTimeout,
		Jar:     jar,
		Transport: &http.Transport{
			ResponseHeaderTimeout: 5 * time.Second,
			IdleConnTimeout:       90 * time.Second,
		},
	}
	c := &Client{
		BaseURL: baseURL,
		jar:     jar,
		http:    httpClient,
	}
	editor := func(ctx context.Context, req *http.Request) error {
		if req.Header.Get("Content-Type") == "" {
			req.Header.Set("Content-Type", "application/json")
		}
		if c.token != "" {
			req.Header.Set("Authorization", "Bearer "+c.token)
		}
		if c.csrf != "" {
			req.Header.Set("X-CSRF-Token", c.csrf)
		}
		return nil
	}
	gen, err := oapi.NewClientWithResponses(
		baseURL,
		oapi.WithHTTPClient(httpClient),
		oapi.WithRequestEditorFn(editor),
	)
	if err == nil {
		c.gen = gen
	}
	return c
}

func (c *Client) requireGen() (*oapi.ClientWithResponses, error) {
	if c.gen == nil {
		return nil, fmt.Errorf("openapi client not initialized")
	}
	return c.gen, nil
}

// Health checks connectivity and harvests the CSRF cookie.
func (c *Client) Health(ctx context.Context) error {
	gen, err := c.requireGen()
	if err != nil {
		return err
	}
	resp, err := gen.HealthCheckWithResponse(ctx)
	if err != nil {
		return err
	}
	if resp.HTTPResponse != nil {
		for _, ck := range resp.HTTPResponse.Cookies() {
			if ck.Name == "csrf_token" {
				c.csrf = ck.Value
			}
		}
	}
	if resp.StatusCode() >= 400 {
		return fmt.Errorf("health status %d", resp.StatusCode())
	}
	return nil
}

func (c *Client) CSRF() string  { return c.csrf }
func (c *Client) Token() string { return c.token }

// Register creates a new user (idempotent — server returns 200/409/422 if exists).
func (c *Client) Register(ctx context.Context, email, password, name string) error {
	gen, err := c.requireGen()
	if err != nil {
		return err
	}
	resp, err := gen.AuthRegisterWithResponse(ctx, oapi.RegisterRequest{
		Email:    email,
		Password: password,
		Name:     &name,
	})
	if err != nil {
		return err
	}
	code := resp.StatusCode()
	if code == 200 || code == 409 || code == 422 {
		return nil
	}
	return fmt.Errorf("register status %d", code)
}

// Login exchanges credentials for a JWT bearer token.
func (c *Client) Login(ctx context.Context, email, password string) error {
	gen, err := c.requireGen()
	if err != nil {
		return err
	}
	emptyName := ""
	resp, err := gen.AuthLoginWithResponse(ctx, oapi.LoginRequest{
		Email:    email,
		Password: password,
		Name:     &emptyName,
	})
	if err != nil {
		return err
	}
	if resp.StatusCode() >= 400 {
		return fmt.Errorf("login status %d: %s", resp.StatusCode(), string(resp.Body))
	}
	if resp.JSON200 != nil && resp.JSON200.AccessToken != nil {
		c.token = *resp.JSON200.AccessToken
	}
	return nil
}

// OneClick submits a one-click discovery job and returns its job_id.
func (c *Client) OneClick(ctx context.Context, problem, domain string) (string, error) {
	return c.OneClickWithTier(ctx, problem, domain, "", "human")
}

// OneClickWithTier sends a discovery request with explicit LLM tier (C1/C2/C3).
func (c *Client) OneClickWithTier(ctx context.Context, problem, domain, tier, outputMode string) (string, error) {
	gen, err := c.requireGen()
	if err != nil {
		return "", err
	}
	if domain == "" {
		domain = "science"
	}
	if outputMode == "" {
		outputMode = "human"
	}
	req := oapi.OneClickRequest{
		Problem: problem,
		Domain:  &domain,
	}
	if tier != "" {
		t := oapi.OneClickRequestLlmTier(tier)
		req.LlmTier = &t
	}
	mode := oapi.OneClickRequestOutputMode(outputMode)
	req.OutputMode = &mode

	resp, err := gen.DiscoverOneClickWithResponse(ctx, req)
	if err != nil {
		return "", err
	}
	if resp.StatusCode() >= 400 {
		return "", fmt.Errorf("one-click status %d", resp.StatusCode())
	}
	if resp.JSON200 == nil {
		return "", fmt.Errorf("one-click: empty response")
	}
	return resp.JSON200.JobId, nil
}

// JobStatus polls the job status endpoint.
func (c *Client) JobStatus(ctx context.Context, jobID string) (JobStatus, error) {
	gen, err := c.requireGen()
	if err != nil {
		return JobStatus{}, err
	}
	resp, err := gen.DiscoverJobStatusWithResponse(ctx, jobID)
	if err != nil {
		return JobStatus{}, err
	}
	if resp.StatusCode() >= 400 {
		return JobStatus{}, fmt.Errorf("job status %d", resp.StatusCode())
	}
	return jobStatusFromOAPI(resp.JSON200), nil
}

// FlashAndWait runs flash; if the API returns job_id, polls until complete.
// Returns an error after 3 consecutive JobStatus failures (transient
// errors are common and we tolerate them, but a sustained outage should
// not make us poll forever — the user's context is typically 60s for
// flash, so 3 failures × 2s = 6s of backoff plus the actual poll cadence
// stays well under the timeout).
func (c *Client) FlashAndWait(ctx context.Context, problem, domain string) (map[string]any, error) {
	raw, err := c.Flash(ctx, problem, domain)
	if err != nil {
		return nil, err
	}
	if raw == nil {
		return nil, nil
	}
	jobID, _ := raw["job_id"].(string)
	if jobID == "" {
		return raw, nil
	}
	ticker := time.NewTicker(2 * time.Second)
	defer ticker.Stop()
	const maxConsecutiveErrors = 3
	consecutiveErrors := 0
	for {
		select {
		case <-ctx.Done():
			return nil, ctx.Err()
		case <-ticker.C:
			js, err := c.JobStatus(ctx, jobID)
			if err != nil {
				consecutiveErrors++
				if consecutiveErrors >= maxConsecutiveErrors {
					return nil, fmt.Errorf("job %s: %d consecutive status failures: %w", jobID, consecutiveErrors, err)
				}
				continue
			}
			consecutiveErrors = 0
			if js.Completed {
				if js.Result != nil {
					// Propagate job-level status into result for celebration policy
					if _, ok := js.Result["status"]; !ok && js.Status != "" {
						js.Result["status"] = js.Status
					}
					return js.Result, nil
				}
				return map[string]any{"job_id": jobID, "status": js.Status}, nil
			}
		}
	}
}

// Flash submits /v8/discover/flash.
func (c *Client) Flash(ctx context.Context, problem, domain string) (map[string]any, error) {
	gen, err := c.requireGen()
	if err != nil {
		return nil, err
	}
	if domain == "" {
		domain = "science"
	}
	resp, err := gen.DiscoverFlashWithResponse(ctx, oapi.FlashRequest{
		Problem: problem,
		Domain:  &domain,
	})
	if err != nil {
		return nil, err
	}
	if resp.StatusCode() >= 400 {
		return nil, fmt.Errorf("flash status %d", resp.StatusCode())
	}
	return flexibleToMap(resp.JSON200), nil
}

// Multi submits /v8/discover/multi (sync, multi-hypothesis).
func (c *Client) Multi(ctx context.Context, problem, domain string, count int) (map[string]any, error) {
	gen, err := c.requireGen()
	if err != nil {
		return nil, err
	}
	if domain == "" {
		domain = "science"
	}
	if count <= 0 {
		count = 3
	}
	resp, err := gen.DiscoverMultiWithResponse(ctx, oapi.MultiRequest{
		Problem: problem,
		Domain:  &domain,
		Count:   &count,
	})
	if err != nil {
		return nil, err
	}
	if resp.StatusCode() >= 400 {
		return nil, fmt.Errorf("multi status %d", resp.StatusCode())
	}
	return flexibleToMap(resp.JSON200), nil
}

// KnowledgeSearch queries /v8/knowledge/search.
func (c *Client) KnowledgeSearch(ctx context.Context, query string, maxResults int) ([]map[string]any, error) {
	gen, err := c.requireGen()
	if err != nil {
		return nil, err
	}
	if maxResults <= 0 {
		maxResults = 3
	}
	resp, err := gen.KnowledgeSearchWithResponse(ctx, oapi.KnowledgeSearchRequest{
		Query:      query,
		MaxResults: &maxResults,
	})
	if err != nil {
		return nil, err
	}
	if resp.StatusCode() >= 400 {
		return nil, fmt.Errorf("knowledge search status %d", resp.StatusCode())
	}
	if resp.JSON200 == nil || resp.JSON200.Results == nil {
		return nil, nil
	}
	out := make([]map[string]any, 0, len(*resp.JSON200.Results))
	for _, item := range *resp.JSON200.Results {
		out = append(out, map[string]any(item))
	}
	return out, nil
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
func (c *Client) Stream(ctx context.Context, jobID string) (<-chan SSEEvent, func(), error) {
	gen, err := c.requireGen()
	if err != nil {
		return nil, nil, err
	}
	reqEditors := []oapi.RequestEditorFn{
		func(ctx context.Context, req *http.Request) error {
			req.Header.Set("Accept", "text/event-stream")
			return nil
		},
	}
	httpResp, err := gen.DiscoverJobStream(ctx, jobID, reqEditors...)
	if err != nil {
		return nil, nil, err
	}
	if httpResp.StatusCode >= 400 {
		httpResp.Body.Close()
		return nil, nil, fmt.Errorf("stream status %d", httpResp.StatusCode)
	}
	out := make(chan SSEEvent, 16)
	streamCtx, cancel := context.WithCancel(ctx)
	go func() {
		defer close(out)
		defer httpResp.Body.Close()
		buf := make([]byte, 4096)
		var pending string
		for {
			select {
			case <-streamCtx.Done():
				return
			default:
			}
			n, readErr := httpResp.Body.Read(buf)
			if n > 0 {
				pending += string(buf[:n])
				if len(pending) > maxSSEPendingBytes {
					return
				}
				for {
					idx := indexOfSSEBoundary(pending)
					if idx < 0 {
						break
					}
					event := parseSSEEvent(pending[:idx])
					pending = pending[idx+sseBoundaryWidth(pending[idx:]):]
					if event.Event != "" || event.Data != "" {
						select {
						case out <- event:
						case <-streamCtx.Done():
							return
						}
					}
				}
			}
			if readErr != nil {
				return
			}
		}
	}()
	return out, cancel, nil
}

func jobStatusFromOAPI(raw *oapi.JobStatusResponse) JobStatus {
	if raw == nil {
		return JobStatus{}
	}
	js := JobStatus{}
	if raw.Status != nil {
		js.Status = *raw.Status
	}
	if raw.Phase != nil {
		js.Phase = *raw.Phase
	}
	if raw.Progress != nil {
		js.Progress = float64(*raw.Progress)
	}
	if raw.Result != nil {
		js.Result = map[string]any(*raw.Result)
	}
	js.Completed = js.Status == "complete" || js.Status == "failed" || js.Status == "partial"
	return js
}

func flexibleToMap(raw *oapi.FlexibleObject) map[string]any {
	if raw == nil {
		return nil
	}
	return map[string]any(*raw)
}

const maxSSEPendingBytes = 1 << 20

func indexOfSSEBoundary(s string) int {
	lf := strings.Index(s, "\n\n")
	crlf := strings.Index(s, "\r\n\r\n")
	if lf < 0 {
		return crlf
	}
	if crlf >= 0 && crlf < lf {
		return crlf
	}
	return lf
}

func sseBoundaryWidth(s string) int {
	if strings.HasPrefix(s, "\r\n\r\n") {
		return 4
	}
	return 2
}

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
