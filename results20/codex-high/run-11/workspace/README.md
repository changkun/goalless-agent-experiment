# passgen

A tiny, dependency-free Go CLI that generates **memorable, secure passphrases**.

## Install / run

```sh
go run ./cmd/passgen
go build -o passgen ./cmd/passgen
```

## Examples

```sh
passgen
# -> Green-Banjo-Canyon!43     (~45 bits, fair)

passgen -words 6 -sep . -digits 0
passgen -count 5 -no-cap
```

## Flags

| Flag    | Default | Meaning                            |
|---------|---------|------------------------------------|
| `-words`| `4`     | Number of words (1-12)             |
| `-digits`| `2`    | Trailing digits (0-4)              |
| `-sep`  | `-`     | Separator: `- . ! _ ~`             |
| `-count`| `1`     | Passphrases to print (1-20)        |
| `-no-cap`| `false`| Don't capitalize each word        |

Entropy is estimated from wordlist size, separator choice, capitalization, and digits.
Source of randomness is `crypto/rand`.

## Test

```sh
go test ./...
```
