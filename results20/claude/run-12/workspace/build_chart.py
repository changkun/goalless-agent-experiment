#!/usr/bin/env python3
"""
Build a self-contained interactive HTML chart of NASA GISS global
temperature anomalies (1880–2025).

Data: NASA Goddard Institute for Space Studies — GISTEMP v4
      "GLOBAL Land-Ocean Temperature Index", annual (J-D) anomalies
      vs the 1951–1980 base period, in 0.01 degC.
Source file: /tmp/glb.txt (fetched from data.giss.nasa.gov)
"""
import re

SRC = "/tmp/glb.txt"
OUT = "/workspace/temperature.html"

# ---- parse -------------------------------------------------------------
years, anoms = [], []
with open(SRC) as f:
    for line in f:
        m = re.match(r"\s*(\d{4})\s+(.+?)\s+(-?\d+|\*{3,4})\s+", line)
        if not m:
            continue
        year = int(m.group(1))
        jd = m.group(3)
        if jd.startswith("*"):
            continue
        years.append(year)
        anoms.append(int(jd) / 100.0)

# keep complete years only (drop partial trailing rows, e.g. 2026)
while years and years[-1] != 2025:
    years.pop()
    anoms.pop()

# ---- linear trend (degC per decade) ------------------------------------
n = len(years)
mx = sum(years) / n
my = sum(anoms) / n
sxx = sum((y - mx) ** 2 for y in years)
sxy = sum((y - mx) * (v - my) for y, v in zip(years, anoms))
slope = sxy / sxx
per_decade = slope * 10
intercept = my - slope * mx

latest_year, latest = years[-1], anoms[-1]
warm_idx = max(range(n), key=lambda i: anoms[i])
warm_year, warm_val = years[warm_idx], anoms[warm_idx]

# ---- assemble pieces ----------------------------------------------------
pts = ",".join(f"[{y},{v:.2f}]" for y, v in zip(years, anoms))
trend0 = intercept + slope * years[0]
trend1 = intercept + slope * years[-1]

def stat_cls(v):
    return "up" if v > 0 else "down"

rows = "".join(
    f"<tr><td>{y}</td>"
    f"<td>{v:+.2f}</td><td class=\"delta {stat_cls(v)}\">{'&#9650;' if v>=0 else '&#9660;'} {abs(v):.2f}</td></tr>"
    for y, v in zip(years, anoms)
)

# ---- template with placeholder tokens (no f-string brace escaping) ------
TEMPLATE = open("/workspace/_template.html").read()

T = TEMPLATE
for token, val in [
    ("@@LATEST@@", f"{latest:.2f}"),
    ("@@LATEST_YEAR@@", str(latest_year)),
    ("@@PER_DECADE@@", f"{per_decade:.2f}"),
    ("@@WARM_YEAR@@", str(warm_year)),
    ("@@WARM_VAL@@", f"{warm_val:.2f}"),
    ("@@FIRST_YEAR@@", str(years[0])),
    ("@@LAST_YEAR@@", str(years[-1])),
    ("@@TREND0@@", f"{trend0:.3f}"),
    ("@@TREND1@@", f"{trend1:.3f}"),
    ("@@PTS@@", pts),
    ("@@ROWS@@", rows),
]:
    T = T.replace(token, val)

assert "@@" not in T, "unreplaced template token remains"

with open(OUT, "w") as f:
    f.write(T)

print(f"wrote {OUT}")
print(f"{n} years ({years[0]}–{years[-1]}), anomaly {anoms[0]:+.2f} -> {anoms[-1]:+.2f} C")
print(f"trend {per_decade:+.3f} C/decade; warmest {warm_year} {warm_val:+.2f} C; latest {latest_year} {latest:+.2f} C")
