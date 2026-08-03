package passgen

import (
	"strings"
	"testing"
)

func TestGenerateShape(t *testing.T) {
	opts := DefaultOptions()
	p, err := Generate(opts)
	if err != nil {
		t.Fatal(err)
	}
	parts := strings.Split(p, opts.Separator)
	if len(parts) != opts.Words {
		t.Fatalf("expected %d words, got %d: %q", opts.Words, len(parts), p)
	}
	if !strings.HasSuffix(p, string(rune('0'+opts.Digits))) && !isDigitRune(p[len(p)-1]) {
		t.Fatalf("expected digits at end, got %q", p)
	}
	if opts.Capitalize && !isUpper(parts[0][0]) {
		t.Fatalf("expected capitalized word, got %q", p)
	}
}

func TestGenerateInvalidOptions(t *testing.T) {
	if _, err := Generate(Options{Words: 0}); err == nil {
		t.Error("expected error for Words=0")
	}
	if _, err := Generate(Options{Words: 2, Digits: 5}); err == nil {
		t.Error("expected error for Digits=5")
	}
	if _, err := Generate(Options{Words: 2, Separator: "?"}); err == nil {
		t.Error("expected error for bad separator")
	}
}

func TestWordlistUniqueness(t *testing.T) {
	seen := make(map[string]bool, len(words))
	for _, w := range words {
		if w == "" {
			t.Fatal("empty word in list")
		}
		if seen[w] {
			t.Fatalf("duplicate word %q", w)
		}
		seen[w] = true
	}
	if WordlistSize != len(words) {
		t.Fatalf("WordlistSize mismatch: %d != %d", WordlistSize, len(words))
	}
}

func TestEntropyBitsAndStrength(t *testing.T) {
	opts := DefaultOptions()
	bits := EntropyBits(opts)
	// 4 words from a big list should be comfortably above 40 bits.
	if bits < 40 {
		t.Fatalf("expected strong entropy, got %.1f", bits)
	}
	if Strength(30) != "weak" || Strength(50) != "fair" || Strength(70) != "strong" || Strength(100) != "very strong" {
		t.Fatal("Strength labels incorrect")
	}
}

func TestGenerateVariety(t *testing.T) {
	opts := DefaultOptions()
	seen := make(map[string]bool, WordlistSize)
	// Generate enough samples to collect many distinct words without flakiness.
	for i := 0; i < 200; i++ {
		p, err := Generate(opts)
		if err != nil {
			t.Fatal(err)
		}
		for _, part := range strings.Split(p, opts.Separator) {
			w := strings.ToLower(part)
			seen[w] = true
		}
	}
	if len(seen) < 50 {
		t.Fatalf("expected varied words, only saw %d distinct", len(seen))
	}
}

func isUpper(b byte) bool { return b >= 'A' && b <= 'Z' }
func isDigitRune(b byte) bool {
	return b >= '0' && b <= '9'
}
