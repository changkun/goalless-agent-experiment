#!/usr/bin/env bash
# Convenience wrapper so you can run `./todo.sh` (or alias it).
exec python3 "$(dirname "$0")/todo.py" "$@"
