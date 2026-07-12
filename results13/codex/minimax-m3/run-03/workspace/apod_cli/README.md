# apod-cli

A dependency-free Python CLI that fetches NASA's **Astronomy Picture of the
Day** and renders it as a beautifully formatted terminal card, a Markdown
file, or a self-contained HTML page.

```
$ apod --random
```

```
✦  Milky Way over the French Alps   Sunday, July 12, 2026   [IMAGE]
──────────────────────────────────────────────────────────────────────
  A snow-capped mountain range sits under a glittering band of stars…
──────────────────────────────────────────────────────────────────────
  URL:  https://apod.nasa.gov/apod/image/2607/Alps_MilkyWay_960.jpg
  By:   © Jean-Marie Malherbe
  API:  v1
```

## Install

```bash
pip install -e .
```

No third-party dependencies — just the Python standard library.

## Usage

```bash
apod                       # today's picture
apod 2024-08-12            # specific date
apod --random              # a random past entry
apod --range 2024-08-10 2024-08-15
apod --format md -o out.md # Markdown export
apod --format html -o out.html
NASA_API_KEY=your_key apod # use a real API key (else DEMO_KEY is used)
```

## API key

By default the public `DEMO_KEY` is used. The NASA API limits it to 30
requests per hour per IP. Set `NASA_API_KEY` in the environment to lift the
cap.
