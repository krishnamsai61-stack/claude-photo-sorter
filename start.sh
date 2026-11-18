#!/bin/bash
# Opens the photo sorter in your browser. Safe to run again: if it's already running it just opens the page.
#   ./start.sh               run here (Ctrl+C to stop)
#   ./start.sh --background  keep running after this window or chat closes (logs in work/server.log)
#   ./start.sh --demo        open the demo camera roll
#   ./start.sh --no-open     don't open a browser tab
cd "$(dirname "$0")" || exit 1
BG=0; DEMO=0; OPEN=1
for a in "$@"; do
  case "$a" in --background) BG=1 ;; --demo) DEMO=1 ;; --no-open) OPEN=0 ;; esac
done

ours() { curl -sf -m 2 "http://127.0.0.1:$1/api/state" 2>/dev/null | grep -q '"categories"'; }
busy() { curl -s -o /dev/null -m 2 "http://127.0.0.1:$1/" 2>/dev/null || lsof -nP -iTCP:"$1" -sTCP:LISTEN >/dev/null 2>&1; }
open_page() {
  [ "$OPEN" = 1 ] || return 0
  if command -v open >/dev/null; then open "$1"; elif command -v xdg-open >/dev/null; then xdg-open "$1" >/dev/null 2>&1; fi
}

PORT="${PORT:-8765}"
# already running (this copy or another): just open it
for p in $(seq "$PORT" $((PORT + 9))); do
  if ours "$p"; then
    URL="http://127.0.0.1:$p/"; [ "$DEMO" = 1 ] && URL="${URL}?demo"
    echo "READY $URL (already running)"; open_page "$URL"; exit 0
  fi
done
# the port is taken by some other app: use the next free one
while busy "$PORT"; do PORT=$((PORT + 1)); done
URL="http://127.0.0.1:$PORT/"; [ "$DEMO" = 1 ] && URL="${URL}?demo"

[ -f .venv/.ok ] || ./setup.sh || exit 1
[ -f dashboard/demo/inventory.json ] || .venv/bin/python scripts/demo.py >/dev/null 2>&1 || true

wait_ready() {
  for _ in $(seq 1 100); do ours "$PORT" && return 0; sleep 0.2; done
  return 1
}

if [ "$BG" = 1 ]; then
  mkdir -p work
  PORT="$PORT" nohup .venv/bin/python scripts/server.py >work/server.log 2>&1 &
  if wait_ready; then echo "READY $URL"; open_page "$URL"; exit 0; fi
  echo "START_FAILED: see work/server.log"; tail -5 work/server.log; exit 1
fi
(wait_ready && open_page "$URL") &
PORT="$PORT" exec .venv/bin/python scripts/server.py
