#!/usr/bin/env bash
# Convenience launcher for Terminal Wordle.
cd "$(dirname "$0")" || exit 1
exec python3 -m wordle "$@"
