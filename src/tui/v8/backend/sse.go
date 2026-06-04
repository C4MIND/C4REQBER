package backend

import (
	"bufio"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"strings"
)

// SSEEvent represents a single Server-Sent Event.
type SSEEvent struct {
	Event string
	Data  string
}

// PhaseEvent is the JSON payload inside SSE data fields.
type PhaseEvent struct {
	Phase    string  `json:"phase"`
	Status   string  `json:"status"`
	Progress float64 `json:"progress"`
	Detail   string  `json:"detail"`
}

// ResultEvent is sent when a job completes.
type ResultEvent struct {
	Phase    string         `json:"phase"`
	Status   string         `json:"status"`
	Progress float64        `json:"progress"`
	Result   map[string]any `json:"result"`
	Errors   []string       `json:"errors"`
}

// SubscribeSSE opens an SSE stream for a job and returns a channel of events.
// The caller should read from the channel until it closes.
func (c *Client) SubscribeSSE(ctx context.Context, jobID string) (<-chan SSEEvent, <-chan error, error) {
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, c.BaseURL+"/v8/discover/stream/"+jobID, nil)
	if err != nil {
		return nil, nil, fmt.Errorf("create SSE request: %w", err)
	}
	req.Header.Set("Accept", "text/event-stream")
	req.Header.Set("Cache-Control", "no-cache")
	c.csrfMu.Lock()
	if c.csrfToken != "" {
		req.Header.Set("X-CSRF-Token", c.csrfToken)
	}
	c.csrfMu.Unlock()

	resp, err := c.SSEClient.Do(req)
	if err != nil {
		return nil, nil, fmt.Errorf("connect SSE: %w", err)
	}
	if resp.StatusCode != http.StatusOK {
		resp.Body.Close()
		return nil, nil, fmt.Errorf("SSE returned %d", resp.StatusCode)
	}

	const sseEventBuffer = 64
	events := make(chan SSEEvent, sseEventBuffer)
	errCh := make(chan error, 1)

	go func() {
		defer func() {
			if r := recover(); r != nil {
				select {
				case errCh <- fmt.Errorf("SSE goroutine panic: %v", r):
				default:
				}
			}
		}()
		defer close(events)
		defer close(errCh)
		defer resp.Body.Close()

		// Interrupt scanner when context is cancelled.
		// AfterFunc avoids leaking a goroutine if the stream finishes normally.
		stopCancel := context.AfterFunc(ctx, func() { resp.Body.Close() })
		defer stopCancel()

		scanner := bufio.NewScanner(resp.Body)
		// Increase scanner buffer to handle large SSE payloads (default is 64KB).
		const maxScanTokenSize = 512 * 1024 // 512KB
		buf := make([]byte, 0, 4096)
		scanner.Buffer(buf, maxScanTokenSize)
		var current SSEEvent

		for scanner.Scan() {
			select {
			case <-ctx.Done():
				select {
				case errCh <- ctx.Err():
				default:
				}
				return
			default:
			}

			line := scanner.Text()
			if line == "" {
				if current.Event != "" || current.Data != "" {
					select {
					case events <- current:
					case <-ctx.Done():
						select {
						case errCh <- ctx.Err():
						default:
						}
						return
					}
					current = SSEEvent{}
				}
				continue
			}
			if strings.HasPrefix(line, "event:") {
				current.Event = strings.TrimSpace(strings.TrimPrefix(line, "event:"))
			} else if strings.HasPrefix(line, "data:") {
				current.Data = strings.TrimSpace(strings.TrimPrefix(line, "data:"))
			}
		}

		if err := scanner.Err(); err != nil {
			select {
			case errCh <- err:
			default:
			}
		}
	}()

	return events, errCh, nil
}

// ParsePhaseEvent tries to parse SSE data as a PhaseEvent.
func ParsePhaseEvent(data string) (*PhaseEvent, error) {
	var p PhaseEvent
	if err := json.Unmarshal([]byte(data), &p); err != nil {
		return nil, err
	}
	if p.Phase == "" || p.Status == "" {
		return nil, fmt.Errorf("invalid PhaseEvent: missing phase or status")
	}
	return &p, nil
}

// ParseResultEvent tries to parse SSE data as a ResultEvent.
func ParseResultEvent(data string) (*ResultEvent, error) {
	var r ResultEvent
	if err := json.Unmarshal([]byte(data), &r); err != nil {
		return nil, err
	}
	if r.Phase == "" || r.Status == "" {
		return nil, fmt.Errorf("invalid ResultEvent: missing phase or status")
	}
	return &r, nil
}

// (SSEPollFallback removed — SSE streaming is the sole transport path)
