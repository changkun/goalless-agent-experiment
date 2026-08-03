// Command passgen generates memorable, cryptographically random passphrases.
package main

import (
	"flag"
	"fmt"
	"os"

	"passgen/internal/passgen"
)

func main() {
	words := flag.Int("words", 4, "number of words (1-12)")
	digits := flag.Int("digits", 2, "number of trailing digits (0-4)")
	sep := flag.String("sep", "-", "separator: one of - . ! _ ~")
	count := flag.Int("count", 1, "number of passphrases to print (1-20)")
	noCap := flag.Bool("no-cap", false, "do not capitalize words")
	flag.Usage = func() {
		fmt.Fprintf(os.Stderr, "Usage: %s [flags]\n\nGenerate memorable, secure passphrases.\n\n", os.Args[0])
		flag.PrintDefaults()
	}
	flag.Parse()

	if *words < 1 || *words > 12 {
		fmt.Fprintln(os.Stderr, "error: -words must be between 1 and 12")
		os.Exit(2)
	}
	if *digits < 0 || *digits > 4 {
		fmt.Fprintln(os.Stderr, "error: -digits must be between 0 and 4")
		os.Exit(2)
	}
	if *count < 1 || *count > 20 {
		fmt.Fprintln(os.Stderr, "error: -count must be between 1 and 20")
		os.Exit(2)
	}

	opts := passgen.Options{
		Words:      *words,
		Digits:     *digits,
		Separator:  *sep,
		Capitalize: !*noCap,
	}

	for i := 0; i < *count; i++ {
		p, err := passgen.Generate(opts)
		if err != nil {
			fmt.Fprintln(os.Stderr, "error:", err)
			os.Exit(1)
		}
		fmt.Println(p)
	}

	bits := passgen.EntropyBits(opts)
	fmt.Fprintf(os.Stderr, "# ~%.0f bits (%s)\n", bits, passgen.Strength(bits))
}
