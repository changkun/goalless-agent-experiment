# Workspace Snapshot

A small standard-library Python utility for quickly understanding a directory before
editing it.

Run it from this workspace:

```bash
python3 workspace_snapshot.py .
```

Useful options:

```bash
python3 workspace_snapshot.py /path/to/project --json
python3 workspace_snapshot.py . --include-hidden --ignore logs --max-files 20
```

It reports file counts, total size, broad language breakdown, largest files, and
TODO-like comments while ignoring common generated directories.
