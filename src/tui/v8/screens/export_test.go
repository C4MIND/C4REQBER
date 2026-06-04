package screens

import (
	"strings"
	"testing"
	"time"
)

func TestBibTeXEscape(t *testing.T) {
	tests := []struct {
		input string
		want  string
	}{
		{"Simple Title", "Simple Title"},
		{"Title with $pecial chars", "Title with \\$pecial chars"},
		{"100% complete", "100\\% complete"},
		{"A & B", "A \\& B"},
		{"under_score", "under\\_score"},
		{"brace{test}", "brace\\{test\\}"},
		{"hash#tag", "hash\\#tag"},
		{"caret^2", "caret\\^{}2"},
		{"tilde~wave", "tilde\\~{}wave"},
		{"percent%sign", "percent\\%sign"},
	}

	for _, tt := range tests {
		t.Run(tt.input, func(t *testing.T) {
			got := bibTeXEscape(tt.input)
			if got != tt.want {
				t.Errorf("bibTeXEscape(%q) = %q, want %q", tt.input, got, tt.want)
			}
		})
	}
}

func TestExportPicker_Done(t *testing.T) {
	ep := NewExportPicker(nil)
	if ep.Done() {
		t.Error("new picker should not be done")
	}
}

func TestExportPicker_Title(t *testing.T) {
	ep := NewExportPicker(nil)
	if ep.Title() != "Export" {
		t.Errorf("expected title 'Export', got %q", ep.Title())
	}
}

func TestExportPicker_toBibTeX_EscapesSpecialChars(t *testing.T) {
	result := map[string]interface{}{
		"_papers_list": []interface{}{
			map[string]interface{}{
				"title":   "100% & {test}",
				"authors": []interface{}{"Doe, John$"},
				"year":    2024.0,
				"url":     "https://example.com/test",
			},
		},
	}
	ep := NewExportPicker(result)
	data, err := ep.toBibTeX(time.Now())
	if err != nil {
		t.Fatalf("toBibTeX error: %v", err)
	}
	out := string(data)
	if strings.Contains(out, "title = {100% & {test}}") {
		t.Error("BibTeX title was not escaped")
	}
	if !strings.Contains(out, `title = {100\% \& \{test\}}`) {
		t.Errorf("BibTeX title escape incorrect: %s", out)
	}
	if !strings.Contains(out, `author = {Doe, John\$}`) {
		t.Errorf("BibTeX author escape incorrect: %s", out)
	}
}

func TestExportPicker_toJSON(t *testing.T) {
	result := map[string]any{"key": "value"}
	ep := NewExportPicker(result)
	data, err := ep.toJSON()
	if err != nil {
		t.Fatalf("toJSON error: %v", err)
	}
	if !strings.Contains(string(data), `"key": "value"`) {
		t.Errorf("JSON output missing expected content: %s", string(data))
	}
}

func TestExportPicker_toHTML_Escapes(t *testing.T) {
	result := map[string]any{"title": "<script>alert(1)</script>"}
	ep := NewExportPicker(result)
	data, err := ep.toHTML(time.Now())
	if err != nil {
		t.Fatalf("toHTML error: %v", err)
	}
	if strings.Contains(string(data), "<script>") {
		t.Error("HTML output was not escaped")
	}
	if !strings.Contains(string(data), "&lt;script&gt;") {
		t.Errorf("HTML escape incorrect: %s", string(data))
	}
}
