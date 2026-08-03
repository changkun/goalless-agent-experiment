#!/usr/bin/env python3
"""
Generate the dataset embedded in index.html for a fictional SaaS analytics dashboard.

Deterministic (seeded) synthetic data so the report is reproducible:
  12 months, 4 acquisition channels, weekly + monthly + weekday aggregates.
Outputs a single JSON object written into the HTML template.
"""

import json
import random
from datetime import date, timedelta

CHANNELS = [
    # (name, base_sessions, session_growth/mo, base_conv, conv_growth/mo, arpu)
    ("Organic",  3500, 0.0015, 0.030, 0.003, 42),
    ("Paid",     2600, 0.0007, 0.024, 0.002, 36),
    ("Referral", 1750, 0.0011, 0.028, 0.004, 39),
    ("Social",   2100, 0.0005, 0.020, 0.001, 31),
]

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def _arange_sum(seed, n, lo, hi):
    """Return n random floats from [lo, hi], seeded, summing to 1."""
    rng = random.Random(seed)
    w = [rng.uniform(lo, hi) for _ in range(n)]
    s = sum(w)
    return [x / s for x in w]


def _approx(x):
    return round(float(x), 4)


def build():
    rng = random.Random(2027)
    data = {"channels": [c[0] for c in CHANNELS], "months": MONTHS,
            "weekdays": WEEKDAYS, "generated": date(2026, 8, 3).isoformat()}

    # ---- monthly per-channel sessions & revenue ----
    monthly_sessions = []
    monthly_revenue = []
    monthly_conv = []
    seasonality = [0.88, 0.9, 1.0, 0.96, 1.0, 1.03, 0.94, 1.06, 1.05, 1.0, 0.97, 1.14]
    for m, (name, base, sgr, conv0, cgr, arpu) in enumerate(CHANNELS):
        session_list, revenue_list, conv_list = [], [], []
        for t in range(12):
            growth = (1 + sgr) ** t
            sessions = base * growth * seasonality[t] * rng.uniform(0.92, 1.08)
            conv = conv0 * (1 + cgr) ** t * rng.uniform(0.9, 1.1)
            revenue = sessions * conv * arpu * rng.uniform(0.95, 1.05)
            session_list.append(_approx(sessions))
            revenue_list.append(_approx(revenue / 1000))  # store in $k
            conv_list.append(_approx(conv))
        monthly_sessions.append(session_list)
        monthly_revenue.append(revenue_list)
        monthly_conv.append(conv_list)

    data["monthly_sessions"] = monthly_sessions   # [channel][month] -> sessions
    data["monthly_revenue"] = monthly_revenue     # [channel][month] -> $k

    # monthly totals (for hero + stat tiles)
    rev_total = [sum(monthly_revenue[c][m] for c in range(4)) for m in range(12)]
    ses_total = [sum(monthly_sessions[c][m] for c in range(4)) for m in range(12)]
    data["rev_total"] = [_approx(v) for v in rev_total]
    data["ses_total"] = [_approx(v) for v in ses_total]

    # per-channel monthly conversion rate (percentage points)
    data["conv_rate"] = [[_approx(c * 100) for c in row] for row in monthly_conv]

    # channel mix (full-year share of sessions) for the horizontal stacked bar
    mix = [_sum(monthly_sessions[c]) for c in range(4)]
    mix_total = sum(mix)
    data["channel_share"] = [_approx(100 * x / mix_total) for x in mix]

    # weekday x month heatmap: sessions indexed by weekday * month index
    weekday_weights = _arange_sum("weekday", 7, 0.7, 1.3)
    heat = []
    for w in range(7):
        row = []
        for m in range(12):
            base = ses_total[m] / 4.3            # mean daily sessions that month
            val = 100 * base * weekday_weights[w] * rng.uniform(0.88, 1.12)
            row.append(_approx(val / 1000.0))    # store in k sessions
        heat.append(row)
    data["heatmap"] = heat

    # weekly revenue line (52 points) for the sparkline / trend context
    weekly = []
    d = date(2025, 8, 4)  # a Monday ~52 weeks before generated date
    week_growth = 1.015
    for i in range(52):
        week = week_growth ** i * rng.uniform(0.9, 1.1)
        weekly.append(_approx(280 * week))
    data["weekly_rev"] = weekly

    return data


def _sum(xs):
    return sum(xs)


def main():
    data = build()
    # Path to the HTML template next to this script.
    import pathlib
    here = pathlib.Path(__file__).resolve().parent
    html = here / "index.html"
    if not html.exists():
        raise SystemExit(f"index.html not found next to this script ({html})")
    src = html.read_text(encoding="utf-8")
    marker = "/*__DATA_JSON__*/"
    if marker not in src:
        raise SystemExit("marker /*__DATA_JSON__*/ not found in index.html")
    json_str = json.dumps(data)
    # the template marker carries the declaration, so the whole statement is
    # "const DATA = { ... };" — inject the JSON between the braces.
    out = src.replace(marker, "const DATA = " + json_str + ";", 1)
    (here / "index.generated.html").write_text(out, encoding="utf-8")
    print(f"Wrote index.generated.html ({len(out)} bytes, json {len(json_str)} bytes)")


if __name__ == "__main__":
    main()
