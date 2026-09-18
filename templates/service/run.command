#!/usr/bin/env bash
# Wrapper: shortcut/timer calls THIS, never python directly.
cd "$(dirname "$0")" || exit 3
export PATH="$HOME/.local/bin:$PATH"
mkdir -p logs
exec uv run python run.py "$@"
