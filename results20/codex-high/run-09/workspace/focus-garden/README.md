# 🌱 Focus Garden

A single-file pomodoro timer that grows a little garden as you complete focus
sessions. No dependencies, no servers, no tracking — everything is saved in
your browser's `localStorage`.

## Run it

Just open `index.html` in a browser. That's it.

```bash
# optional: serve it locally
python3 -m http.server 8000 --directory .
# then visit http://localhost:8000
```

## How it works

- **Focus** phase grows a plant every time you finish a session; **Break** phase
  follows automatically.
- Plants, total focused minutes, and day streaks persist across reloads via
  `localStorage`.
- Adjust focus/break lengths, skip phases, reset, or clear the whole garden.
- **#** button renders your garden as plain text (nice for sharing).

## Milestones

Garden grows and weather changes as your plant count climbs: 1, 5, 10, 25, 50.
