package internal

import "testing"

func TestInput_Sanitizes(t *testing.T) {
	cases := []struct {
		in, want string
	}{
		{"  hello world  ", "hello world"},
		{"<b>bold</b>", "bold"},
		{"hello\x00world", "helloworld"},
		{"hello\nworld", "hello\nworld"},
		{"hello\tworld", "hello\tworld"},
		{"café", "café"}, // NFKC stable
	}
	for _, c := range cases {
		got := Input(c.in)
		if got != c.want {
			t.Errorf("Input(%q) = %q, want %q", c.in, got, c.want)
		}
	}
}
