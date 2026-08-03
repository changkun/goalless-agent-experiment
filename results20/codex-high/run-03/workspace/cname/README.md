# cname

Generate memorable, human-friendly codenames for projects, releases, environments, branches, and containers — no dependencies, no network.

## Install / run

```sh
node bin/cname.js --help
# or link it globally:
npm link
cname --help
```

## Usage

```sh
# default: amber-giraffe-17 style
cname

# several at once
cname -n 5

# different formats
cname -f camel    # amberOcelot42
cname -f snake    # amber_ocelot_42
cname -f kebab    # amber-ocelot-42
cname -f title    # Amber Ocelot 42
cname -f plain    # amber ocelot 42

# no numeric suffix
cname --no-number

# deterministic output from a seed
cname -s release-1 -n 3
```

## Library

```js
const { generate } = require('cname');
generate();                 // 'amber-giraffe-17'
generate({ count: 3 });     // ['...', '...', '...']
generate({ seed: 'api', format: 'camel' });
```

## Options

| Flag | Description |
| --- | --- |
| `-n, --count <num>` | Number of names (default `1`) |
| `-f, --format <fmt>` | `short`, `camel`, `snake`, `kebab`, `title`, `plain` |
| `--no-number` | Omit the numeric suffix |
| `-s, --seed <str>` | Deterministic seed |
| `-h, --help` | Show help |
| `-v, --version` | Show version |

## Test

```sh
npm test
```
