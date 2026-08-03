# Acquisition Dashboard

A single-file, self-contained HTML dashboard (`dashboard.html`) — a demo built to
exercise the `dataviz` method. No build step, no dependencies, no network.

## Open it

```sh
open dashboard.html      # macOS
xdg-open dashboard.html  # Linux
```

(or drag the file into any browser)

## What's inside

Synthetic daily signups across three acquisition channels (Direct, Organic,
Referral) over 12 weeks. One page, scoped by a single filter row:

- **KPI row** — active signups (with sparkline), avg/day, conversion
- **Line chart** — signups over time, direct-labeled with hover crosshair
- **Stacked bar** — part-to-whole share for the selected period, per-mark hover
- **Table view** — every value, keyboard/BV reachable with no hovering

## Method points honored

Built against the dataviz reference palette:

- Single axis throughout (no dual-axis)
- Categorical hues in **fixed order** (slots 1/2/3) — never cycled or generated
- **Emphasis** treatment on the line chart: Direct is the lead series in color, the
  rest recede in gray — color follows the entity, not rank
- Legend + direct labels so identity is never color-alone
- Hover layer by default: crosshair on lines, per-mark tooltip on bars, hit targets
  bigger than the mark
- Filter row above the charts; all views re-render against the same slice
- **Dark mode** selected from the same ramps (both `prefers-color-scheme` and a
  `data-theme` toggle), **texture** toggle for the CVD/print/forced-colors case
- Tooltip rows use line keys, not ink boxes; values lead, labels follow

## Data

The dataset is generated in-browser from a seeded PRNG (deterministic — same
renders each load), so the file is fully self-contained. Replace the `rows` block
with real data to repurpose it.
