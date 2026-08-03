# ascii-terminal

A tiny, zero-dependency ASCII landscape generator that renders a scrolling
night-time scene in a fake terminal. Built with plain HTML, CSS, and
JavaScript — no build step, no frameworks, no external assets.

## Run it

Open `index.html` in a browser, or serve the folder locally:

```sh
python3 -m http.server 8000 --directory ascii-terminal
# then open http://localhost:8000
```

## Commands

| Command | What it does |
| --- | --- |
| `help` | Show available commands |
| `speed <1-10>` | Change the scroll speed |
| `theme <name>` | Switch color scheme (`night`, `amber`, `matrix`, `paper`) |
| `clear` | Clear the scrollback buffer |
| `about` | Show a little blurb |
| `quit` | Stop the animation (well, "quit" — you'll come back) |

You can also press `?` to see the command list, or just hit `Enter` with an
empty line to start/pause the scene.
