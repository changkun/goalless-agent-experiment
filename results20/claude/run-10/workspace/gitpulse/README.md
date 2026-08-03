# gitpulse

A dependency-free health check for a git repository. It reads commit history
via git plumbing and reports:

- **Pace** — commits, active days, commit span, commits per day
- **Authors** — commit share per author, with an activity sparkline over the
  last 8 active days
- **Bus factor** — the smallest set of authors responsible for half the commits
- **Churn hotspots** — who made the most commits on a single day

## Usage

```console
$ gitpulse [path] [-n N]
```

```console
$ gitpulse /path/to/repo
gitpulse 0.1.0  —  /path/to/repo  (main)
========================================================================
Commits          482
Active days      131
Commit span      2023-01-12 → 2026-07-30
Pace             3.68 commits/active day (0.38/day overall)
Bus factor       3

author                   commits   share  activity (last 8 active days)
Alice A                    210   43.6%   ▁▃▄▅▆▇█▆
Bob B                      150   31.1%   ▂▃▂▄▅▂▃▄
...
```

## Install

```console
$ pip install .
$ gitpulse --version
```

Or run without installing:

```console
$ python -m gitpulse.cli .
```

## Tests

```console
$ python -m unittest discover -s tests -v
```

## License

MIT
