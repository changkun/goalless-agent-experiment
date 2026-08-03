// Package passgen provides cryptographically random, memorable passphrases
// built from a fixed wordlist, with a strength (entropy) estimator.
package passgen

import (
	"crypto/rand"
	"errors"
	"math"
	"math/big"
	"strings"
)

// Separators available for joining words together.
var Separators = []string{"-", ".", "!", "_", "~"}

// Options controls how a passphrase is generated.
type Options struct {
	// Words is the number of words to include.
	Words int
	// Digits is the number of random digits to append (0-4).
	Digits int
	// Separator used between words.
	Separator string
	// Capitalize makes each word start with an uppercase letter.
	Capitalize bool
}

// DefaultOptions returns a sane baseline (4 words, 2 digits, hyphen-separated).
func DefaultOptions() Options {
	return Options{Words: 4, Digits: 2, Separator: "-", Capitalize: true}
}

// Generate builds a passphrase from the given options using the OS CSPRNG.
func Generate(opts Options) (string, error) {
	if opts.Words < 1 {
		return "", errors.New("passgen: Words must be at least 1")
	}
	if opts.Digits < 0 || opts.Digits > 4 {
		return "", errors.New("passgen: Digits must be between 0 and 4")
	}
	if !validSeparator(opts.Separator) {
		return "", errors.New("passgen: unknown separator")
	}

	selected := make([]string, 0, opts.Words)
	for i := 0; i < opts.Words; i++ {
		idx, err := randInt(WordlistSize)
		if err != nil {
			return "", err
		}
		w := words[idx]
		if opts.Capitalize {
			w = strings.ToUpper(w[:1]) + w[1:]
		}
		selected = append(selected, w)
	}

	full := strings.Join(selected, opts.Separator)

	if opts.Digits > 0 {
		for i := 0; i < opts.Digits; i++ {
			d, err := randInt(10)
			if err != nil {
				return "", err
			}
			full += string(rune('0' + d))
		}
	}

	return full, nil
}

// EntropyBits estimates the passphrase entropy in bits for the given options.
// It counts word selections, the separator, digit order, capitalization, and
// the appended digits.
func EntropyBits(opts Options) float64 {
	if opts.Words < 1 {
		return 0
	}
	bits := float64(opts.Words) * log2(float64(WordlistSize))

	// Choice of separator adds log2(len) if more than one is available.
	if len(Separators) > 1 {
		bits += log2(float64(len(Separators)))
	}
	if opts.Capitalize {
		// Each first letter could have been capitalized or not.
		bits += float64(opts.Words)
	}
	if opts.Digits > 0 {
		// Digits add 10^opts.Digits combinations.
		bits += log2(pow10(opts.Digits))
	}
	return bits
}

// Strength returns a human label for a number of bits.
func Strength(bits float64) string {
	switch {
	case bits < 40:
		return "weak"
	case bits < 60:
		return "fair"
	case bits < 80:
		return "strong"
	default:
		return "very strong"
	}
}

// randInt returns a uniform integer in [0, n) using crypto/rand.
func randInt(n int) (int, error) {
	if n <= 0 {
		return 0, errors.New("passgen: n must be positive")
	}
	bi, err := rand.Int(rand.Reader, big.NewInt(int64(n)))
	if err != nil {
		return 0, err
	}
	return int(bi.Int64()), nil
}

func validSeparator(s string) bool {
	for _, sep := range Separators {
		if s == sep {
			return true
		}
	}
	return false
}

// log2 is a small convenience wrapper over math.Log2.
func log2(x float64) float64 {
	return math.Log2(x)
}

func pow10(n int) float64 {
	r := 1.0
	for i := 0; i < n; i++ {
		r *= 10
	}
	return r
}
