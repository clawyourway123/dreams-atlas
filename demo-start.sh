#!/usr/bin/env bash
# DreaMS Atlas — one-command local demo launcher (Python path, no Docker required)
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$REPO_ROOT/.venv-demo"
PORT="${PORT:-8000}"

echo "==> DreaMS Atlas demo launcher"
echo ""

# Require Python 3.10+
PYTHON=""
for candidate in python3.12 python3.11 python3.10 python3; do
  if command -v "$candidate" &>/dev/null; then
    version=$("$candidate" -c 'import sys; print(sys.version_info[:2])')
    if "$candidate" -c 'import sys; assert sys.version_info >= (3,10)' 2>/dev/null; then
      PYTHON="$candidate"
      break
    fi
  fi
done

if [ -z "$PYTHON" ]; then
  echo "ERROR: Python 3.10+ is required. Install it from https://python.org and re-run."
  exit 1
fi

echo "==> Using $($PYTHON --version)"

# Create virtual environment if needed
if [ ! -d "$VENV" ]; then
  echo "==> Creating virtual environment..."
  "$PYTHON" -m venv "$VENV"
fi

source "$VENV/bin/activate"

# Install dependencies
echo "==> Installing dependencies (first run may take ~30s)..."
pip install --quiet --upgrade pip
pip install --quiet -r "$REPO_ROOT/backend/requirements.txt"

echo ""
echo "==> Starting DreaMS Atlas..."
echo ""
echo "  ┌─────────────────────────────────────────┐"
echo "  │  Open in browser: http://localhost:$PORT  │"
echo "  │  Press Ctrl+C to stop                   │"
echo "  └─────────────────────────────────────────┘"
echo ""

cd "$REPO_ROOT"
exec python backend/server.py
