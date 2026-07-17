# Neon Asteroids

A glowing, dependency-free Asteroids clone in a single HTML file + one JS file.
Pure canvas, no build step, no network.

## Play

Open `index.html` in any browser, or serve it:

```sh
cd neon-asteroids && python3 -m http.server 8000
# -> http://localhost:8000
```

## Controls

| Action      | Keys              |
| ----------- | ----------------- |
| Thrust      | Up / W            |
| Turn        | Left Right / A D  |
| Fire        | Space (hold)      |
| Hyperspace  | Shift             |
| Pause       | P                 |
| Start       | Enter             |

## Features

- Neon glow rendering with a slowly hue-cycling asteroid palette
- Three asteroid sizes with classic split-on-hit behavior (20/50/100 pts)
- Wave progression with banner, screen shake, and particle explosions
- Invulnerability blink after respawn, hyperspace with 3s cooldown
- Twinkling parallax starfield
