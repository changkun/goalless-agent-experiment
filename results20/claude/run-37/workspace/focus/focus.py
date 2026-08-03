#!/usr/bin/env python3
"""focus — a tiny offline task + pomodoro focus tracker.

Zero dependencies. Tasks and focus sessions persist to a JSON file
(default ~/.focus/data.json). No network, no servers, no setup.

Usage:
  focus add "write report" [--tags work]
  focus list [--all] [--tag work]
  focus done <id>          mark a task complete
  focus redo <id>          mark a task incomplete
  focus rm <id>            delete a task
  focus focus [--min 25] [--tags work]   start a pomodoro (countdown)
  focus stats [--days 7]   focus-time summary
  focus dashboard          serve an HTML dashboard
  focus sync               prune finished tasks older than 7 days
"""

import argparse
import json
import os
import signal
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path

DATA_DIR = Path(os.environ.get("FOCUS_DATA_DIR", Path.home() / ".focus"))
DATA_FILE = DATA_DIR / "data.json"

FOCUS_MIN = 25   # default pomodoro length in minutes
SYNC_DAYS = 7    # completed tasks are pruned after this many days

COLORS = {"reset": "\033[0m", "dim": "\033[2m", "bold": "\033[1m",
          "green": "\033[32m", "red": "\033[31m", "yellow": "\033[33m",
          "cyan": "\033[36m", "magenta": "\033[35m"}


def c(text, *names):
    """Colorize text if stdout is a TTY; plain otherwise."""
    if not sys.stdout.isatty():
        return text
    return "".join(COLORS[n] for n in names) + text + COLORS["reset"]


def now_iso():
    return datetime.now().isoformat(timespec="seconds")


def load():
    if DATA_FILE.exists():
        try:
            return json.loads(DATA_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            return {"tasks": [], "sessions": []}
    return {"tasks": [], "sessions": []}


def save(data):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    tmp = DATA_FILE.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n")
    tmp.replace(DATA_FILE)


def next_id(tasks):
    return (max((t["id"] for t in tasks), default=0) + 1)


# ---------------------------------------------------------------- tasks
def cmd_add(args):
    data = load()
    tid = next_id(data["tasks"])
    data["tasks"].append({
        "id": tid,
        "title": args.title,
        "tags": args.tags or [],
        "done": False,
        "created": now_iso(),
    })
    save(data)
    print(c(f"✓ added #{tid}: {args.title}", "green"))


def cmd_list(args):
    data = load()
    tasks = [t for t in data["tasks"]
             if (args.all or not t["done"])
             and (not args.tag or args.tag in t["tags"])]
    tasks.sort(key=lambda t: (t["done"], -t["id"]))
    if not tasks:
        print(c("No tasks. Add one with: focus add \"your task\"", "dim"))
        return
    for t in tasks:
        mark = c("[x]", "green") if t["done"] else c("[ ]", "red")
        title = c(t["title"], "dim") if t["done"] else t["title"]
        tags = c(" ".join(f"#{x}" for x in t["tags"]), "cyan") if t["tags"] else ""
        print(f"#{t['id']:<3} {mark} {title} {tags}")


def _set_done(tid, done, verb):
    data = load()
    for t in data["tasks"]:
        if t["id"] == tid:
            t["done"] = done
            if done:
                t.setdefault("completed", now_iso())
            save(data)
            print(c(f"{verb} #{tid}: {t['title']}", "green"))
            return
    print(c(f"No task #{tid}.", "red"), file=sys.stderr)
    sys.exit(1)


def cmd_done(args):
    _set_done(args.id, True, "✓ completed")


def cmd_redo(args):
    _set_done(args.id, False, "↩ reopened")


def cmd_rm(args):
    data = load()
    before = len(data["tasks"])
    data["tasks"] = [t for t in data["tasks"] if t["id"] != args.id]
    if len(data["tasks"]) == before:
        print(c(f"No task #{args.id}.", "red"), file=sys.stderr)
        sys.exit(1)
    save(data)
    print(c(f"✗ removed #{args.id}", "yellow"))


def cmd_sync(args):
    data = load()
    prune = date.today() - timedelta(days=args.days)
    kept = []
    removed = 0
    for t in data["tasks"]:
        if t["done"] and "completed" in t:
            comp = datetime.fromisoformat(t["completed"]).date()
            if comp < prune:
                removed += 1
                continue
        kept.append(t)
    data["tasks"] = kept
    save(data)
    print(c(f"pruned {removed} finished task(s) older than {args.days} day(s)", "dim"))


# -------------------------------------------------------------- focus
def _fmt_seconds(secs):
    secs = max(0, int(secs))
    h, rem = divmod(secs, 3600)
    m, s = divmod(rem, 60)
    return f"{h}h {m:02d}m {s:02d}s" if h else f"{m:02d}m {s:02d}s"


def cmd_focus(args):
    data = load()
    minutes = args.min or FOCUS_MIN
    total = minutes * 60
    tags = args.tags or []
    # A backgrounded process inherits SIGINT as ignored; re-arm it so the
    # pomodoro is always interruptible.
    signal.signal(signal.SIGINT, signal.default_int_handler)
    # optional countdown to the minute; 1s tick, alarms + prints on completion
    print(c(f"⏱  focus for {minutes:02d} min", "bold"))
    if tags:
        print(c("   " + " ".join(f"#{t}" for t in tags), "cyan"))
    print(c("   (Ctrl+C to stop early — elapsed time is still saved)", "dim"))
    start = time.time()
    remaining = total
    try:
        while remaining > 0:
            bar_w = 24
            filled = int(bar_w * (total - remaining) / total)
            bar = "█" * filled + "░" * (bar_w - filled)
            sys.stdout.write(f"\r   {bar} {_fmt_seconds(remaining)}")
            sys.stdout.flush()
            time.sleep(1)
            remaining = total - int(time.time() - start)
        print()
    except KeyboardInterrupt:
        print("\n   stopped early.")
    elapsed = int(time.time() - start)
    data["sessions"].append({
        "date": date.today().isoformat(),
        "minutes": elapsed / 60,
        "tags": tags,
        "planned_min": minutes,
    })
    save(data)
    print(c(f"✓ logged {_fmt_seconds(elapsed)} of focus", "green") +
          (f"  {_fmt_seconds(total)} planned" if elapsed < total else "  🎉 completed!"))


# --------------------------------------------------------------- stats
def cmd_stats(args):
    data = load()
    days = args.days
    cutoff = date.today() - timedelta(days=days - 1)
    recent = [s for s in data["sessions"]
              if datetime.fromisoformat(s["date"]).date() >= cutoff]

    total_min = sum(s["minutes"] for s in recent)
    sessions = len(recent)

    # per-day tally filling the whole window
    tally = {}
    for i in range(days):
        d = (cutoff + timedelta(days=i)).isoformat()
        tally[d] = 0.0
    for s in recent:
        tally[s["date"]] = tally.get(s["date"], 0.0) + s["minutes"]

    print(c(f"Focus — last {days} day(s)", "bold"))
    print(f"  total      : {_fmt_seconds(total_min * 60)}")
    print(f"  sessions   : {sessions}")
    if days > 1:
        peak = max(tally.values())
        for d, mins in tally.items():
            bar_w = 20
            filled = int(bar_w * mins / peak) if peak else 0
            bar = "█" * filled
            label = c(d[5:], "dim")  # MM-DD
            print(f"  {label}  {bar} {_fmt_seconds(mins*60)}")

    # tags breakdown
    tag_min = {}
    for s in recent:
        for tg in s["tags"]:
            tag_min[tg] = tag_min.get(tg, 0.0) + s["minutes"]
    if tag_min:
        print(c("  by tag:", "dim"))
        for tg, mins in sorted(tag_min.items(), key=lambda x: -x[1]):
            print(f"    #{tg:<14} {_fmt_seconds(mins*60)}")


# ----------------------------------------------------------- dashboard
DASHBOARD_HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>focus · dashboard</title>
<style>
  :root { color-scheme: light dark; }
  * { box-sizing: border-box; }
  body { font: 15px/1.5 system-ui, sans-serif; max-width: 760px; margin: 0 auto;
         padding: 2rem 1.5rem; color: #1a1a1a; background: #fafafa; }
  h1 { font-size: 1.4rem; }
  h2 { font-size: 1.05rem; margin: 2rem 0 .5rem; color: #555; }
  .card { background: #fff; border: 1px solid #e3e3e3; border-radius: 10px;
          padding: 1rem 1.25rem; margin: .5rem 0; box-shadow: 0 1px 2px rgb(0 0 0 / .03); }
  .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: .5rem; }
  .stat b { display: block; font-size: 1.5rem; }
  .stat span { color: #777; font-size: .8rem; }
  .bar-row { display: flex; align-items: center; gap: .6rem; margin: .25rem 0; }
  .bar-grow { flex: 1; background: #eee; border-radius: 6px; height: 14px; overflow: hidden; }
  .bar-fill { height: 100%; background: linear-gradient(90deg,#4f46e5,#22d3ee); }
  .bar-label { min-width: 52px; font-variant-numeric: tabular-nums; color: #555; font-size: .8rem; }
  .tag { display: inline-block; background: #eef2ff; color: #4338ca; border-radius: 999px;
         padding: 0 .6rem; font-size: .8rem; margin: 0 .2rem .2rem 0; }
  .done { color: #999; text-decoration: line-through; }
  ul { list-style: none; padding: 0; margin: 0; }
  li { padding: .35rem 0; border-bottom: 1px solid #f0f0f0; }
  .muted { color: #888; }
  @media (prefers-color-scheme: dark) {
    body { color: #e6e6e6; background: #161616; }
    .card { background: #1f1f1f; border-color: #2e2e2e; }
    .bar-grow { background: #2c2c2c; }
    li { border-color: #262626; }
    .tag { background: #262b45; color: #a5b4fc; }
    .done { color: #666; }
  }
</style>
</head>
<body>
<h1>🧘 focus dashboard</h1>
<div class="grid">
  <div class="card stat"><b>{minutes_today}</b><span>min focused today</span></div>
  <div class="card stat"><b>{sessions}</b><span>sessions (7d)</span></div>
  <div class="card stat"><b>{total_7d}</b><span>min focused (7d)</span></div>
  <div class="card stat"><b>{open}</b><span>open tasks</span></div>
</div>

<h2>Last 7 days</h2>
<div class="card">
{bars}
</div>

<h2>Open tasks</h2>
<div class="card"><ul>
{task_list}
</ul></div>

<p class="muted">Data lives in ~/.focus/data.json · rendered at {ts}</p>
</body>
</html>
"""


def _fmt_minutes(mins):
    mins = max(0, round(mins))
    if mins >= 60:
        h, m = divmod(mins, 60)
        return f"{h}h{m:02d}m"
    return f"{mins}m"


def render_dashboard(data):
    today = date.today().isoformat()
    cutoff7 = (date.today() - timedelta(days=6)).isoformat()
    seven = [s for s in data["sessions"] if s["date"] >= cutoff7]
    today_min = sum(s["minutes"] for s in data["sessions"] if s["date"] == today)
    total_7d = sum(s["minutes"] for s in seven)

    # daily bars
    tally = {}
    for i in range(7):
        tally[(date.today() - timedelta(days=6 - i)).isoformat()] = 0.0
    for s in seven:
        tally[s["date"]] = tally.get(s["date"], 0.0) + s["minutes"]
    peak = max(tally.values(), default=0) or 1
    bars = []
    for day, mins in tally.items():
        pct = mins / peak * 100
        label = datetime.fromisoformat(day).strftime("%a %d")
        bars.append(
            f'<div class="bar-row"><span class="bar-label">{label}</span>'
            f'<div class="bar-grow"><div class="bar-fill" style="width:{pct:.0f}%"></div></div>'
            f'<span class="bar-label">{_fmt_minutes(mins)}</span></div>'
        )
    bars_html = "\n".join(bars) if bars else '<span class="muted">No sessions yet.</span>'

    open_tasks = [t for t in data["tasks"] if not t["done"]]
    if open_tasks:
        lis = []
        for t in sorted(open_tasks, key=lambda x: x["id"]):
            tags = "".join(f'<span class="tag">{g}</span>' for g in t["tags"])
            lis.append(f'<li>#{t["id"]} {t["title"]} {tags}</li>')
        task_html = "\n".join(lis)
    else:
        task_html = '<li class="muted">Nothing to do. Add a task from the CLI!</li>'

    # CSS uses braces, so plain .format() would misread them — substitute tokens instead.
    return (DASHBOARD_HTML
            .replace("{minutes_today}", _fmt_minutes(today_min))
            .replace("{sessions}", str(len(seven)))
            .replace("{total_7d}", _fmt_minutes(total_7d))
            .replace("{open}", str(len(open_tasks)))
            .replace("{bars}", bars_html)
            .replace("{task_list}", task_html)
            .replace("{ts}", datetime.now().strftime("%Y-%m-%d %H:%M")))


def cmd_dashboard(args):
    data = load()
    html = render_dashboard(data)
    out = DATA_DIR / "dashboard.html"
    out.write_text(html)
    url = f"http://127.0.0.1:{args.port}"
    print(c(f"dashboard ready → {url}", "green"))
    print(c("press Ctrl+C to stop", "dim"))
    import http.server
    import functools

    handler = functools.partial(http.server.SimpleHTTPRequestHandler,
                                directory=str(DATA_DIR))
    http.server.HTTPServer(("127.0.0.1", args.port), handler).serve_forever()


# ----------------------------------------------------------------- main
def build_parser():
    p = argparse.ArgumentParser(prog="focus", description="task + pomodoro focus tracker")
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("add", help="add a task")
    a.add_argument("title")
    a.add_argument("--tags", nargs="*", default=[], help="space-separated tags")
    a.set_defaults(fn=cmd_add)

    a = sub.add_parser("list", help="list open tasks")
    a.add_argument("--all", action="store_true", help="include completed")
    a.add_argument("--tag", help="filter by tag")
    a.set_defaults(fn=cmd_list)

    for name, fn in (("done", cmd_done), ("redo", cmd_redo), ("rm", cmd_rm)):
        a = sub.add_parser(name)
        a.add_argument("id", type=int)
        a.set_defaults(fn=fn)

    a = sub.add_parser("focus", help="run a pomodoro")
    a.add_argument("--min", type=int, help="length in minutes")
    a.add_argument("--tags", nargs="*", default=[])
    a.set_defaults(fn=cmd_focus)

    a = sub.add_parser("stats", help="focus summary")
    a.add_argument("--days", type=int, default=7)
    a.set_defaults(fn=cmd_stats)

    a = sub.add_parser("sync", help="prune old completed tasks")
    a.add_argument("--days", type=int, default=SYNC_DAYS)
    a.set_defaults(fn=cmd_sync)

    a = sub.add_parser("dashboard", help="serve HTML dashboard")
    a.add_argument("--port", type=int, default=8321)
    a.set_defaults(fn=cmd_dashboard)
    return p


def main():
    args = build_parser().parse_args()
    args.fn(args)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        sys.exit(130)
