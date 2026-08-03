#!/usr/bin/env python3
"""
sysdash — a dependency-free live terminal system dashboard.

Reads Linux /proc and /sys directly (no psutil, no third-party packages)
and renders a self-updating panel: CPU, load, memory, swap, disk, network,
and a live scrolling line chart of CPU/memory over time.

Usage:
    python3 sysdash.py               # auto-detect TTY, 8fps, 120-frame history
    python3 sysdash.py --interval 5  --width 70 --once
"""

import argparse
import math
import os
import shutil
import sys
import time

# --------------------------------------------------------------------------
# /proc readers
# --------------------------------------------------------------------------

def read_cpu_times():
    """Return a dict of aggregate CPU time categories (jiffies since boot)."""
    with open("/proc/stat") as f:
        fields = f.readline().split()
    # fields: ['cpu', user, nice, system, idle, iowait, irq, softirq, steal, ...]
    keys = ["user", "nice", "system", "idle", "iowait", "irq", "softirq", "steal"]
    return {k: int(v) for k, v in zip(keys, fields[1:])}


def cpu_percent(prev, now):
    """Return (total%, idle%) between two sampled /proc/stat cpu rows."""
    delta = sum(now[k] - prev[k] for k in now)
    idle = (now["idle"] + now["iowait"]) - (prev["idle"] + prev["iowait"])
    if delta <= 0:
        return 0.0, 0.0
    return 100.0 * (delta - idle) / delta, 100.0 * idle / delta


def load_average():
    with open("/proc/loadavg") as f:
        parts = f.read().split()
    return [float(p) for p in parts[:3]]


def mem_info():
    """Return used/total (MiB) for RAM and swap."""
    info = {}
    with open("/proc/meminfo") as f:
        for line in f:
            key, rest = line.split(":", 1)
            info[key] = int(rest.split()[0]) * 1024  # KiB -> bytes
    ram_total = info["MemTotal"]
    ram_used = ram_total - info["MemAvailable"]
    swap_total = info["SwapTotal"]
    swap_used = swap_total - info["SwapFree"] - info.get("SwapCached", 0.0)
    return ram_total, ram_used, swap_total, swap_used


def read_net():
    """Return cumulative RX/TX bytes from /proc/net/dev."""
    rx = tx = 0
    with open("/proc/net/dev") as f:
        next(f), next(f)  # header lines
        for line in f:
            if ":" not in line:
                continue
            iface, rest = line.split(":", 1)
            data = rest.split()
            if iface.strip() == "lo":
                continue
            rx += int(data[0])
            tx += int(data[8])
    return rx, tx


def disk_usage():
    """Return a deduped list of (mountpoint, total-bytes, used-bytes).

    One entry per backing device, preferring the shortest mount path so that
    bind-mounts of the same filesystem collapse into a single row.
    """
    skip_fstype = {"proc", "sysfs", "devtmpfs", "tmpfs", "cgroup", "cgroup2",
                   "overlay", "autofs", "debugfs", "mqueue", "securityfs",
                   "pstore", "bpf", "tracefs", "hugetlbfs", "devpts", "binfmt_misc"}
    by_dev = {}
    with open("/proc/mounts") as f:
        for line in f:
            parts = line.split()
            if len(parts) < 2:
                continue
            dev, mnt, fstype = parts[0], parts[1], parts[2]
            if fstype in skip_fstype:
                continue
            try:
                st = os.statvfs(mnt)
            except OSError:
                continue
            total = st.f_blocks * st.f_frsize
            used = (st.f_blocks - st.f_bfree) * st.f_frsize
            # keep the shortest mount path for this device
            prev = by_dev.get(dev)
            if prev is None or len(mnt) < len(prev[0]):
                by_dev[dev] = (mnt, total, used)
    return sorted(by_dev.values(), key=lambda r: r[0])


# --------------------------------------------------------------------------
# rendering helpers
# --------------------------------------------------------------------------

def bar(ratio, width):
    """Render a horizontal bar of the given width for a 0..1 ratio."""
    ratio = max(0.0, min(1.0, ratio))
    filled = int(round(ratio * width))
    # chunky gradient by fill fraction, high usage => hotter color
    if filled == 0:
        return " " * width
    return ("█" * filled) + ("░" * (width - filled))


def human(n):
    """Format a byte count / arbitrary unit as a compact SI-ish string."""
    if n < 0:
        return "-"
    units = ["", "k", "M", "G", "T"]
    val = float(n)
    for unit in units:
        if val < 1000 or unit == units[-1]:
            return f"{val:.1f}{unit}" if unit else f"{int(val)}"
        val /= 1000.0


def human_rate(n):
    """Format a per-second byte rate with a /s suffix."""
    return human(n) + "/s"


class Chart:
    """Minimal scrolling line chart rendered with block characters + braille."""

    def __init__(self, history, height, label):
        self.history = list(history)
        self.height = height
        self.label = label

    def push(self, value, lo, hi):
        self.history.append(value)
        if len(self.history) > 200:
            del self.history[: len(self.history) - 200]

    def render(self, lo, hi, width):
        span = (hi - lo) or 1.0
        rows = []
        for r in range(self.height):
            vmax = hi - span * (r / self.height)
            vmin = hi - span * ((r + 1) / self.height)
            row = ""
            for v in self.history:
                row += "█" if vmax > v >= vmin else " "
            rows.append(row)
        # label header
        head = f"{self.label}  [{lo:.0f}–{hi:.0f}]"
        return "\n".join(rows) + "\n" + head[-width:]


# --------------------------------------------------------------------------
# app
# --------------------------------------------------------------------------

def poll_once(width):
    """Sample everything once; return a dict of formatted panels + raw data."""
    now = read_cpu_times()
    if poll_once._last is None:
        poll_once._last = now
        cpu = 0.0
    else:
        cpu, _ = read_cpu_percent(poll_once._last, now)
        poll_once._last = now
    load = load_average()
    ram_total, ram_used, swap_total, swap_used = mem_info()

    rx, tx = read_net()
    if poll_once._last_net is None:
        rx_rate = tx_rate = 0.0
    else:
        lrx, ltx, lt = poll_once._last_net
        dt = max(time.time() - lt, 1e-6)
        rx_rate = (rx - lrx) / dt
        tx_rate = (tx - ltx) / dt
    poll_once._last_net = (rx, tx, time.time())

    disks = disk_usage()
    return {
        "cpu": cpu, "load": load,
        "ram_total": ram_total, "ram_used": ram_used,
        "swap_total": swap_total, "swap_used": swap_used,
        "rx_rate": rx_rate, "tx_rate": tx_rate,
        "disks": disks, "width": width,
    }


# initialise module-level sample caches
poll_once._last = None
poll_once._last_net = None

# forward refs (defined above but assign at module level to keep poll_once clean)
read_cpu_percent = cpu_percent


def render(p):
    w = p["width"]
    lines = []
    add = lines.append

    # header
    host = os.uname().nodename
    uptime_s = time.monotonic()
    h, m, s = int(uptime_s // 3600), int(uptime_s % 3600 // 60), int(uptime_s % 60)
    cores = getattr(render, "cores", os.cpu_count() or 1)
    add(f"  {host}   {h}h {m:02d}m {s:02d}s   {cores} cores".center(w))

    # CPU bar + load
    cpu_w = w - 12
    add(f"  CPU   {bar(p['cpu'] / 100, cpu_w)} {p['cpu']:5.1f}%")
    load = p["load"]
    loadtxt = f"  load   {load[0]:5.2f}  {load[1]:5.2f}  {load[2]:5.2f}"
    add(loadtxt.ljust(w))

    # memory bar
    ram_ratio = p["ram_used"] / p["ram_total"] if p["ram_total"] else 0
    mw = w - 20
    add(f"  MEM    {bar(ram_ratio, mw)} {human(p['ram_used'])}/{human(p['ram_total'])}".ljust(w))
    if p["swap_total"] > 0:
        swr = p["swap_used"] / p["swap_total"]
        add(f"  swap   {bar(swr, mw)} {human(p['swap_used'])}/{human(p['swap_total'])}".ljust(w))

    # network
    add(f"  net    ↓ {human_rate(p['rx_rate']):>9}   ↑ {human_rate(p['tx_rate']):>9}".ljust(w))

    # disks
    for mnt, total, used in p["disks"][:3]:
        ratio = used / total if total else 0
        add(f"  {mnt:<7} {bar(ratio, w - 25)} {human(used)}/{human(total)}".ljust(w))

    add("  " + "─" * (w - 6))
    return "\n".join(lines)


def draw(interval, width, height, once, history_frames):
    # chart sample accumulators
    hist = []
    t = time.monotonic()
    cpu_hi, mem_hi = 100.0, 100.0

    # seed sample caches, then wait a beat so the first visible frame has a
    # real elapsed window to compute rates/cpu-percent from
    poll_once(width)
    time.sleep(0.25)

    print("\033[2J\033[H\033[?25l", end="", flush=True)
    try:
        while True:
            p = poll_once(width)
            hist.append((p["cpu"], 100.0 * p["ram_used"] / p["ram_total"] if p["ram_total"] else 0))
            if len(hist) > history_frames:
                del hist[: len(hist) - history_frames]

            cpu_hi = max(cpu_hi, max(x[0] for x in hist) or 1)
            mem_hi = max(mem_hi, max(x[1] for x in hist) or 1)

            body = render(p)
            chart = Chart([x[0] for x in hist], 8, "CPU %")
            memchart = Chart([x[1] for x in hist], 8, "MEM %")

            out = ["\033[H"] + body.splitlines()
            out.append("")
            out.append(chart.render(0, cpu_hi, width))
            out.append(memchart.render(0, mem_hi, width))
            out.append("")
            out.append("q : quit".rjust(width - 4))
            sys.stdout.write("\n".join(out))
            sys.stdout.flush()

            if once:
                break

            # wait for next tick, polling stdin for 'q'
            deadline = time.monotonic() + interval
            import select
            while time.monotonic() < deadline:
                r, _, _ = select.select([sys.stdin], [], [], 0.1)
                if r and sys.stdin.read(1).lower() == "q":
                    print("\033[?25h\033[H\033[2J", end="", flush=True)
                    return
                time.sleep(0.02)
    except KeyboardInterrupt:
        pass
    finally:
        print("\033[?25h", end="", flush=True)


def main():
    ap = argparse.ArgumentParser(description="Dependency-free Linux system dashboard")
    ap.add_argument("--interval", type=float, default=1.0, help="refresh seconds (default 1.0)")
    ap.add_argument("--width", type=int, default=None, help="panel width (default: terminal)")
    ap.add_argument("--once", action="store_true", help="render a single frame and exit")
    args = ap.parse_args()

    is_tty = sys.stdout.isatty()
    if not is_tty and not args.once:
        # non-tty: emit a few frames for piping/logging then stop
        draw(args.interval, args.width or 80, 8, once=True, history_frames=60)
        sys.exit(0)

    width = args.width or shutil.get_terminal_size((80, 24)).columns
    width = max(40, min(width, 160))
    draw(args.interval, width, 8, args.once, history_frames=120)


if __name__ == "__main__":
    main()
