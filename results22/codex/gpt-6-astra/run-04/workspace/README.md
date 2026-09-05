# A small universe

A quiet, interactive orbital playground. Open `index.html` in a modern browser; everything runs locally, with no dependencies or network requests.

- Drag backward and release to launch a comet. The dotted line previews its path.
- Tap an empty spot for a circular orbit, or use **Add comet**.
- Press **Space** to pause, **R** to reset, or **Escape** to cancel a launch.
- Toggle trails and adjust the pace with the controls.

The central star supplies all gravity; comets pass through one another. Comets that reach the star are absorbed, and those that travel far away leave the simulation. Up to 16 comets can be present at once. The simulation starts paused when your system requests reduced motion.

Built with plain HTML, CSS, and Canvas, using a fixed timestep and velocity Verlet integration.
