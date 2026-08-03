# About mdgen

This page demonstrates building a multi-file site from nested directories.

The generator walks every `.md` file recursively, preserving relative paths:

- `demo/index.md` → `site/index.html`
- `demo/pages/about.md` → `site/pages/about.html`

No external dependencies, no build step beyond standard Python, and the output
is portable static HTML you can host anywhere.
