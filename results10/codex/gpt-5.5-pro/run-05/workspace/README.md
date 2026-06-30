# Workspace Digest

`workspace_digest.py` creates a compact Markdown inventory for a directory tree.

```bash
python3 workspace_digest.py /path/to/project --output digest.md
```

It reports file counts, total size, file-type totals, largest files, and a capped file list. Common generated directories such as `.git`, `node_modules`, `__pycache__`, and build outputs are skipped by default.

Useful options:

```bash
python3 workspace_digest.py . --top 20 --file-limit 200
python3 workspace_digest.py . --ignore snapshots --ignore fixtures
python3 workspace_digest.py . --no-default-ignores
```
