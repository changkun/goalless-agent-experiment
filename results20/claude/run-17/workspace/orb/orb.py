#!/usr/bin/env python3
"""orb — a tiny, dependency-free terminal dashboard.

Reads CPU / memory / disk / uptime straight from /proc (or `psutil` if
available) and renders a live single-screen dashboard with Unicode bars and
sparklines. Zero third-party dependencies by default.
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys
import time


# --------------------------------------------------------------------------- #
# Data collection (pure-ish; each function returns a float 0..1 plus context)
# --------------------------------------------------------------------------- #

def _read_proc_stat() -> tuple[int, int] | None:
    """Return (total_jiffies, idle_jiffies) from /proc/stat, or None."""
    try:
        with open("/proc/stat") as fh:
            line = fh.readline()
    except OSError:
        return None
    parts = line.split()
    if not parts or parts[0] != "cpu":
        return None
    nums = [int(x) for x in parts[1:]]
    idle = nums[3] + (nums[4] if len(nums) > 4 else 0)  # idle + iowait
    return (sum(nums), idle)


def cpu_percent(prev: tuple[int, int] | None) -> float | None:
    """CPU busy percentage vs the previous sample, or None on first call."""
    cur = _read_proc_stat()
    if cur is None:
        return None
    if prev is not None:
        d_total = cur[0] - prev[0]
        d_idle = cur[1] - prev[1]
        if d_total:
            return max(0.0, min(100.0, 100.0 * (1 - d_idle / d_total)))
    return None


def memory_usage() -> tuple[float | None, float, float] | None:
    """(percent, used_bytes, total_bytes) from /proc/meminfo, else None."""
    fields: dict[str, int] = {}
    try:
        with open("/proc/meminfo") as fh:
            for line in fh:
                key, rest = line.split(":", 1)
                fields[key] = int(rest.split()[0]) * 1024  # kB -> bytes
    except (OSError, ValueError):
        return None
    total = fields.get("MemTotal")
    avail = fields.get("MemAvailable")
    if total and avail:
        used = total - avail
        return (100.0 * used / total, used, total)
    return None


def disk_usage(path: str = "/") -> tuple[float, float, float] | None:
    """(percent, used_bytes, total_bytes) for a filesystem."""
    try:
        st = shutil.disk_usage(path)
    except OSError:
        return None
    return (100.0 * st.used / st.total, st.used, st.total)


def system_info() -> dict:
    """Uptime, load average, hostname — best-effort."""
    info: dict = {"host": "?", "uptime": 0.0, "load": None}
    info["host"] = os.uname().nodename or "?"
    try:
        with open("/proc/uptime") as fh:
            info["uptime"] = float(fh.read().split()[0])
    except (OSError, ValueError):
        pass
    try:
        with open("/proc/loadavg") as fh:
            parts = fh.read().split()
        info["load"] = [float(x) for x in parts[:3]]
    except (OSError, ValueError):
        pass
    return info


# --------------------------------------------------------------------------- #
# Rendering (pure functions — unit-testable)
# --------------------------------------------------------------------------- #

_BAR_CHARS = " ▏▎▍▌▋▊▉█"


def bar(value: float, width: int) -> str:
    """Render `value` (0..100) as a block bar of exactly `width` cells."""
    if width <= 0:
        return ""
    value = max(0.0, min(100.0, value))
    full = int(value / 100.0 * width)
    frac = (value / 100.0 * width - full) * len(_BAR_CHARS)
    cells = _BAR_CHARS[-1] * full
    if full < width:
        cells += _BAR_CHARS[int(frac) % len(_BAR_CHARS)]
    return cells.ljust(width)


def sparkline(values: list[float], width: int, low: float = 0.0,
              high: float = 100.0) -> str:
    """Render a series as a sparkline. `values` are percent numbers."""
    if width <= 0 or not values:
        return ""
    span = max(1e-9, high - low)
    out = []
    for v in values[-width:]:
        norm = max(0.0, min(1.0, (v - low) / span))
        idx = int(norm * (len(_BAR_CHARS) - 1))
        out.append(_BAR_CHARS[idx])
    return "".join(out)


def human_bytes(n: float | None) -> str:
    """Bytes to a short human string, e.g. 1.4 GiB."""
    if n is None:
        return "?"
    step = 1024.0
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if abs(n) < step:
            return f"{n:.1f} {unit}" if unit != "B" else f"{int(n)} B"
        n /= step
    return f"{n:.1f} PiB"


def fmt_uptime(seconds: float) -> str:
    """Format a duration as '3d 04:12' or '47m'."""
    days, rem = divmod(int(seconds), 86400)
    hours, rem = divmod(rem, 3600)
    mins, secs = divmod(rem, 60)
    if days:
        return f"{days}d {hours:02d}:{mins:02d}"
    if hours:
        return f"{hours}h {mins:02d}m"
    return f"{mins}m {secs:02d}s"


# --------------------------------------------------------------------------- #
# Dashboard
# --------------------------------------------------------------------------- #

class Row:
    """One metric row: label, percentage, and extra detail text."""

    def __init__(self, label: str, percent: float | None, detail: str = ""):
        self.label = label
        self.percent = percent if percent is not None else 0.0
        self.have = percent is not None
        self.detail = detail

    def render(self, width: int) -> str:
        bar_w = max(10, width - len(self.label) - len(self.detail) - 5)
        pct = f"{self.percent:5.1f}%" if self.have else "  n/a "
        line = f"{self.label:<{width}}".split("  ")[0]
        core = f"{self.label} {pct} {bar(self.percent, bar_w)} {self.detail}"
        return core[:width]


def render(rows: list[Row], cpu_history: list[float], width: int,
           host: str, uptime: str, load: str) -> str:
    """Compose the whole dashboard frame as a string."""
    top = f"orb — {host}   up {uptime}   load {load}"
    top = top[:width]
    lines = [top, "─" * width]
    for r in rows:
        lines.append(r.render(width))
    if cpu_history:
        spark = sparkline(cpu_history, max(10, width - 12))
        lines.append(f"CPU history {spark}")
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Main loop
# --------------------------------------------------------------------------- #

def collect(cpu_prev):
    """Gather all metrics and return (rows, info, load_string)."""
    rows = []
    cur = cpu_percent(cpu_prev)
    rows.append(Row("CPU", cur, ""))

    mem = memory_usage()
    if mem:
        pct, used, total = mem
        rows.append(Row("Mem", pct, f"{human_bytes(used)} / {human_bytes(total)}"))
    else:
        rows.append(Row("Mem", None, ""))

    disk = disk_usage()
    if disk:
        pct, used, total = disk
        rows.append(Row("Disk", pct, f"{human_bytes(used)} / {human_bytes(total)}"))
    else:
        rows.append(Row("Disk", None, ""))

    info = system_info()
    load = ", ".join(f"{x:.2f}" for x in info["load"]) if info["load"] else "?"
    return rows, info, load


def _demo_frame(seed: float, history: list[float]) -> list[Row]:
    """A self-contained stand-in for real metrics (used by --demo)."""
    rows = [
        Row("CPU", ((seed * 7) % 91) + 5, ""),
        Row("Mem", ((seed * 3) % 70) + 20, "demo data"),
        Row("Disk", (seed * 13) % 100, "demo"),
    ]
    history.append(((seed * 7) % 100))
    return rows


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="tiny terminal dashboard")
    ap.add_argument("--interval", type=float, default=1.0)
    ap.add_argument("--once", action="store_true", help="single snapshot, then exit")
    ap.add_argument("--demo", action="store_true", help="simulate data")
    ap.add_argument("--count", type=int, default=0, help="frames, then exit")
    args = ap.parse_args(argv)

    cpu_prev = _read_proc_stat()
    cpu_history: list[float] = []
    frames = 0

    try:
        while True:
            width = shutil.get_terminal_size((80, 24)).columns
            os.system("cls" if os.name == "nt" else "clear")

            if args.demo:
                rows = _demo_frame(time.time(), cpu_history)
                info = {"host": "demo-host", "uptime": 3661, "load": [0.5, 0.4, 0.3]}
                load = "0.50, 0.40, 0.30"
            else:
                rows, info, load = collect(cpu_prev)
                cpu_prev = _read_proc_stat()  # refresh baseline for next frame
                if rows[0].have:
                    cpu_history.append(rows[0].percent)

            print(render(
                rows, cpu_history, width,
                info["host"],
                fmt_uptime(info.get("uptime", 0)),
                load,
            ))

            frames += 1
            if args.once or (args.count and frames >= args.count):
                break
            time.sleep(max(0.1, args.interval))
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
