# td — a tiny terminal task manager

Zero-dependency task manager in a single Python file. Tasks live in one JSON file
(no database, no setup).

## Install

```bash
chmod +x td.py
sudo ln -s "$(pwd)/td.py" /usr/local/bin/td   # optional: use it anywhere as `td`
```

Data is stored at `~/.config/td/tasks.json` (override with the `TD_DIR` env var).

## Usage

```
td                        list all open tasks
td add TEXT [#tag...]     add a task        (aliases: a, new)
      -p, --prio 0|1|2    priority (0 low, 1 normal, 2 high; default 1)
      -d, --due 2026-12-31  due date (YYYY-MM-DD)
td done ID [ID...]        mark done         (aliases: d, complete)
td open ID [ID...]        mark not done     (aliases: o)
td rm ID [ID...]          delete permanently (aliases: del, delete)
td edit ID TEXT           replace the text
td tag ID TAG [TAG...]    add tags
td untag ID TAG [TAG...]  remove tags
td prio ID 0|1|2          set priority
td due ID 2026-12-31|none set / clear due date
td ls [FILTER...]         filter the list
td stats                  show a summary
td clear-done             remove all completed tasks
td help                   this help
```

### Filters (`td ls`)

| Filter  | Meaning                            |
|---------|------------------------------------|
| `+tag`  | only tasks with `tag`              |
| `-tag`  | only tasks without `tag`           |
| `prio:N`| only tasks with priority N (0-2)   |
| `done`  | only completed tasks               |
| `open`  | only not-done tasks                |
| `today` | due today                          |
| `overdue` | past-due and not done            |
| `text`  | case-insensitive substring of text |

Combine freely: `td ls +work overdue` lists high-priority, not-done, past-due work tasks.

> Note: tags must be quoted in some shells (`#` starts a comment in bash/zsh):
> `td add "Write report" "#work"`.

## Examples

```bash
td add "Ship v2" "#urgent" "#work" -p 2 -d 2026-08-20
td add "Water plants" "#home"
td ls +urgent          # all urgent tasks
td ls overdue          # what's past-due
td done 1              # finish task 1
td stats               # summary
```

## Design

- JSON storage, atomic writes (write-then-rename) so a crashed write never corrupts data.
- Sorting: done tasks sink to the bottom; open tasks by priority desc, then id.
- Priorities, due dates, and tags are all optional — add plain tasks and enrich later.
- Pure standard library; works on any Python ≥ 3.8.

## Tests

```bash
python3 test_td.py      # or: ./test_td.py
```
