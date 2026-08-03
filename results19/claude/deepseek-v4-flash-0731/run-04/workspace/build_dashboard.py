#!/usr/bin/env python3
"""Build a self-contained GitHub-stars dashboard as a single HTML file.
Data: /tmp/rows.json (live GitHub API fetch). No external dependencies."""
import json

rows = json.load(open('/tmp/rows.json'))
TOTAL_STARS = sum(r['stars'] for r in rows)
N = len(rows)

# ---- categorical palette: validated 8-slot order (light) ----
CAT = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100',
       '#e87ba4', '#008300', '#4a3aa7', '#e34948']
CAT_DARK = ['#3987e5', '#d95926', '#199e70', '#c98500',
            '#d55181', '#008300', '#9085e9', '#e66767']
OTHER = '#898781'   # neutral "fold in" gray, not a 9th hue

# ---- language shares (top 8 + Other) ----
lang_counts = {}
for r in rows:
    l = r['lang'] or '(no language)'
    lang_counts[l] = lang_counts.get(l, 0) + 1
langs = sorted(lang_counts.items(), key=lambda x: -x[1])
top8 = langs[:8]
other_n = sum(v for k, v in langs[8:])
lang_rows = [(k, v) for k, v in top8] + ([] if other_n == 0 else [('Other', other_n)])
N_LANG = len(lang_rows)
lang_colors = [CAT[i] if i < 8 else OTHER for i in range(N_LANG)]

# ---- repos created per year ----
years = {}
for r in rows:
    y = r['created'][:4]
    years[y] = years.get(y, 0) + 1
year_labels = sorted(years)

# ---- top 15 by stars ----
top15 = rows[:15]


def rounded_top(x, y, w, h, r=4):
    """Top-rounded bar path with square baseline anchor."""
    if h <= 2 * r:
        return f'M{x},{y + h} L{x},{y} L{x + w},{y} L{x + w},{y + h} Z'
    return (f'M{x},{y + h}'
            f' L{x},{y + r}'
            f' Q{x},{y} {x + r},{y}'
            f' L{x + w - r},{y}'
            f' Q{x + w},{y} {x + w},{y + r}'
            f' L{x + w},{y + h} Z')


# ================= Chart 1: repos per year =================
W1, H1 = 860, 300
ML, MR, MT, MB = 34, 12, 18, 44
pw, ph = W1 - ML - MR, H1 - MT - MB
base = MT + ph
ymax = max(years.values())
n_year = len(year_labels)
slot = pw / n_year
barw = max(6.0, slot * 0.6)

lc = [(y, years[y]) for y in year_labels]
svg1 = [f'<svg viewBox="0 0 {W1} {H1}" role="img" aria-label="Repositories created per year, 2009 to 2026">']
# gridlines (recessive)
for g in range(0, ymax + 1, max(1, (ymax + 2) // 4)):
    gy = base - ph * (g / ymax)
    svg1.append(f'<line x1="{ML}" y1="{gy:.1f}" x2="{W1 - MR}" y2="{gy:.1f}" class="grid"/>')
    svg1.append(f'<text x="{ML - 8}" y="{gy + 3:.1f}" class="tick" text-anchor="end">{g}</text>')
for i, (y, v) in enumerate(lc):
    cx = ML + i * slot + slot / 2
    bw = barw
    bx, bw2 = cx - bw / 2, bw
    bh = ph * (v / ymax)
    by = base - bh
    tip = 0 if i >= 0 else None
    svg1.append(
        f'<a href="#lang">'
        f'<path d="{rounded_top(bx, by, bw2, max(bh, 2))}"'
        f' class="yrbar" data-name="{y}" data-val="{v}"'
        f' data-tip="<b>{y}</b> &#183; {v} repo{"s" if v != 1 else ""}"/>'
        f'</a>')
    # baseline-anchored value label at bar top (relief rule)
    svg1.append(f'<text x="{cx:.1f}" y="{by - 5:.1f}" class="val" text-anchor="middle">{v}</text>')
    # x tick
    svg1.append(f'<text x="{cx:.1f}" y="{base + 18}" class="tick" text-anchor="middle">{y}</text>')
svg1.append('</svg>')
CHART1 = ''.join(svg1)

# ================= Chart 2: language share (categorical) =================
W2, H2 = 860, 320
rowh = 34
plot_h2 = N_LANG * rowh
svg2 = [f'<svg viewBox="0 0 {W2} {H2}" role="img" aria-label="Repository share by programming language">']
maxl = max(v for _, v in lang_rows)
bar_area = W2 - 170 - 150  # label + bar + value
for i, (name, v) in enumerate(lang_rows):
    y = 24 + i * rowh
    color = lang_colors[i]
    m = 'd' if i < 8 else 'l'
    bw = bar_area * (v / maxl)
    svg2.append(f'<rect x="170" y="{y + 8}" width="{max(bw, 2)}" height="16" rx="4"'
                f' class="lbar {m}" style="--c:{color}"'
                f' data-name="{name}" data-val="{v}"/>')
    svg2.append(f'<text x="160" y="{y + 20}" class="lname" text-anchor="end">{name}</text>')
    svg2.append(f'<text x="{170 + max(bw, 2) + 8}" y="{y + 20}" class="val">{v}</text>')
svg2.append('</svg>')
CHART2 = ''.join(svg2)

# ================= Chart 3: top 15 by stars =================
W3, H3 = 860, 420
rowh3 = 26
maxs = top15[0]['stars']
bar_area = W3 - 90 - 86
svg3 = [f'<svg viewBox="0 0 {W3} {H3}" role="img" aria-label="Top 15 repositories by GitHub stars">']
for i, r in enumerate(top15):
    y = 10 + i * rowh3
    bw = bar_area * (r['stars'] / maxs)
    svg3.append(f'<a href="{r["url"]}" target="_blank" rel="noopener">')
    svg3.append(f'<rect x="90" y="{y}" width="{max(bw, 2)}" height="16" rx="4" class="tbar"'
                f' data-name="{r["name"]}" data-val="{r["stars"]:,}"'
                f' data-tip="<b>{r["name"]}</b> &#183; {r["stars"]:,} stars<br>'
                f'<span class="sub">{r["desc"]}</span>"/>')
    svg3.append(f'</a>')
    svg3.append(f'<text x="80" y="{y + 12}" class="rank" text-anchor="end">{i + 1}</text>')
    svg3.append(f'<text x="98" y="{y + 12}" class="tname">{r["name"]}</text>')
    svg3.append(f'<text x="{90 + max(bw, 2) + 8}" y="{y + 12}" class="val">{(r["stars"] // 1000) / 1000:.2f}M</text>')
svg3.append('</svg>')
CHART3 = ''.join(svg3)

# ================= table rows =================
TR = []
for r in rows:
    TR.append(
        f'<tr><td class="mono">{r["name"]}</td>'
        f'<td>{r["lang"] or "—"}</td>'
        f'<td>{r["created"]}</td>'
        f'<td class="num">{r["stars"]:,}</td></tr>')
TABLE = ''.join(TR)

# language legend swatches
LEG = ''.join(
    f'<span class="lg"><i style="background:{color}"></i>{name} · {v}</span>'
    for (name, v), color in zip(lang_rows, lang_colors))

fmtr = lambda n: f'{n:,}'
html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>GitHub 100k&nbsp;★ Club — live dashboard</title>
<style>
:root{{--surface:#fcfcfb;--page:#f9f9f7;--ink:#0b0b0b;--ink2:#52514e;--muted:#898781;
--grid:#e1e0d9;--axis:#c3c2b7;--border:rgba(11,11,11,.10);--c1:#2a78d6;--c2:#eb6834;
--c3:#1baf7a;--c4:#eda100;--c5:#e87ba4;--c6:#008300;--c7:#4a3aa7;--c8:#e34948;--other:#898781;}}
@media (prefers-color-scheme:dark){{
:root:where(:not([data-theme="light"])){{--surface:#1a1a19;--page:#0d0d0d;--ink:#fff;
--ink2:#c3c2b7;--muted:#898781;--grid:#2c2c2a;--axis:#383835;--border:rgba(255,255,255,.10);
--c1:#3987e5;--c2:#d95926;--c3:#199e70;--c4:#c98500;--c5:#d55181;--c6:#008300;--c7:#9085e9;--c8:#e66767;}}
}}
:root[data-theme="dark"]{{--surface:#1a1a19;--page:#0d0d0d;--ink:#fff;--ink2:#c3c2b7;
--muted:#898781;--grid:#2c2c2a;--axis:#383835;--border:rgba(255,255,255,.10);
--c1:#3987e5;--c2:#d95926;--c3:#199e70;--c4:#c98500;--c5:#d55181;--c6:#008300;--c7:#9085e9;--c8:#e66767;}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--page);color:var(--ink);
font-family:system-ui,-apple-system,"Segoe UI",sans-serif;line-height:1.5}}
.wrap{{max-width:920px;margin:0 auto;padding:40px 24px 80px}}
header{{display:flex;align-items:flex-end;justify-content:space-between;gap:16px;flex-wrap:wrap;
border-bottom:1px solid var(--border);padding-bottom:20px;margin-bottom:8px}}
h1{{font-size:26px;margin:0;font-weight:650;letter-spacing:-.01em}}
.sub{{color:var(--ink2);margin:6px 0 0;font-size:14px}}
.controls{{display:flex;gap:8px}}
button{{font:inherit;font-size:13px;color:var(--ink2);background:var(--surface);border:1px solid var(--border);
border-radius:8px;padding:6px 12px;cursor:pointer}}
button.on{{color:var(--ink);border-color:var(--ink2)}}
.hero{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:20px 0 4px}}
.tile{{background:var(--surface);border:1px solid var(--border);border-radius:14px;padding:16px 18px}}
.tile .k{{font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:.06em}}
.tile .v{{font-size:24px;font-weight:650;margin-top:4px;font-variant-numeric:tabular-nums}}
.tile .d{{font-size:13px;color:var(--ink2);margin-top:2px}}
.card{{background:var(--surface);border:1px solid var(--border);border-radius:16px;
padding:22px 20px 12px;margin-top:22px}}
.card h2{{font-size:17px;margin:0 0 2px;font-weight:650}}
.card .ctx{{font-size:13px;color:var(--ink2);margin:0 0 10px}}
svg{{display:block;width:100%;height:auto;max-height:60vh}}
.grid{{stroke:var(--grid);stroke-width:1}}
.tick{{fill:var(--muted);font:12px system-ui,sans-serif}}
.val{{fill:var(--ink2);font:12px system-ui,sans-serif;font-variant-numeric:tabular-nums}}
.yrbar{{fill:var(--c1);cursor:pointer;transition:opacity .15s}}
.yrbar:hover{{opacity:.82}}
.lbar{{fill:var(--c);cursor:pointer}}
.ldot{{opacity:0}}
.tbar{{fill:var(--c1);cursor:pointer;transition:opacity .15s}}
.tbar:hover{{opacity:.85}}
.rank{{fill:var(--muted);font:12px system-ui,sans-serif}}
.tname{{fill:var(--ink);font:13px system-ui,sans-serif;font-weight:500}}
.legend{{display:flex;flex-wrap:wrap;gap:8px 18px;padding:6px 4px 14px}}
.legend i{{display:inline-block;width:12px;height:12px;border-radius:3px;margin-right:7px;vertical-align:-1px}}
.legend .lg{{font-size:13px;color:var(--ink2)}}
.chart-scroll{{overflow-x:auto}}
/* tooltip */
.tip{{position:fixed;pointer-events:none;background:var(--ink);color:var(--page);
padding:8px 12px;border-radius:8px;font-size:12.5px;max-width:300px;opacity:0;
transform:translate(-50%,-125%);transition:opacity .08s;z-index:10;box-shadow:0 6px 20px rgba(0,0,0,.18)}}
.tip .sub{{color:inherit;opacity:.7;font-size:12px}}
/* table */
table{{width:100%;border-collapse:collapse;font-size:13px;display:none}}
table.show{{display:table}}
th{{text-align:left;color:var(--muted);font-weight:500;font-size:12px;text-transform:uppercase;
letter-spacing:.05em;padding:6px 10px;border-bottom:1px solid var(--border)}}
td{{padding:7px 10px;border-bottom:1px solid var(--grid)}}
.mono{{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12.5px}}
.num{{text-align:right;font-variant-numeric:tabular-nums}}
table tr:hover td{{background:var(--page)}}
@keyframes fade{{from{{opacity:0;transform:translateY(4px)}}to{{opacity:1;transform:none}}}}
.card{{animation:fade .4s ease both}}
@media (prefers-reduced-motion:reduce){{.card{{animation:none}}}}
</style>
</head>
<body data-theme="">
<div class="wrap">
  <header>
    <div>
      <h1>GitHub 100k&nbsp;★ Club</h1>
      <p class="sub">Live data pulled from the GitHub API — repositories with 100,000+ stars. Updated 2026-08-03.</p>
    </div>
    <div class="controls">
      <button id="tbl" class="on">Charts</button><button id="tbl2">Table</button>
      <button id="theme">Theme</button>
    </div>
  </header>

  <div class="hero">
    <div class="tile"><div class="k">Repositories</div><div class="v">{N}</div><div class="d">at or above 100k ★</div></div>
    <div class="tile"><div class="k">Combined stars</div><div class="v">{fmtr(TOTAL_STARS)}</div><div class="d">across all in the club</div></div>
    <div class="tile"><div class="k">Top language</div><div class="v" style="font-size:20px">{top8[0][0]}</div><div class="d">{top8[0][1]} repos</div></div>
    <div class="tile"><div class="k">Oldest member</div><div class="v" style="font-size:20px">{min(years)}</div><div class="d">club started growing</div></div>
  </div>

  <div class="card" id="lang">
    <h2>Repos created per year</h2>
    <p class="ctx">100k+ star repos by the year they were created — magnitude by length.</p>
    <div class="chart-scroll">{CHART1}</div>
  </div>

  <div class="card">
    <h2>Share by language</h2>
    <p class="ctx">How the club splits across primary languages (top 8, remainder folded into “Other”).</p>
    <div class="legend">{LEG}</div>
    <div class="chart-scroll">{CHART2}</div>
  </div>

  <div class="card">
    <h2>Top 15 by stars</h2>
    <p class="ctx">The most-starred members of the club. Click a bar to open the repo.</p>
    <div class="chart-scroll">{CHART3}</div>
  </div>

  <div class="card">
    <h2>Full roster</h2>
    <p class="ctx">All {N} members, sorted by stars.</p>
    <div class="chart-scroll"><table id="rt">
      <thead><tr><th>Repository</th><th>Language</th><th>Created</th><th class="num">Stars</th></tr></thead>
      <tbody>{TABLE}</tbody>
    </table></div>
  </div>
</div>

<div class="tip" id="tip"></div>
<script>
// theme toggle
const opts = ['', 'light', 'dark'];
let ti = 0;
try {{ ti = opts.indexOf(localStorage.getItem('gh-theme')||''); if(ti<0)ti=0; }} catch(e){{}}
document.body.dataset.theme = opts[ti];
document.getElementById('theme').textContent = opts[ti] ? (opts[ti]==='dark'?'Light':'Dark') : 'Auto';
document.getElementById('theme').onclick = () => {{
  ti = (ti+1)%opts.length; document.body.dataset.theme = opts[ti];
  document.getElementById('theme').textContent = opts[ti] ? (opts[ti]==='dark'?'Light':'Dark') : 'Auto';
  try{{localStorage.setItem('gh-theme', opts[ti]);}}catch(e){{}}
}};
// charts <-> table toggle
const tblBtn=document.getElementById('tbl'), tblBtn2=document.getElementById('tbl2');
function showCharts(on){{
  document.querySelectorAll('.card').forEach(c=>c.style.display= on?'':'none');
  tblBtn.classList.toggle('on', on); tblBtn2.classList.toggle('on', !on);
  document.getElementById('rt').classList.toggle('show', !on);
}}
tblBtn.onclick=()=>showCharts(true);
tblBtn2.onclick=()=>showCharts(false);
// tooltip
const tip=document.getElementById('tip');
function show(ev, html){{
  tip.innerHTML=html; tip.style.opacity=1;
  const r=tip.getBoundingClientRect();
  tip.style.left=(ev.clientX)+'px'; tip.style.top=(ev.clientY-14)+'px';
}}
document.querySelectorAll('[data-tip]').forEach(el=>{{
  el.addEventListener('mousemove',e=>show(e,el.dataset.tip));
  el.addEventListener('mouseleave',()=>tip.style.opacity=0);
}});
document.querySelectorAll('.lbar').forEach(el=>{{
  el.addEventListener('mousemove',e=>show(e,`<b>${{el.dataset.name}}</b> &#183; ${{el.dataset.val}} repo${{el.dataset.val==1?'':'s'}}`));
  el.addEventListener('mouseleave',()=>tip.style.opacity=0);
}});
</script>
</body>
</html>
"""
open('/workspace/dashboard.html', 'w').write(html)
print('wrote /workspace/dashboard.html', len(html), 'bytes')
