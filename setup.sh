#!/bin/bash
# One-time setup (safe to run again): finds Python 3.9+, installs 3 small packages into .venv/,
# and draws the demo camera roll. Nothing is installed system-wide.
cd "$(dirname "$0")" || exit 1

say() { printf '%s\n' "$*"; }

# 1. a Python that is new enough
PY=""
for c in python3.13 python3.12 python3.11 python3.10 python3 /opt/homebrew/bin/python3 /usr/local/bin/python3 /usr/bin/python3; do
  p=$(command -v "$c" 2>/dev/null) || continue
  # /usr/bin/python3 is only a stub until Apple's developer tools are installed
  if [ "$p" = "/usr/bin/python3" ] && [ "$(uname)" = "Darwin" ] && ! xcode-select -p >/dev/null 2>&1; then continue; fi
  if "$p" -c 'import sys, venv; sys.exit(sys.version_info < (3, 9))' >/dev/null 2>&1; then PY="$p"; break; fi
done
if [ -z "$PY" ]; then
  if [ "$(uname)" = "Darwin" ]; then
    xcode-select --install >/dev/null 2>&1
    say "PYTHON_MISSING: Python 3.9 or newer is needed."
    say "A window asking to install Apple's command line developer tools should have opened: click Install,"
    say "wait for it to finish (a few minutes), then run setup again. Or install Python from python.org."
  else
    say "PYTHON_MISSING: install Python 3.9 or newer (python.org), then run setup again."
  fi
  exit 1
fi

# 2. the virtual environment (rebuilt if an earlier setup was interrupted)
if [ -d .venv ] && [ ! -f .venv/.ok ]; then rm -rf .venv; fi
if [ ! -x .venv/bin/python ]; then
  say "Setting up with $("$PY" --version 2>&1)..."
  "$PY" -m venv .venv || { say "SETUP_FAILED: couldn't create .venv with $PY"; exit 1; }
fi
.venv/bin/python -m pip install -q --disable-pip-version-check --upgrade pip >/dev/null 2>&1
if ! .venv/bin/python -m pip install -q --disable-pip-version-check --prefer-binary "pillow>=10.0" "imagehash>=4.3"; then
  say "SETUP_FAILED: couldn't download the Python packages. Check the internet connection and run setup again."
  exit 1
fi
# HEIC (iPhone) support is optional: never let it block setup
.venv/bin/python -m pip install -q --disable-pip-version-check --prefer-binary --only-binary=:all: "pillow-heif>=0.16" >/dev/null 2>&1 \
  || say "Note: iPhone HEIC previews aren't available on this computer (photos still get sorted)."

# 3. the demo camera roll (drawn shapes, not real photos)
[ -f dashboard/demo/inventory.json ] || .venv/bin/python scripts/demo.py >/dev/null 2>&1 || true
touch .venv/.ok

if ! command -v ffmpeg >/dev/null; then
  say "Note: ffmpeg isn't installed, so videos get plain previews (they are still sorted)."
  command -v brew >/dev/null && say "      To add video previews: brew install ffmpeg"
fi
say "SETUP_OK"
