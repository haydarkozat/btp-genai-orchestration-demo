#!/usr/bin/env bash
# Set up the screenshot capture tool: a local venv with Playwright + Chromium.
set -euo pipefail
cd "$(dirname "$0")"

if command -v uv >/dev/null 2>&1; then
  # uv fetches a compatible interpreter so this works regardless of system Python.
  uv venv --python 3.12 .venv
  uv pip install --python .venv/bin/python -r requirements.txt
  .venv/bin/playwright install chromium
else
  python3 -m venv .venv
  ./.venv/bin/python -m pip install --upgrade pip
  ./.venv/bin/python -m pip install -r requirements.txt
  ./.venv/bin/playwright install chromium
fi

cat <<'EOF'

Setup complete. Usage:
  ./capture login    # headed browser — sign in manually, then press Enter
  ./capture shoot    # capture masked screenshots into docs/screenshots/

Fill in the REPLACE-ME URLs/selectors in targets.yaml first.
EOF
